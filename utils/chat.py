import streamlit as st
from datetime import datetime
import pytz
import os
from loguru import logger

def enable_chat_history(func):
    def wrapper(*args, **kwargs):
        if "messages" not in st.session_state:
            st.session_state["messages"] = [{
                "role": "assistant", 
                "content": "안녕하세요! 그집밥 주문 받습니다!"
            }]
        
        for msg in st.session_state["messages"]:
            st.chat_message(msg["role"]).write(msg["content"])
            
        return func(*args, **kwargs)
    return wrapper

def display_msg(msg, author):
    st.session_state.messages.append({"role": author, "content": msg})
    st.chat_message(author).write(msg)

def get_chat_history():
    if "messages" not in st.session_state:
        return ""
    
    chat_history = []
    for message in st.session_state.messages:
        role = "사용자" if message["role"] == "user" else "챗봇"
        chat_history.append(f"{role}: {message['content']}")
    
    return "\n".join(chat_history)

def get_current_time_info():
    weekday_names = {
        0: '월요일', 1: '화요일', 2: '수요일', 
        3: '목요일', 4: '금요일', 5: '토요일', 6: '일요일'
    }
    
    kst = pytz.timezone('Asia/Seoul')
    now = datetime.now(kst)
    
    return {
        "time": now.strftime("%H:%M"),
        "date": now.strftime("%Y년 %m월 %d일"),
        "weekday": weekday_names[now.weekday()]
    }

def load_common_instructions():
    try:
        with open("store_infos/공통지시사항.md", 'r', encoding='utf-8') as file:
            return file.read()
    except Exception as e:
        logger.error(f"공통 지시사항 로드 중 오류 발생: {str(e)}")
        return "공통 지시사항을 불러오는데 실패했습니다."

def load_project_context(store_name):
    try:
        with open(f"store_infos/{store_name}.md", 'r', encoding='utf-8') as file:
            return file.read()
    except Exception as e:
        logger.error(f"프로젝트 컨텍스트 로드 중 오류 발생: {str(e)}")
        return "컨텍스트를 불러오는데 실패했습니다."
