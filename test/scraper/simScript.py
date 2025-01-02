
import math
import json
import os
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from datetime import date
import time
from nba_api.stats.endpoints import playergamelogs
from nba_api.stats.static import players

today = date.today()
# os.mkdir("playerData/"+str(today))

all_jsons = os.listdir('lineJsons')
paths = [os.path.join("lineJsons", file) for file in all_jsons]
latest_lines = max(paths, key=os.path.getmtime)
todays_lines = os.path.join("lineJsons", today)

with open(latest_lines) as f:
    jsonFile = json.load(f)
    y_data = jsonFile['data']
    y_included = jsonFile['included']

with open(todays_lines) as f:
    jsonFile = json.load(f)
    t_data = jsonFile['data']
    t_included = jsonFile['included']

included_players = []
for inc in y_included:
    if (inc['type']=='new_player'):
        included_players.append(inc)
for inc in t_included:
    if (inc['type']=='new_player'):
        if inc not in included_players:
            included_players.append(inc)

def find_player(id):
    for player in included_players:
        if (player['id']==id):
            return player['attributes']['name']
    return None
statNameToAbbrev = {"Points" : "PTS", "Rebounds": "REB", "Assists": "AST", "Blks+Stls": "BLK+STL", "Rebs+Asts": "REB+AST", "Pts+Asts": "PTS+AST", "Pts+Rebs": "PTS+REB", "Pts+Rebs+Asts": "PTS+REB+AST", "Blocked Shots": "BLK", "Steals": "STL", "Turnovers": "TOV", "Free Throws Made": "FTM", "FG Made": "FGM", "3-PT Made": "FG3M"}
STATS_LIST = ['PTS', 'REB', 'AST', 'STL', 'BLK', 'FTM', 'FGM', 'FG3M', 'TOV']

# get data for all players involved in yesterdays or todays lines (will build up over time to basically every nba player)
for player in included_players:
    try:
        player_name = player['attributes']['name']
        if os.path.exists('playerData/'+today+'/'+player_name+'.csv'):
            print("already exists")
            continue
        print(player_name)
        if ('+' in player_name):
            # combo stat, skip for now
            continue
        player_obj = players.find_players_by_full_name(player_name)[0]
        gamelogs = playergamelogs.PlayerGameLogs(player_id_nullable=player_obj['id'], season_nullable="2024-25")
        queried_stats = gamelogs.get_data_frames()[0][STATS_LIST]
        queried_stats.to_csv('playerData/'+today+'/'+player_name+'.csv', index=False)
        time.sleep(5)
    except Exception as e:
        print('error', e)

# check yesterday's hit rates
analytics = []
for stat in y_data:
    # print(stat)
    player_name = find_player(stat['relationships']['new_player']['data']['id'])
    try:
        if stat['attributes']['stat_type'] not in statNameToAbbrev:
            continue
        print (player_name)
        print(stat['attributes']['line_score'], stat['attributes']['stat_type'])
        yesterday_stats = pd.read_csv('playerData/'+os.path.basename(latest_lines)+'/'+player_name+'.csv')
        today_stats = pd.read_csv('playerData/'+today+'/'+player_name+'.csv')
        statType = statNameToAbbrev[stat['attributes']['stat_type']]
        stats = 0
        if statType in STATS_LIST:
            stats = yesterday_stats[statType]
            hits = today_stats[statType]
        elif "+" in statType:
            statType = statType.split("+")
            yesterday_stats = yesterday_stats[statType]
            hits_unsummed = today_stats[statType]
            stats = yesterday_stats.sum(axis=1)
            hits = hits_unsummed.sum(axis=1)
        hitLine = stats>float(stat['attributes']['line_score'])
        # actualHits = hits>float(stat['attributes']['line_score'])
        # print({"games": int(hitLine.shape[0]), "hit": int(hitLine.sum()), "percentage": float(hitLine.sum()/hitLine.shape[0])})
        # print(hit_stats)
        hit_or_not = hits>float(stat['attributes']['line_score'])
        print("expected percentage", float(hitLine.sum()/hitLine.shape[0]))
        print("actual outcome", hit_or_not.sum(), "/", hit_or_not.shape[0])
        if (hit_or_not.shape[0]>0):
            for i in range(hit_or_not.sum()):
                analytics.append({"percentage": float(hitLine.sum()/hitLine.shape[0]), "hit": 1, "playerProp": player_name+" "+str(stat['attributes']['line_score'])+" "+str(stat['attributes']['stat_type'])})
                
            for i in range(hit_or_not.shape[0]-hit_or_not.sum()):
                analytics.append({"percentage": float(hitLine.sum()/hitLine.shape[0]), "hit": 0, "playerProp": player_name+" "+str(stat['attributes']['line_score'])+" "+str(stat['attributes']['stat_type'])})
    except Exception as e:      
        print("error", e)

sorted_analytics = sorted(analytics, key=lambda x: x['percentage'])
expected = []
actual = []

reasonable = []

for i in range(20):
    prob_lower = 0.05*i
    prob_higher = 0.05*(i+1)
    total = 0
    hits = 0
    for result in sorted_analytics:
        if (result['percentage']>prob_higher):
            break
        if (result['percentage']<prob_lower):
            continue
        total+=1
        if (result["hit"]==1):
            hits+=1
    if (total==0):
        continue
    print("Expected ", prob_lower, " to ", prob_higher)
    print("Actual", hits/total, hits, "/", total)
    expected.append((prob_lower+prob_higher)/2)
    actual.append(hits/total)

print(reasonable)

plt.scatter(np.array(expected), np.array(actual))
plt.show()