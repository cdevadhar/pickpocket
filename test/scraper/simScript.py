
import json
import os
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from datetime import date, datetime
import time
from nba_api.stats.endpoints import playergamelogs
from nba_api.stats.static import players
import scipy.stats as stats

def ks_normal_test(sample, mean, std_dev):
    _, p_value = stats.kstest(sample, 'norm', args=(mean, std_dev))
    return p_value

def truncated_normal_pdf(x, mean, std_dev):
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

def prob_under_for_std_dist(x, mean, std_dev):
    if std_dev == 0:
        std_dev = 0.01
    a = (0 - mean) / std_dev
    b = np.inf
    return stats.truncnorm.cdf(x, a, b, loc=mean, scale=std_dev)

def prob_over_for_std_dist(x, mean, std_dev):
    return 1-prob_under_for_std_dist(x, mean, std_dev)

todayDate = date.today()
today = todayDate.strftime("%Y-%m-%d")
# os.mkdir("playerData/"+str(today))

all_jsons = os.listdir('lineJsons')
paths = [os.path.join("lineJsons", file) for file in all_jsons]
latest_lines = max(paths, key=os.path.getmtime)
todays_lines = os.path.join("lineJsons", today+'.json')

with open(latest_lines) as f:
    jsonFile = json.load(f)
    y_data = jsonFile['data']
    y_included = jsonFile['included']


included_players = []
for inc in y_included:
    if (inc['type']=='new_player'):
        included_players.append(inc)
def find_player(id):
    for player in included_players:
        if (player['id']==id):
            return player['attributes']['name']
    return None
statNameToAbbrev = {"Points" : "PTS", "Pts+Asts": "PTS+AST", "Pts+Rebs": "PTS+REB", "Pts+Rebs+Asts": "PTS+REB+AST"}
STATS_LIST = ['PTS', 'REB', 'AST', 'STL', 'BLK', 'FTM', 'FGM', 'FG3M', 'TOV', 'GAME_DATE']

if not os.path.exists("playerData/"+today):
    os.mkdir('playerData/'+today)
# get data for all players involved in yesterdays or todays lines (will build up over time to basically every nba player)
for player in included_players:
    try:
        player_name = player['attributes']['name']
        if os.path.exists('playerData/'+today+'/'+player_name+'.csv'):
            print("player data already exists")
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
    print(stat)
    start_time = stat['attributes']['start_time']
    start_date = pd.to_datetime(start_time).date()
    player_name = find_player(stat['relationships']['new_player']['data']['id'])
    try:
        if stat['attributes']['stat_type'] not in statNameToAbbrev:
            continue
        # print (player_name)
        # print(stat['attributes']['line_score'], stat['attributes']['stat_type'])
        line = float(stat['attributes']['line_score'])
        today_stats = pd.read_csv('playerData/'+today+'/'+player_name+'.csv')
        today_stats['GAME_DATE'] = pd.to_datetime(today_stats['GAME_DATE']).dt.date
        # print(today_stats)
        prediction_stats = today_stats.loc[today_stats['GAME_DATE'] < start_date]
        # print(prediction_stats)
        result_stats = today_stats.loc[today_stats['GAME_DATE'] >= start_date]
        # print(result_stats)
        statType = statNameToAbbrev[stat['attributes']['stat_type']]
        # stats = 0
        if statType in STATS_LIST:
            old_stats = prediction_stats[statType]
            new_stats = result_stats[statType]
        elif "+" in statType:
            statType = statType.split("+")
            old_stats_unsummed = prediction_stats[statType]
            old_stats = old_stats_unsummed.sum(axis=1)

            new_stats_unsummed = result_stats[statType]
            new_stats = new_stats_unsummed.sum(axis=1)
        expectedHits = old_stats>line
        actualHits = new_stats>line
        sample = old_stats.values
        print(sample)
        lowest_mean, std_dev = lowest_mean_and_std(sample)
        actual_mean = np.mean(sample)
        print(f"Line: {line}")
        p_value = ks_normal_test(old_stats, lowest_mean, std_dev)
        probability = prob_over_for_std_dist(line, lowest_mean, std_dev)
        print({"games": int(expectedHits.shape[0]), "hit": int(expectedHits.sum()), "percentage": probability})
        print(actualHits.sum(), "/", actualHits.shape[0])
        # print("expected percentage", float(hitLine.sum()/hitLine.shape[0]))
        # print("actual outcome", hit_or_not.sum(), "/", hit_or_not.shape[0])
        if (actualHits.shape[0]>0):
            for i in range(actualHits.sum()):
                analytics.append({"lower_percentage": probability, "emp_percentage": float(expectedHits.sum()/expectedHits.shape[0]), "hit": 1, "playerProp": player_name+" "+str(line)+" "+str(stat['attributes']['stat_type'])})
            for i in range(actualHits.shape[0]-actualHits.sum()):
                analytics.append({"lower_percentage": probability, "emp_percentage": float(expectedHits.sum()/expectedHits.shape[0]), "hit": 0, "playerProp": player_name+" "+str(line)+" "+str(stat['attributes']['stat_type'])})
    except Exception as e:      
        print("error", e)


sorted_analytics = sorted(analytics, key=lambda x: x['lower_percentage'])
sorted_analytics2 = sorted(analytics, key=lambda x: x['emp_percentage'])
print(len(sorted_analytics))
print(len(y_data))
print(sorted_analytics)
expected = []
actual = []

expected2 = []
actual2 = []

reasonable = []

for i in range(20):
    prob_lower = 0.05*i
    prob_higher = 0.05*(i+1)
    total = 0
    hits = 0
    for result in sorted_analytics:
        if (result['lower_percentage']>prob_higher):
            break
        if (result['lower_percentage']<prob_lower):
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

for i in range(20):
    prob_lower = 0.05*i
    prob_higher = 0.05*(i+1)
    total = 0
    hits = 0
    for result in sorted_analytics2:
        if (result['emp_percentage']>prob_higher):
            break
        if (result['emp_percentage']<prob_lower):
            continue
        total+=1
        if (result["hit"]==1):
            hits+=1
    if (total==0):
        continue
    print("Expected ", prob_lower, " to ", prob_higher)
    print("Actual", hits/total, hits, "/", total)
    expected2.append((prob_lower+prob_higher)/2)
    actual2.append(hits/total)
    
plt.scatter(np.array(expected), np.array(actual), label="Using Normal Dist")
plt.scatter(np.array(expected2), np.array(actual2), label="Raw Data")
plt.plot([0, 1], [0, 1])
plt.legend()
plt.show()
