import streamlit as st
from loguru import logger
from utils import chat, llm, logger_setup, session
from streaming import StreamHandler
from langchain.chains import ConversationChain
from langchain.memory import ConversationBufferMemory
from utils.googlesheetapi import GoogleAPIManager
from utils.chat_session_manager import ChatSessionManager
import os
from dotenv import load_dotenv

logger_setup.setup_logging()
load_dotenv()

# Supabase 설정
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')

st.set_page_config(
    page_title="Butlerian Holtz",
    page_icon='💬',
    layout='wide',
    initial_sidebar_state="collapsed"
)

logger.info("메인 페이지 로드됨")

st.header("Holtz : 키오스크 줄서지마")

# 이미지를 위한 컨테이너 생성
image_container = st.container()

# 컬럼을 사용하여 이미지 크기 조절
with image_container:
    col1, col2, col3 = st.columns([1,3,1])  # 1:3:1 비율로 분할
    with col2:  # 중앙 컬럼에 이미지 배치
        st.image(
            "assets/그집밥_오늘의메뉴_202411xx.png",
            caption="그집밥 오늘 메뉴",
            width=400  # 이미지 너비 지정
        )
class MainChatbot:
    def __init__(self):
        session.sync_st_session()
        self.llm = llm.configure_llm()
        self.sheet_manager = GoogleAPIManager()
        self.SPREADSHEET_ID = "1eJ266ItXio_9haQ2G5wPULYQS5H7dXHgpOZ3cbVaw7s"
        self.chat_session_manager = ChatSessionManager(SUPABASE_URL, SUPABASE_KEY)
        self.store_name = "서울창업허브 3층 그집밥"
        
        # 세션 ID가 없으면 새로 생성
        if 'session_id' not in st.session_state:
            st.session_state.session_id = self.chat_session_manager.create_session(self.store_name)
            logger.info(f"새 채팅 세션 생성됨: {st.session_state.session_id}")
    
    def get_waiting_info(self) -> str:
        """구글 시트에서 대기 인원수 정보를 가져옵니다."""
        try:
            metadata = self.sheet_manager.get_spreadsheet_metadata(self.SPREADSHEET_ID)
            if metadata and metadata.get('sheets'):
                sheet_title = metadata['sheets'][0]['properties']['title']
                range_name = f"{sheet_title}!A:B"
                
                data = self.sheet_manager.read_sheet_data(self.SPREADSHEET_ID, range_name)
                if data:
                    waiting_info = "\n현재 대기 현황:\n"
                    for row in data:
                        if len(row) >= 2:  # A열과 B열 모두 데이터가 있는 경우
                            waiting_info += f"- {row[0]}: {row[1]}명\n"
                    return waiting_info
            return "\n현재 대기 인원 정보를 확인할 수 없습니다."
        except Exception as e:
            logger.error(f"대기 인원 정보 조회 중 오류 발생: {str(e)}")
            return "\n현재 대기 인원 정보를 확인할 수 없습니다."
    
    @st.cache_resource
    def setup_chain(_self, max_tokens=1000):
        memory = ConversationBufferMemory(max_token_limit=max_tokens)
        chain = ConversationChain(
            llm=_self.llm, 
            memory=memory,
            verbose=True
        )
        return chain
    
    @chat.enable_chat_history
    def main(self):
        chain = self.setup_chain(1000)
        user_query = st.chat_input(placeholder="안녕하세요! 주문할 식권 수를 입력해주세요!")

        if user_query:
            chat.display_msg(user_query, 'user')
            with st.chat_message("assistant"):
                st_cb = StreamHandler(st.empty())
                try:
                    common_instructions = chat.load_common_instructions()
                    project_instructions = chat.load_project_context(self.store_name)
                    time_info = chat.get_current_time_info()
                    waiting_info = self.get_waiting_info()
                    
                    full_query = f"""
공통 지시사항:
{common_instructions}

프로젝트 지시사항:
{project_instructions}

현재 시간 정보:
- 날짜: {time_info['date']}
- 요일: {time_info['weekday']}
- 시간 (한국): {time_info['time']}

대기 현황 정보:
{waiting_info}

이전 대화 내용:
{chat.get_chat_history()}

사용자 질문: {user_query}"""
                    
                    result = chain.invoke(
                        {"input": full_query},
                        {"callbacks": [st_cb]}
                    )
                    response = result["response"]
                    
                    # Supabase에 대화 내용 저장
                    self.chat_session_manager.save_message(
                        session_id=st.session_state.session_id,
                        role="user",
                        question={"text": user_query, "full_query": full_query},
                        answer={"text": response}
                    )
                    
                    st.session_state.messages.append({"role": "assistant", "content": response})
                    logger.info(f"사용자 질문: {user_query}")
                    logger.info(f"챗봇 응답: {response}")
                    
                    # 세션 타임스탬프 업데이트
                    self.chat_session_manager.update_session_timestamp(st.session_state.session_id)
                    
                except Exception as e:
                    error_msg = f"응답 생성 중 오류 발생: {str(e)}"
                    st.error(error_msg)
                    logger.error(error_msg)

if __name__ == "__main__":
    obj = MainChatbot()
    obj.main()

logger.info("메인 페이지 렌더링 완료")

# streamlit run main.py