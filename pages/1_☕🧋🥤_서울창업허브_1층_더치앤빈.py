import os
import utils
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
        utils.sync_st_session()
        self.llm = utils.configure_llm()
        self.context = self.load_project_context()
    
    def load_project_context(self):
        try:
            file_path = os.path.join("store_infos", "더치앤빈 서울창업허브점.md")
            with open(file_path, 'r', encoding='utf-8') as file:
                context = file.read()
            return context
        except Exception as e:
            logger.error(f"프로젝트 컨텍스트 로드 중 오류 발생: {str(e)}")
            return "컨텍스트를 불러오는데 실패했습니다."

    @st.cache_resource
    def setup_chain(_self, max_tokens=1000):
        memory = ConversationBufferMemory(max_token_limit=max_tokens)
        chain = ConversationChain(
            llm=_self.llm, 
            memory=memory,
            verbose=True
        )
        return chain
    
    @utils.enable_chat_history
    def main(self):
        max_tokens = st.sidebar.slider("메모리 크기 (토큰)", 100, 2000, 1000)
        chain = self.setup_chain(max_tokens)

        with st.expander("프로젝트 컨텍스트 정보", expanded=False):
            st.text(self.context)

        user_query = st.chat_input(placeholder="더치앤빈 서울창업허브점입니다! 주문하시겠어요?")
        
        if user_query:
            utils.display_msg(user_query, 'user')
            with st.chat_message("assistant"):
                st_cb = StreamHandler(st.empty())
                try:
                    # 프로젝트 컨텍스트를 포함한 쿼리 생성
                    full_query = f"""프로젝트 컨텍스트:
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