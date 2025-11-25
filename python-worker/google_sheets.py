import os
from dotenv import load_dotenv
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import pickle

load_dotenv()

# Google Sheets API scopes
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

column_name = "Query"

# Environment variables
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
GOOGLE_SPREADSHEET_ID = os.getenv("GOOGLE_SPREADSHEET_ID")
GOOGLE_SHEET_NAME = os.getenv("GOOGLE_SHEET_NAME", "Sheet1")  # Default to Sheet1

# Token file path
TOKEN_FILE = os.path.join(os.path.dirname(__file__), 'token.pickle')


def get_credentials():
    """
    Get valid user credentials from storage or OAuth flow.
    Returns credentials object.
    """
    creds = None
    
    # Load existing token if available
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, 'rb') as token:
            creds = pickle.load(token)
    
    # If there are no (valid) credentials available, let the user log in
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # Create OAuth2 flow
            client_config = {
                "installed": {
                    "client_id": GOOGLE_CLIENT_ID,
                    "client_secret": GOOGLE_CLIENT_SECRET,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": ["http://localhost"]
                }
            }
            flow = InstalledAppFlow.from_client_config(client_config, SCOPES)
            creds = flow.run_local_server(port=0)
        
        # Save credentials for next run
        with open(TOKEN_FILE, 'wb') as token:
            pickle.dump(creds, token)
    
    return creds


def get_service():
    """
    Get Google Sheets service object.
    """
    creds = get_credentials()
    return build('sheets', 'v4', credentials=creds)


def ensure_header_exists(service, spreadsheet_id, sheet_name):
    """
    Ensure the header row exists in the sheet.
    """
    try:
        # Get the sheet to check if header exists
        sheet = service.spreadsheets()
        result = sheet.values().get(
            spreadsheetId=spreadsheet_id,
            range=f"{sheet_name}!A1"
        ).execute()
        values = result.get('values', [])
        
        # If no header exists, add it
        if not values or values[0][0] != column_name:
            sheet.values().update(
                spreadsheetId=spreadsheet_id,
                range=f"{sheet_name}!A1",
                valueInputOption='RAW',
                body={'values': [[column_name]]}
            ).execute()
    except HttpError as error:
        # If sheet doesn't exist or is empty, create header
        try:
            service.spreadsheets().values().update(
                spreadsheetId=spreadsheet_id,
                range=f"{sheet_name}!A1",
                valueInputOption='RAW',
                body={'values': [[column_name]]}
            ).execute()
        except Exception as e:
            raise Exception(f"Failed to create header: {e}")


def add_to_sheet(query: str):
    """
    Add a query to the Google Sheet.
    
    Args:
        query: The query string to add to the sheet
    """
    if not GOOGLE_SPREADSHEET_ID:
        raise ValueError("GOOGLE_SPREADSHEET_ID environment variable is not set")
    
    try:
        service = get_service()
        
        # Ensure header exists
        ensure_header_exists(service, GOOGLE_SPREADSHEET_ID, GOOGLE_SHEET_NAME)
        
        # Append the query to the sheet
        sheet = service.spreadsheets()
        values = [[query]]
        body = {'values': values}
        
        result = sheet.values().append(
            spreadsheetId=GOOGLE_SPREADSHEET_ID,
            range=f"{GOOGLE_SHEET_NAME}!A:A",
            valueInputOption='RAW',
            body=body
        ).execute()
        
        return result
    except HttpError as error:
        raise Exception(f"An error occurred while adding to sheet: {error}")


def get_all_queries():
    """
    Get all queries from the Google Sheet.
    
    Returns:
        List of query strings (excluding the header)
    """
    if not GOOGLE_SPREADSHEET_ID:
        raise ValueError("GOOGLE_SPREADSHEET_ID environment variable is not set")
    
    try:
        service = get_service()
        sheet = service.spreadsheets()
        
        # Get all values from column A
        result = sheet.values().get(
            spreadsheetId=GOOGLE_SPREADSHEET_ID,
            range=f"{GOOGLE_SHEET_NAME}!A:A"
        ).execute()
        
        values = result.get('values', [])
        
        # Remove header and return queries
        if not values:
            return []
        
        # Skip the header row (first row)
        queries = [row[0] for row in values[1:] if row and len(row) > 0]
        
        return queries
    except HttpError as error:
        raise Exception(f"An error occurred while reading from sheet: {error}")
