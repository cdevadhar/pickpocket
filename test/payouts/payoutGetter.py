#!/usr/bin/env python3

import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

session = requests.Session()
LOGIN_EMAIL = os.getenv("LOGIN_EMAIL")
LOGIN_PASSWORD = os.getenv("LOGIN_PASSWORD")

headers = {
    "Content-Type": "application/json"
}

LOGIN_ENDPOINT = 'https://api.prizepicks.com/users/sign_in'

login_payload = {
    "user": {
        "email": LOGIN_EMAIL,
        "password": LOGIN_PASSWORD,
        "remember_me": True
    },
    "token": ""
}


login_res = session.post(LOGIN_ENDPOINT, headers=headers, data=json.dumps(login_payload))

if login_res.status_code == 200:
    print("Login successful")
    print("Cookies after login:", session.cookies.get_dict()) 
else:
    print(f"Error during login: {login_res.status_code} - {login_res.text}")
    exit()

DATA_ENDPOINT = "https://api.prizepicks.com/game_types"

payload = {
    "new_wager": {
        "amount_bet_cents": 0,
        "picks": [
            {"wager_type": "over", "projection_id": "3562308"},
            {"wager_type": "over", "projection_id": "3562319"},
            {"wager_type": "over", "projection_id": "3562258"},
            {"wager_type": "over", "projection_id": "3562267"}
        ],
        "pick_protection": False
    },
    "lat": None,
    "lng": None,
    "game_mode": "pickem",
    "token": "your_token_here"
}

res = session.post(DATA_ENDPOINT, headers=headers, data=json.dumps(payload))

if res.status_code == 200:
    data = res.json()
    print("Response:", data)
else:
    print(f"Error {res.status_code}: {res.text}")