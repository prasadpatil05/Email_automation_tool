from google.oauth2 import service_account
from googleapiclient.discovery import build

def connect_google_sheets(credentials_file):
    credentials = service_account.Credentials.from_service_account_info(credentials_file.file.read())
    service = build('sheets', 'v4', credentials=credentials)
    sheet = service.spreadsheets()
    result = sheet.values().get(spreadsheetId='your_spreadsheet_id', range='Sheet1').execute()
    return result.get('values', [])