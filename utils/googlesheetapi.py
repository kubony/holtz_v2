import os
from dotenv import load_dotenv
import googleapiclient.discovery
from google.oauth2 import service_account
from googleapiclient.errors import HttpError
import pandas as pd
import logging
from googleapiclient.discovery import build
from googleapiclient.discovery_cache.base import Cache
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

class MemoryCache(Cache):
    _CACHE = {}

    def get(self, url):
        return MemoryCache._CACHE.get(url)

    def set(self, url, content):
        MemoryCache._CACHE[url] = content

class GoogleAPIManager:
    def __init__(self):
        try:
            # 환경 변수 로드
            load_dotenv()
            
            # 서비스 계정 정보 설정
            self.credentials_info = {
                "type": os.getenv("type"),
                "project_id": os.getenv("project_id"),
                "private_key_id": os.getenv("private_key_id"),
                "private_key": os.getenv("private_key").replace('\\n', '\n'),
                "client_email": os.getenv("client_email"),
                "client_id": os.getenv("client_id"),
                "auth_uri": os.getenv("auth_uri"),
                "token_uri": os.getenv("token_uri"),
                "auth_provider_x509_cert_url": os.getenv("auth_provider_x509_cert_url"),
                "client_x509_cert_url": os.getenv("client_x509_cert_url")
            }

            # 스프레드시트 ID와 스코프 설정
            self.SPREADSHEET_ID = os.getenv("GOOGLE_SHEETS_SPREADSHEET_ID")
            self.SCOPES = os.getenv("GOOGLE_SHEETS_SCOPES").split()

            # Credentials 객체 생성
            self.credentials = service_account.Credentials.from_service_account_info(
                self.credentials_info, scopes=self.SCOPES)

            # 서비스 객체 초기화 (메모리 캐시 사용)
            self.sheet_service = build('sheets', 'v4', 
                                     credentials=self.credentials,
                                     cache=MemoryCache())
            self.drive_service = build('drive', 'v3', 
                                     credentials=self.credentials,
                                     cache=MemoryCache())
            self.forms_service = build('forms', 'v1', 
                                     credentials=self.credentials,
                                     cache=MemoryCache())
            
        except Exception as err:
            logger.error(f"GoogleAPIManager initialization error: {err}")
            self.sheet_service = None
            self.drive_service = None
            self.forms_service = None

    def create_spreadsheet(self, title: str) -> Optional[str]:
        """
        새로운 스프레드시트를 생성합니다.
        """
        try:
            spreadsheet = {
                'properties': {
                    'title': title
                }
            }
            spreadsheet = self.sheet_service.spreadsheets().create(
                body=spreadsheet,
                fields='spreadsheetId'
            ).execute()
            return spreadsheet.get('spreadsheetId')
        except HttpError as error:
            logging.error(f"Failed to create spreadsheet: {error}")
            return None

    def get_spreadsheet_metadata(self, spreadsheet_id: str) -> Optional[Dict]:
        """
        스프레드시트의 메타데이터를 가져옵니다.
        """
        try:
            return self.sheet_service.spreadsheets().get(
                spreadsheetId=spreadsheet_id
            ).execute()
        except HttpError as error:
            logging.error(f"Failed to get spreadsheet metadata: {error}")
            return None

    def read_sheet_data(self, spreadsheet_id: str, range_name: str) -> List[List]:
        """
        지정된 스프레드시트의 범위에서 데이터를 읽어옵니다.
        range_name 형식: 'Sheet1' 또는 'Sheet1!A1:D10' 또는 'A1:D10'
        """
        try:
            # 시트 메타데이터 확인
            metadata = self.get_spreadsheet_metadata(spreadsheet_id)
            if not metadata:
                logging.error("Failed to get spreadsheet metadata")
                return []

            # range_name이 시트 이름만 포함하는 경우 전체 범위를 읽음
            if '!' not in range_name:
                range_name = f"'{range_name}'"

            result = self.sheet_service.spreadsheets().values().get(
                spreadsheetId=spreadsheet_id,
                range=range_name
            ).execute()
            return result.get('values', [])
        except HttpError as error:
            logging.error(f"Failed to read sheet data: {error}")
            return []

    def write_sheet_data(self, spreadsheet_id: str, range_name: str, values: List[List]) -> bool:
        """
        지정된 스프레드시트의 범위에 데이터를 씁니다.
        """
        try:
            body = {'values': values}
            self.sheet_service.spreadsheets().values().update(
                spreadsheetId=spreadsheet_id,
                range=range_name,
                valueInputOption='RAW',
                body=body
            ).execute()
            return True
        except HttpError as error:
            logging.error(f"Failed to write sheet data: {error}")
            return False

    def append_sheet_data(self, spreadsheet_id: str, range_name: str, values: List[List]) -> bool:
        """
        지정된 스프레드시트의 마지막 행에 데이터를 추가합니다.
        """
        try:
            body = {'values': values}
            self.sheet_service.spreadsheets().values().append(
                spreadsheetId=spreadsheet_id,
                range=range_name,
                valueInputOption='RAW',
                insertDataOption='INSERT_ROWS',
                body=body
            ).execute()
            return True
        except HttpError as error:
            logging.error(f"Failed to append sheet data: {error}")
            return False

    def batch_update_sheet(self, spreadsheet_id: str, requests: List[Dict]) -> bool:
        """
        여러 업데이트를 한 번에 실행합니다.
        """
        try:
            body = {'requests': requests}
            self.sheet_service.spreadsheets().batchUpdate(
                spreadsheetId=spreadsheet_id,
                body=body
            ).execute()
            return True
        except HttpError as error:
            logging.error(f"Failed to batch update sheet: {error}")
            return False

    def clear_sheet_range(self, spreadsheet_id: str, range_name: str) -> bool:
        """
        지정된 스프레드시트의 범위의 데이터를 지웁니다.
        """
        try:
            self.sheet_service.spreadsheets().values().clear(
                spreadsheetId=spreadsheet_id,
                range=range_name
            ).execute()
            return True
        except HttpError as error:
            logging.error(f"Failed to clear sheet range: {error}")
            return False

    def get_sheet_as_dataframe(self, spreadsheet_id: str, range_name: str) -> pd.DataFrame:
        """
        스프레드시트 데이터를 pandas DataFrame으로 변환합니다.
        """
        try:
            data = self.read_sheet_data(spreadsheet_id, range_name)
            if not data:
                return pd.DataFrame()
            
            headers = data[0]
            values = data[1:]
            return pd.DataFrame(values, columns=headers)
        except Exception as error:
            logging.error(f"Failed to convert sheet to DataFrame: {error}")
            return pd.DataFrame()
    def dataframe_to_sheet(self, spreadsheet_id: str, range_name: str, df: pd.DataFrame) -> bool:
        """
        DataFrame을 스프레드시트에 씁니다.
        """
        try:
            values = [df.columns.values.tolist()] + df.values.tolist()
            return self.write_sheet_data(spreadsheet_id, range_name, values)
        except Exception as error:
            logging.error(f"Failed to write DataFrame to sheet: {error}")
            return False

    def create_sheet(self, spreadsheet_id: str, title: str) -> Optional[int]:
        """
        스프레드시트에 새 시트를 추가합니다.
        """
        try:
            request = {
                'addSheet': {
                    'properties': {
                        'title': title
                    }
                }
            }
            response = self.batch_update_sheet(spreadsheet_id, [request])
            if response:
                return response['replies'][0]['addSheet']['properties']['sheetId']
            return None
        except Exception as error:
            logging.error(f"Failed to create new sheet: {error}")
            return None

    def delete_sheet(self, spreadsheet_id: str, sheet_id: int) -> bool:
        """
        스프레드시트에서 시트를 삭제합니다.
        """
        try:
            request = {
                'deleteSheet': {
                    'sheetId': sheet_id
                }
            }
            return self.batch_update_sheet(spreadsheet_id, [request])
        except Exception as error:
            logging.error(f"Failed to delete sheet: {error}")
            return False

