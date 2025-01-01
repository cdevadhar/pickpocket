import json
import os
import pandas as pd
from nba_api.stats.endpoints import playergamelogs
from nba_api.stats.static import players
import matplotlib.pyplot as plt
import numpy as np

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

player_new_stats = {}
for player in included_players:
    try:
        player_name = player['attributes']['name']
        if os.path.exists('playerData/'+player_name+'.csv') and os.path.exists('playerData/'+player_name+'.csv'):
            file1 = open('playerData/'+player_name+'.csv').readlines()
            file2 = open('playerDataCheck/'+player_name+'.csv').readlines()
            newGames = (len(file2)-len(file1))
            newGameStats = file2[0:newGames+1]
            header = newGameStats[0].strip().split(',')
            pdata = []
            for line in newGameStats[1:]:
                pdata.append([int(x) for x in line.strip().split(',')])
            df = pd.DataFrame(pdata, columns=header)
            player_new_stats[player_name] = df
            print(df)
    except Exception as e:
        print('error', e)

for key in player_new_stats.keys():
    print(player_new_stats[key])

analytics = []
x_axis = []
y_axis = []
for stat in data:
    # print(stat)
    player_name = find_player(stat['relationships']['new_player']['data']['id'])
    try:
        if stat['attributes']['stat_type'] not in statNameToAbbrev:
            continue
        print (player_name)
        print(stat['attributes']['line_score'], stat['attributes']['stat_type'])
        queried_stats = pd.read_csv('playerData/'+player_name+'.csv')
        hit_stats = player_new_stats[player_name]
        statType = statNameToAbbrev[stat['attributes']['stat_type']]
        stats = 0
        if statType in STATS_LIST:
            stats = queried_stats[statType]
            hits = hit_stats[statType]
        elif "+" in statType:
            statType = statType.split("+")
            queried_stats = queried_stats[statType]
            hits_unsummed = hit_stats[statType]
            stats = queried_stats.sum(axis=1)
            hits = hits_unsummed.sum(axis=1)
        hitLine = stats>float(stat['attributes']['line_score'])
        # actualHits = hits>float(stat['attributes']['line_score'])
        # print({"games": int(hitLine.shape[0]), "hit": int(hitLine.sum()), "percentage": float(hitLine.sum()/hitLine.shape[0])})
        # print(hit_stats)
        hit_or_not = hits>float(stat['attributes']['line_score'])
        print("expected percentage", float(hitLine.sum()/hitLine.shape[0]))
        print(hit_or_not.sum(), hit_or_not.shape[0])
        if (hit_or_not.shape[0]>0):
            for i in range(hit_or_not.sum()):
                x_axis.append(float(hitLine.sum()/hitLine.shape[0]))
                y_axis.append(1)
                analytics.append({"percentage": float(hitLine.sum()/hitLine.shape[0]), "hit": 1, "playerProp": player_name+" "+str(stat['attributes']['line_score'])+" "+str(stat['attributes']['stat_type'])})
            for i in range(hit_or_not.shape[0]-hit_or_not.sum()):
                x_axis.append(float(hitLine.sum()/hitLine.shape[0]))
                y_axis.append(0)
                analytics.append({"percentage": float(hitLine.sum()/hitLine.shape[0]), "hit": 0, "playerProp": player_name+" "+str(stat['attributes']['line_score'])+" "+str(stat['attributes']['stat_type'])})
        # print(actualHits)
    except Exception as e:
        print('error', e)

x_axis_np = np.array(x_axis)
y_axis_np = np.array(y_axis)
# plt.scatter(x_axis_np, y_axis_np)
# plt.show()

sorted_analytics = sorted(analytics, key=lambda x: x['percentage'])
expected = []
actual = []

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

plt.scatter(np.array(expected), np.array(actual))
plt.show()
