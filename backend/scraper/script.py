import requests
import json
import time
import os
import pandas as pd
from nba_api.stats.endpoints import playergamelogs
from nba_api.stats.static import players

session = requests.Session()
session.headers.update({'User-Agent': 'Chrome/102.0.0.0'})

lines_response = session.get("https://api.prizepicks.com/projections?league_id=7")
print(lines_response)