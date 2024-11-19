import streamlit as st
from datetime import datetime
import openai
from loguru import logger
from config.settings import settings
from langchain_openai import ChatOpenAI
from langchain_community.chat_models import ChatOllama
from anthropic import Anthropic

def get_openai_model_list(api_key):
    try:
        client = openai.OpenAI(api_key=api_key)
        models = client.models.list()
        gpt_models = [{"id": m.id, "created": datetime.fromtimestamp(m.created)} 
                     for m in models if m.id.startswith("gpt")]
        return sorted(gpt_models, key=lambda x: x["created"], reverse=True)
    except Exception as e:
        logger.error(f"OpenAI 모델 목록 조회 중 오류 발생: {str(e)}")
        st.error("모델 목록을 가져오는 중 오류가 발생했습니다.")
        st.stop()

def configure_llm():
    available_llms = [settings.DEFAULT_MODEL, "llama3:8b", "OpenAI API 키 사용"]
    llm_opt = st.sidebar.radio("LLM 선택", options=available_llms, key="SELECTED_LLM")

    if llm_opt == "llama3:8b":
        return ChatOllama(model="llama3", base_url=settings.OLLAMA_ENDPOINT)
    elif llm_opt == settings.DEFAULT_MODEL:
        return ChatOpenAI(
            model_name=llm_opt, 
            temperature=0, 
            streaming=True, 
            api_key=settings.OPENAI_API_KEY.get_secret_value()
        )
    else:
        return handle_custom_openai_key()

def handle_custom_openai_key():
    api_key = st.sidebar.text_input(
        "OpenAI API 키", 
        type="password", 
        placeholder="sk-...", 
        key="CUSTOM_OPENAI_API_KEY"
    )
    
    if not api_key:
        st.error("계속하려면 OpenAI API 키를 입력해주세요.")
        st.info("API 키는 다음 링크에서 얻을 수 있습니다: https://platform.openai.com/account/api-keys")
        st.stop()

    models = get_openai_model_list(api_key)
    model = st.sidebar.selectbox(
        "모델 선택", 
        options=[m["id"] for m in models], 
        key="SELECTED_OPENAI_MODEL"
    )
    
    return ChatOpenAI(model_name=model, temperature=0, streaming=True, api_key=api_key)
