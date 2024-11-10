import os
import pickle
import pandas as pd
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import streamlit as st

SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

def get_spreadsheet_id(url):
        url_parts = url.split("/")
        return url_parts[5]

    # Authenticate with Google Sheets
def authenticate():
        creds = None
        if os.path.exists('token.pickle'):
            with open('token.pickle', 'rb') as token:
                creds = pickle.load(token)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
                creds = flow.run_local_server(port=0)
            with open('token.pickle', 'wb') as token:
                pickle.dump(creds, token)
        return creds


    # Display sheet records preview
def display_sheet_records(service, spreadsheet_id):
        sheet = service.spreadsheets()
        result = sheet.values().get(
            spreadsheetId=spreadsheet_id,
            range="A:Z"
        ).execute()
        values = result.get('values', [])
        # Initialize max columns
        max_cols = 0
        # Find max columns
        for row in values:
            max_cols = max(max_cols, len(row))
        
        # Pad rows with empty strings
        for i, row in enumerate(values):
            values[i] += [''] * (max_cols - len(row))
        
        # Replace empty strings with None
        values = [[cell if cell != '' else None for cell in row] for row in values]
        # Check if values are available
        if values:
            # Set headers as the first row and data as the remaining rows
            headers = values[0]
            data = [[cell if cell else None for cell in row] for row in values[1:]]
            # Replace empty strings with None
            data = [[None if cell == '' else cell for cell in row] for row in data]
            df = pd.DataFrame(data, columns=headers)
        else:
            df = pd.DataFrame()
        return df

def clear_and_write_data_to_sheet(service, spreadsheet_id, range_name, df):
        clear_body = {
                'range': f"{range_name[0]}2:{range_name[-1]}{df.shape[0]+1}"  # Start from row 2
            }
        service.spreadsheets().values().clear(
            spreadsheetId=spreadsheet_id,
            body=clear_body,
            range=range_name
        ).execute()

        # Write entire DataFrame (including headers and index)
        write_body = {
            'values': [[df.index.name] + df.columns.values.tolist()] +  # Header row with index name
                    [[i] + row for i, row in zip(df.index, df.values.tolist())]  # Data rows with index
        }
        service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range=range_name,
            valueInputOption='USER_ENTERED',
            body=write_body
        ).execute()
        st.write(f"Data updated.")