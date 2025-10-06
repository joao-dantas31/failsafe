import os

import discord
import requests
import pandas as pd
import numpy as np
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow,Flow
from google.oauth2 import service_account
from google.auth.transport.requests import Request

load_dotenv()

client = discord.Client()
url = "https://stats.bungie.net/Platform/Destiny2/Stats/PostGameCarnageReport/{idRaid}/"

SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

SAMPLE_SPREADSHEET_ID_INPUT = os.getenv('SAMPLE_SPREADSHEET_ID_INPUT')
SAMPLE_RANGE_NAME = 'A1:AA1000'
BUNGIE_API_KEY = os.getenv('BUNGIE_API_KEY')

emoji = '\N{SQUARED OK}'

def write(columnsList):
    creds = service_account.Credentials.from_service_account_file(
                'aut.json', scopes=SCOPES)

    service = build('sheets', 'v4', credentials=creds)

    # Call the Sheets API
    sheet = service.spreadsheets()
    result_input = sheet.values().get(spreadsheetId=SAMPLE_SPREADSHEET_ID_INPUT,
                                      range=SAMPLE_RANGE_NAME).execute()
    values_input = result_input.get('values', [])

    if not values_input and not values_expansion:
        print('No data found.')
    else:
        df = pd.DataFrame(values_input[1:], columns=values_input[0])
        df = df.apply(pd.to_numeric)
        df['raidId'] = df['raidId'].astype(str)
        
        for column in columnsList.keys():
            if column not in df:
                df.loc[:, column] = 0
                
        for column in list(df):
            if column not in columnsList:
                columnsList[column] = 0
        df.loc[df.shape[0]] = columnsList

        service.spreadsheets().values().update(
        spreadsheetId=SAMPLE_SPREADSHEET_ID_INPUT,
        valueInputOption='RAW',
        range=SAMPLE_RANGE_NAME,
        body=dict(
            majorDimension='ROWS',
            values=df.T.reset_index().T.values.tolist())
        ).execute()

@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.startswith('$r'):
        request = requests.get(url.format(idRaid = message.content[3:]), headers={"x-api-key": BUNGIE_API_KEY})
        data = request.json().get('Response')
        participantes = data.get('entries')
        columnsList = {'raidId': message.content[3:]}
        for user in participantes:
            if(user.get('values').get('completed').get('basic').get('value')):
                columnsList[user.get('player').get('destinyUserInfo').get('membershipId')] = 1
        write(columnsList)
        await message.add_reaction(emoji)

client.run(os.getenv('BOT_SECRET'))