def main():
    # 로깅 설정
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    logging.getLogger('googleapiclient.discovery_cache').setLevel(logging.ERROR)
    
    # GoogleAPIManager 인스턴스 생성
    manager = GoogleAPIManager()
    
    # 테스트용 스프레드시트 ID
    SPREADSHEET_ID = "1eJ266ItXio_9haQ2G5wPULYQS5H7dXHgpOZ3cbVaw7s"
    
    try:
        # 스프레드시트 메타데이터 확인
        metadata = manager.get_spreadsheet_metadata(SPREADSHEET_ID)
        if metadata:
            sheets = metadata.get('sheets', [])
            if sheets:
                first_sheet_title = sheets[0]['properties']['title']
                logging.info(f"First sheet title: {first_sheet_title}")
                
                # A열과 B열 데이터 읽기
                range_name = f"'{first_sheet_title}'!A:B"  # A열부터 B열까지 전체 데이터
                
                data = manager.read_sheet_data(SPREADSHEET_ID, range_name)
                logging.info(f"Read {len(data)} rows of data")
                
                # 데이터 내용 출력
                if data:
                    logging.info("Data preview:")
                    for row in data[:5]:  # 처음 5행만 출력
                        logging.info(row)
                
                # DataFrame으로 변환
                df = manager.get_sheet_as_dataframe(SPREADSHEET_ID, range_name)
                logging.info(f"Converted to DataFrame with shape: {df.shape}")
                if not df.empty:
                    logging.info("\nDataFrame preview:")
                    logging.info(df.head())
            else:
                logging.error("No sheets found in the spreadsheet")
        else:
            logging.error("Failed to get spreadsheet metadata")
            
    except Exception as e:
        logging.error(f"Test failed: {str(e)}")

if __name__ == "__main__":
    main()

