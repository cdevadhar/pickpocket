#!/usr/bin/env python3

import json
import time
import os
import pandas as pd
from nba_api.stats.endpoints import playergamelogs
from nba_api.stats.static import players
import scipy.stats as stats
import numpy as np

def ks_normal_test(sample, mean, std_dev):
    if std_dev <= 0:
        std_dev = 0.01
    _, p_value = stats.kstest(sample, 'norm', args=(mean, std_dev))
    return p_value

def truncated_normal_pdf(x, mean, std_dev):
    if std_dev <= 0:
        std_dev = 0.01
    a = (0 - mean) / std_dev
    b = np.inf
    return stats.truncnorm.pdf(x, a, b, loc=mean, scale=std_dev)

def lowest_mean_and_std(sample, threshold=0.05, step=0.1):
    mean = np.mean(sample)
    std_dev = np.std(sample)
    while True:
        p = ks_normal_test(sample, mean, std_dev)
        if p < threshold:
            return mean+step, std_dev
        mean -= step

def highest_mean_and_std(sample, threshold=0.05, step=0.1):
    mean = np.mean(sample)
    std_dev = np.std(sample)
    while True:
        p = ks_normal_test(sample, mean, std_dev)
        if p < threshold:
            return mean - step, std_dev  # Return the last valid mean
        mean += step

def prob_under_for_std_dist(x, mean, std_dev):
    if std_dev == 0:
        std_dev = 0.01
    a = (0 - mean) / std_dev
    b = np.inf
    return stats.truncnorm.cdf(x, a, b, loc=mean, scale=std_dev)

def prob_over_for_std_dist(x, mean, std_dev):
    return 1-prob_under_for_std_dist(x, mean, std_dev)

with open('lineJsons/2025-01-07.json') as f:
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

statNameToAbbrev = {"Points" : "PTS", "Pts+Asts": "PTS+AST", "Pts+Rebs": "PTS+REB", "Pts+Rebs+Asts": "PTS+REB+AST"}
STATS_LIST = ['PTS', 'REB', 'AST', 'STL', 'BLK', 'FTM', 'FGM', 'FG3M', 'TOV']
player_gamelogs = {}
count = 0
for player in included_players:
    try:
        player_name = player['attributes']['name']
        if os.path.exists('playerData/2025-01-08/'+player_name+'.csv'):
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
        queried_stats.to_csv('playerData/2025-01-08/'+player_name+'.csv', index=False)
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
        queried_stats = pd.read_csv('playerData/2025-01-08/'+player_name+'.csv')
        statType = statNameToAbbrev[stat['attributes']['stat_type']]
        pstats = 0
        if statType in STATS_LIST:
            pstats = queried_stats[statType]
        elif "+" in statType:
            statType = statType.split("+")
            queried_stats = queried_stats[statType]
            pstats = queried_stats.sum(axis=1)
        hitLine = pstats>float(stat['attributes']['line_score'])
        sample = pstats.values
        lowest_mean, std_dev = lowest_mean_and_std(sample)
        highest_mean, _ = highest_mean_and_std(sample)
        if std_dev <= 0:
            std_dev = 0.01
        actual_mean = np.mean(sample)
        p_value = ks_normal_test(pstats, lowest_mean, std_dev)

        probability_over = prob_over_for_std_dist(stat['attributes']['line_score'], lowest_mean, std_dev)
        probability_under = prob_under_for_std_dist(stat['attributes']['line_score'], highest_mean, std_dev)
        print({"games": int(hitLine.shape[0]), "hit": int(hitLine.sum()), "percentage": float(hitLine.sum()/hitLine.shape[0])})
        pickObj = {"player": player_name, "line": stat["attributes"]["line_score"], "statType": statType, "games": int(hitLine.shape[0]), "hit": int(hitLine.sum()), "percentage": max(probability_over, probability_under)}
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
for pick in standard[-30:]:
    print(pick)
# print(goblins[-20:])
# print(demons[-20:])