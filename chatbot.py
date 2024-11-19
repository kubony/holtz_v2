# utils.py
import os
import openai
import streamlit as st
from datetime import datetime
from loguru import logger
from config.settings import settings
from langchain_openai import ChatOpenAI
from langchain_community.chat_models import ChatOllama
import anthropic
from anthropic import Anthropic
import pytz

def setup_logging():
    logger.add("logs/app.log", rotation="500 MB", level="INFO")
    if settings.OPENAI_API_KEY:
        logger.info(f"OPENAI_API_KEY loaded: {settings.OPENAI_API_KEY.get_secret_value()[:5]}...{settings.OPENAI_API_KEY.get_secret_value()[-5:]}")
    else:
        logger.error("OPENAI_API_KEY is not set in the environment variables.")

setup_logging()

def enable_chat_history(func):
    if settings.OPENAI_API_KEY:
        current_page = func.__qualname__
        if "current_page" not in st.session_state:
            st.session_state["current_page"] = current_page
        if st.session_state["current_page"] != current_page:
            try:
                st.cache_resource.clear()
                del st.session_state["current_page"]
                del st.session_state["messages"]
            except KeyError:
                pass

        if "messages" not in st.session_state:
            st.session_state["messages"] = [{"role": "assistant", "content": "안녕하세요. 그집밥 주문 챗봇이에요. 몇장 드릴까요?"}]
        for msg in st.session_state["messages"]:
            st.chat_message(msg["role"]).write(msg["content"])

    def execute(*args, **kwargs):
        func(*args, **kwargs)
    return execute

def display_msg(msg, author):
    st.session_state.messages.append({"role": author, "content": msg})
    st.chat_message(author).write(msg)

def get_openai_model_list(api_key):
    try:
        client = openai.OpenAI(api_key=api_key)
        models = client.models.list()
        gpt_models = [{"id": m.id, "created": datetime.fromtimestamp(m.created)} for m in models if m.id.startswith("gpt")]
        return sorted(gpt_models, key=lambda x: x["created"], reverse=True)
    except openai.AuthenticationError as e:
        logger.error(f"OpenAI 인증 오류: {str(e)}")
        st.error("OpenAI API 키가 유효하지 않습니다.")
        st.stop()
    except Exception as e:
        logger.error(f"OpenAI 모델 목록 조회 중 오류 발생: {str(e)}")
        st.error("모델 목록을 가져오는 중 오류가 발생했습니다. 나중에 다시 시도해주세요.")
        st.stop()

def configure_llm():
    available_llms = [settings.DEFAULT_MODEL, "llama3:8b", "OpenAI API 키 사용"]
    llm_opt = st.sidebar.radio("LLM 선택", options=available_llms, key="SELECTED_LLM")

    if llm_opt == "llama3:8b":
        return ChatOllama(model="llama3", base_url=settings.OLLAMA_ENDPOINT)
    elif llm_opt == settings.DEFAULT_MODEL:
        return ChatOpenAI(model_name=llm_opt, temperature=0, streaming=True, api_key=settings.OPENAI_API_KEY.get_secret_value())
    else:
        openai_api_key = st.sidebar.text_input("OpenAI API 키", type="password", placeholder="sk-...", key="CUSTOM_OPENAI_API_KEY")
        if not openai_api_key:
            st.error("계속하려면 OpenAI API 키를 입력해주세요.")
            st.info("API 키는 다음 링크에서 얻을 수 있습니다: https://platform.openai.com/account/api-keys")
            st.stop()

        available_models = get_openai_model_list(openai_api_key)
        model = st.sidebar.selectbox("모델 선택", options=[m["id"] for m in available_models], key="SELECTED_OPENAI_MODEL")
        return ChatOpenAI(model_name=model, temperature=0, streaming=True, api_key=openai_api_key)

def sync_st_session():
    for k, v in st.session_state.items():
        st.session_state[k] = v

def configure_llm_with_model(model_name):
    if model_name.startswith('claude-'):
        client = Anthropic(api_key=settings.ANTHROPIC_API_KEY.get_secret_value())
        return client
    elif model_name.startswith('gpt-'):
        return ChatOpenAI(model_name=model_name, temperature=0, streaming=True, api_key=settings.OPENAI_API_KEY.get_secret_value())
    else:
        return ChatOllama(model=model_name, base_url=settings.OLLAMA_ENDPOINT)
    
def truncate_string(s, max_length=100):
    return s if len(s) <= max_length else s[:max_length] + '...'

def setup_logging():
    logger.add("logs/app.log", rotation="500 MB", level="INFO")
    logger.add(lambda msg: print(truncate_string(msg)), level="INFO")
    if settings.OPENAI_API_KEY:
        logger.info(f"OPENAI_API_KEY loaded: {settings.OPENAI_API_KEY.get_secret_value()[:5]}...{settings.OPENAI_API_KEY.get_secret_value()[-5:]}")
    else:
        logger.error("OPENAI_API_KEY is not set in the environment variables.")

def get_current_time_info():

    weekday_names = {
        0: '월요일', 1: '화요일', 2: '수요일', 
        3: '목요일', 4: '금요일', 5: '토요일', 6: '일요일'
    }
    
    # 한국 시간대 설정
    kst = pytz.timezone('Asia/Seoul')
    now = datetime.now(kst)
    
    current_time = now.strftime("%H:%M")
    current_date = now.strftime("%Y년 %m월 %d일")
    weekday = weekday_names[now.weekday()]
    
    return {
        "time": current_time,
        "date": current_date,
        "weekday": weekday
    }

def load_common_instructions():
    try:
        file_path = os.path.join("store_infos", "공통지시사항.md")
        with open(file_path, 'r', encoding='utf-8') as file:
            instructions = file.read()
        return instructions
    except Exception as e:
        logger.error(f"공통 지시사항 로드 중 오류 발생: {str(e)}")
        return "공통 지시사항을 불러오는데 실패했습니다."

def load_project_context(store_name):
    try:
        file_path = os.path.join("store_infos", f"{store_name}.md")
        with open(file_path, 'r', encoding='utf-8') as file:
            context = file.read()
        return context
    except Exception as e:
        logger.error(f"프로젝트 컨텍스트 로드 중 오류 발생: {str(e)}")
        return "컨텍스트를 불러오는데 실패했습니다."

def get_chat_history():
    """
    세션에 저장된 대화 기록을 문자열로 반환합니다.
    """
    if "messages" not in st.session_state:
        return ""
    
    chat_history = []
    for message in st.session_state.messages:
        role = "사용자" if message["role"] == "user" else "챗봇"
        chat_history.append(f"{role}: {message['content']}")
    
    return "\n".join(chat_history)