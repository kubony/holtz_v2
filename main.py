import streamlit as st
from loguru import logger
import utils.utils as utils
import chatbot as chatbot
from streaming import StreamHandler
from langchain.chains import ConversationChain
from langchain.memory import ConversationBufferMemory
from config.settings import settings

st.set_page_config(
    page_title="Butlerian Holtz",
    page_icon='💬',
    layout='wide',
    initial_sidebar_state="collapsed"
)

logger.info("메인 페이지 로드됨")

st.header("키오스크 줄서지마 서비스 - Holtz")

class MainChatbot:
    def __init__(self):
        utils.sync_st_session()
        self.llm = utils.configure_llm()
    
    @st.cache_resource
    def setup_chain(_self, max_tokens=1000):
        memory = ConversationBufferMemory(max_token_limit=max_tokens)
        chain = ConversationChain(
            llm=_self.llm, 
            memory=memory,
            verbose=True
        )
        return chain
    
    @chatbot.enable_chat_history
    def main(self):
        chain = self.setup_chain(1000)  # 기본값으로 1000 설정
        user_query = st.chat_input(placeholder="안녕하세요! 주문하실 매장을 선택해주세요!")
        store_name = "서울창업허브 3층 그집밥"

        if user_query:
            utils.display_msg(user_query, 'user')
            with st.chat_message("assistant"):
                st_cb = StreamHandler(st.empty())
                try:
                    common_instructions = chatbot.load_common_instructions()
                    project_instructions = chatbot.load_project_context(store_name)
                    time_info = chatbot.get_current_time_info()
                    
                    full_query = f"""
공통 지시사항:
{common_instructions}

프로젝트 지시사항:
{project_instructions}

현재 시간 정보:
- 날짜: {time_info['date']}
- 요일: {time_info['weekday']}
- 시간 (한국): {time_info['time']}

이전 대화 내용:
{chatbot.get_chat_history()}

사용자 질문: {user_query}"""
                    
                    result = chain.invoke(
                        {"input": full_query},
                        {"callbacks": [st_cb]}
                    )
                    response = result["response"]
                    st.session_state.messages.append({"role": "assistant", "content": response})
                    logger.info(f"사용자 질문: {user_query}")
                    logger.info(f"챗봇 응답: {response}")
                except Exception as e:
                    error_msg = f"응답 생성 중 오류 발생: {str(e)}"
                    st.error(error_msg)
                    logger.error(error_msg)

if __name__ == "__main__":
    obj = MainChatbot()
    obj.main()

logger.info("메인 페이지 렌더링 완료")

# streamlit run main.py