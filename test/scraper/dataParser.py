#!/usr/bin/env python3

import json
import time
import os
import pandas as pd
from nba_api.stats.endpoints import playergamelogs
from nba_api.stats.static import players

with open('nbaData.json') as f:
    jsonFile = json.load(f)
    data = jsonFile['data']
    included = jsonFile['included']

included_players = []
for inc in included:
    if (inc['type']=='new_player'):
        included_players.append(inc)

def find_player(id):
    for player in included_players:
        if (player['id']==id):
            return player['attributes']['name']
    return None

statNameToAbbrev = {"Points" : "PTS", "Rebounds": "REB", "Assists": "AST", "Blks+Stls": "BLK+STL", "Rebs+Asts": "REB+AST", "Pts+Asts": "PTS+AST", "Pts+Rebs": "PTS+REB", "Pts+Rebs+Asts": "PTS+REB+AST", "Blocked Shots": "BLK", "Steals": "STL", "Turnovers": "TOV", "Free Throws Made": "FTM", "FG Made": "FGM", "3-PT Made": "FG3M"}
STATS_LIST = ['PTS', 'REB', 'AST', 'STL', 'BLK', 'FTM', 'FGM', 'FG3M', 'TOV']
player_gamelogs = {}
count = 0
for player in included_players:
    try:
        player_name = player['attributes']['name']
        if os.path.exists('playerDataCheck/'+player_name+'.csv'):
            print("already exists")
            continue
        print(player_name)
        if ('+' in player_name):
            # combo stat, skip for now
            continue
        player_obj = players.find_players_by_full_name(player_name)[0]
        gamelogs = playergamelogs.PlayerGameLogs(player_id_nullable=player_obj['id'], season_nullable="2024-25")
        queried_stats = gamelogs.get_data_frames()[0][STATS_LIST]
        player_gamelogs[player_name] = queried_stats
        queried_stats.to_csv('playerDataCheck/'+player_name+'.csv', index=False)
        time.sleep(5)
    except Exception as e:
        print('error', e)

standard = []
goblins = []
demons = []

for stat in data:
    player_name = find_player(stat['relationships']['new_player']['data']['id'])
    try:
        if stat['attributes']['stat_type'] not in statNameToAbbrev:
            continue
        print (player_name)
        print(stat['attributes']['line_score'], stat['attributes']['stat_type'])
        queried_stats = pd.read_csv('playerData/'+player_name+'.csv')
        statType = statNameToAbbrev[stat['attributes']['stat_type']]
        stats = 0
        if statType in STATS_LIST:
            stats = queried_stats[statType]
        elif "+" in statType:
            statType = statType.split("+")
            queried_stats = queried_stats[statType]
            stats = queried_stats.sum(axis=1)
        hitLine = stats>float(stat['attributes']['line_score'])
        print({"games": int(hitLine.shape[0]), "hit": int(hitLine.sum()), "percentage": float(hitLine.sum()/hitLine.shape[0])})
        pickObj = {"player": player_name, "line": stat["attributes"]["line_score"], "statType": statType, "games": int(hitLine.shape[0]), "hit": int(hitLine.sum()), "percentage": float(hitLine.sum()/hitLine.shape[0])}
        if stat['attributes']['odds_type']=='standard':
            standard.append(pickObj)
        elif stat['attributes']['odds_type']=='goblin':
            goblins.append(pickObj)
        else:
            demons.append(pickObj)
    except Exception as e:
        print('error', e)

standard = sorted(standard, key=lambda d: d['percentage'])
goblins = sorted(goblins, key=lambda d: d['percentage'])
demons = sorted(demons, key=lambda d: d['percentage'])
print(len(standard))
print(len(goblins))
print(len(demons))
print(standard[-20:])
print(goblins[-20:])
print(demons[-20:])