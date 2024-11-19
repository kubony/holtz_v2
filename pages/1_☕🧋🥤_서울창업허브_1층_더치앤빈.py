import os
import utils.chatbotutils as chatbotutils
import streamlit as st
from streaming import StreamHandler
from langchain.chains import ConversationChain
from langchain.memory import ConversationBufferMemory
from loguru import logger
from config.settings import settings

st.set_page_config(page_title="더치앤빈 서울창업허브점 챗봇", page_icon="📚")
st.header('더치앤빈 서울창업허브점 챗봇')
st.write('메뉴 정보를 기반으로 대화하는 챗봇입니다.')

class ProjectContextChatbot:
    def __init__(self):
        chatbotutils.sync_st_session()
        self.llm = chatbotutils.configure_llm()
        self.context = chatbotutils.load_project_context("더치앤빈 서울창업허브점")
    
    @st.cache_resource
    def setup_chain(_self, max_tokens=1000):
        memory = ConversationBufferMemory(max_token_limit=max_tokens)
        chain = ConversationChain(
            llm=_self.llm, 
            memory=memory,
            verbose=True
        )
        return chain
    
    @chatbotutils.enable_chat_history
    def main(self):
        max_tokens = st.sidebar.slider("메모리 크기 (토큰)", 100, 2000, 1000)
        chain = self.setup_chain(max_tokens)
        common_instructions = chatbotutils.load_common_instructions()

        with st.expander("프로젝트 컨텍스트 정보", expanded=False):
            st.text(self.context)

        user_query = st.chat_input(placeholder="더치앤빈 서울창업허브점입니다! 주문하시겠어요?")
        
        if user_query:
            chatbotutils.display_msg(user_query, 'user')
            with st.chat_message("assistant"):
                st_cb = StreamHandler(st.empty())
                try:
                    time_info = chatbotutils.get_current_time_info()
                    full_query = f"""공통 지시사항:
{common_instructions}

현재 시간 정보:
- 날짜: {time_info['date']}
- 요일: {time_info['weekday']}
- 시간: {time_info['time']}

프로젝트 컨텍스트:
{self.context}

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
    st.sidebar.title("설정")
    model = st.sidebar.selectbox("LLM 모델 선택", [settings.DEFAULT_MODEL, "다른모델1", "다른모델2"])
    temperature = st.sidebar.slider("Temperature", 0.0, 1.0, 0.7)
    
    obj = ProjectContextChatbot()
    obj.main()