import requests
import base64

class KakaoPayAuth:
    def __init__(self, client_id, client_secret, redirect_uri):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        # 수정된 토큰 URL - 카카오페이 OAuth 서버 주소
        self.token_url = "https://kapi.kakao.com/v1/payment/oauth/token"
        
        # Basic 인증을 위한 인코딩된 credentials 생성
        credentials = f"{self.client_id}:{self.client_secret}"
        self.encoded_credentials = base64.b64encode(credentials.encode()).decode()
    
    def get_access_token(self, authorization_code):
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": f"Basic {self.encoded_credentials}"
        }
        
        data = {
            "grant_type": "authorization_code",
            "code": authorization_code,
            "redirect_uri": self.redirect_uri
        }
        
        try:
            response = requests.post(self.token_url, headers=headers, data=data)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"요청 상세 정보: URL={self.token_url}, Headers={headers}, Data={data}")
            if hasattr(e.response, 'status_code') and hasattr(e.response, 'text'):
                print(f"응답 상세 정보: Status={e.response.status_code}, Content={e.response.text}")
            raise Exception(f"토큰 발급 실패: {str(e)}")
    
    def refresh_access_token(self, refresh_token):
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": f"Basic {self.encoded_credentials}"
        }
        
        data = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token
        }
        
        try:
            response = requests.post(self.token_url, headers=headers, data=data)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"요청 상세 정보: URL={self.token_url}, Headers={headers}, Data={data}")
            if hasattr(e.response, 'status_code') and hasattr(e.response, 'text'):
                print(f"응답 상세 정보: Status={e.response.status_code}, Content={e.response.text}")
            raise Exception(f"토큰 갱신 실패: {str(e)}")

def get_authorization_url(client_id, redirect_uri):
    """
    카카오페이 로그인 인증 URL 생성
    """
    auth_url = "https://kapi.kakao.com/v1/payment/oauth/authorize"
    return f"{auth_url}?client_id={client_id}&redirect_uri={redirect_uri}&response_type=code"

# 사용 예시
if __name__ == "__main__":
    # 애플리케이션 정보 설정
    CLIENT_ID = "34B6CF829203332B92B1"
    CLIENT_SECRET = "C4E0D357F96FE1E856F7"
    SECRET_KEY = "PRD2C934DC0BDE8D03B2CD2FBCDE7CBD42C478ED"
    REDIRECT_URI = "https://butlerian-holtz.streamlit.app/"
    
    # 인증 URL 생성
    auth_url = get_authorization_url(CLIENT_ID, REDIRECT_URI)
    print("인증 URL:", auth_url)
    print("\n이 URL로 접속하여 인가 코드를 받으세요.")
    
    # 사용자로부터 인가 코드 입력받기
    authorization_code = input("\n인가 코드를 입력하세요: ")
    
    # 카카오페이 인증 객체 생성
    kakaopay_auth = KakaoPayAuth(CLIENT_ID, CLIENT_SECRET, REDIRECT_URI)
    
    try:
        # 액세스 토큰 발급
        token_info = kakaopay_auth.get_access_token(authorization_code)
        print("\n액세스 토큰 발급 성공:", token_info)
        
        # 리프레시 토큰으로 액세스 토큰 갱신
        refresh_token = token_info.get("refresh_token")
        if refresh_token:
            new_token_info = kakaopay_auth.refresh_access_token(refresh_token)
            print("\n액세스 토큰 갱신 성공:", new_token_info)
    
    except Exception as e:
        print("\n에러 발생:", str(e))