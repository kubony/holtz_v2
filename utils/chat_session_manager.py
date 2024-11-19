from datetime import datetime
from typing import Optional, Dict
from loguru import logger
from supabase import Client, create_client
from pydantic import BaseModel

class ChatMessage(BaseModel):
    role: str
    question: Dict
    answer: Dict

class ChatSessionManager:
    def __init__(self, supabase_url: str, supabase_key: str):
        if not supabase_url or not supabase_key:
            raise ValueError("Supabase URL과 Key는 필수값입니다.")
        self.supabase: Client = create_client(supabase_url, supabase_key)
        logger.info("ChatSessionManager 초기화됨")

    def create_session(self, store_name: str) -> str:
        if not store_name:
            raise ValueError("store_name은 필수값입니다.")
        try:
            current_time = datetime.utcnow().isoformat()
            result = self.supabase.table('chat_sessions').insert({
                'store_name': store_name,
                'created_at': current_time,
                'updated_at': current_time
            }).execute()
            session_id = result.data[0]['id']
            logger.info(f"새 채팅 세션 생성됨: {{'session_id': '{session_id}', 'store_name': '{store_name}'}}")
            return session_id
        except Exception as e:
            logger.error(f"채팅 세션 생성 실패: {str(e)}")
            raise

    def save_message(self, session_id: str, role: str, question: Dict, answer: Dict) -> None:
        if not session_id or not role:
            raise ValueError("session_id와 role은 필수값입니다.")
        if not isinstance(question, dict) or not isinstance(answer, dict):
            raise TypeError("question과 answer는 딕셔너리 형태여야 합니다.")
        try:
            self.supabase.table('chat_messages').insert({
                'session_id': session_id,
                'role': role,
                'question': question,
                'answer': answer
            }).execute()
            logger.info(f"메시지 저장됨: {{'session_id': '{session_id}', 'role': '{role}'}}")
        except Exception as e:
            logger.error(f"메시지 저장 실패: {str(e)}")
            raise

    def get_session_messages(self, session_id: str):
        if not session_id:
            raise ValueError("session_id는 필수값입니다.")
        try:
            result = self.supabase.table('chat_messages')\
                .select('*')\
                .eq('session_id', session_id)\
                .order('created_at')\
                .execute()
            return result.data
        except Exception as e:
            logger.error(f"세션 메시지 조회 실패: {str(e)}")
            raise

    def update_session_timestamp(self, session_id: str) -> None:
        try:
            current_time = datetime.utcnow().isoformat()
            self.supabase.table('chat_sessions').update({
                'updated_at': current_time
            }).eq('id', session_id).execute()
            logger.debug(f"세션 타임스탬프 갱신됨: {session_id}")
        except Exception as e:
            logger.error(f"세션 타임스탬프 갱신 실패: {str(e)}")
            raise