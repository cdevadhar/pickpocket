import os
import json
import matplotlib.pyplot as plt
import numpy as np
import math

# SIMMING STANDARD ONLY PICKS
profit_threshold = 0.574456
# simulating parlays on each day
money = 1000
money_daily = [1000]
days = [1]
day = 2
for filename in os.listdir('analyticsFiles/standardOnly'):
    f = os.path.join('analyticsFiles/standardOnly', filename)
    analytics = json.load(open(f))
    players_taken = {}
    for line in analytics:
        if line['optimal_percentage']>profit_threshold:
            playerName = " ".join(line['playerProp'].split(" ")[0:2])
            hit = line['hit']
            if line['optimal_percentage']==line['lower_percentage_under']:
                hit = 1-hit
            if (playerName in players_taken):
                if (line['optimal_percentage']>players_taken[playerName]['percent']):
                    players_taken[playerName] = {'percent': line['optimal_percentage'], 'hit': hit}
            else:
                players_taken[playerName] = {'percent': line['optimal_percentage'], 'hit': hit}
    # print(players_taken)
    keys = players_taken.keys()
    if (len(keys)>2):
        # u can make at least one parlay
        numHit = 0
        for key in keys:
            if (players_taken[key]['hit']==1):
                numHit+=1
        print(numHit, "/", len(keys))
        parlaysHit = math.comb(numHit, 2)
        totalParlays = math.comb(len(keys), 2)
        moneyIn = totalParlays*5
        moneyBack = parlaysHit*15
        money = money-moneyIn+moneyBack
        print("Money left:", money)
    money_daily.append(money)
    days.append(day)
    day+=1
plt.plot(days, money_daily)
plt.xlabel("Day of simulation")
plt.ylabel("Money")
plt.show()
# plotting expected vs actual for all
all_analytics = []
for filename in os.listdir('analyticsFiles/standardOnly'):
    f = os.path.join('analyticsFiles/standardOnly', filename)
    analytics = json.load(open(f))
    all_analytics.extend(analytics)

sorted_analytics = sorted(all_analytics, key=lambda x: x['lower_percentage_over'])
sorted_analytics2 = sorted(all_analytics, key=lambda x: x['emp_percentage'])

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
        if (result['lower_percentage_over']>prob_higher):
            break
        if (result['lower_percentage_over']<prob_lower):
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
plt.scatter(np.array(expected2), np.array(actual2))
plt.plot([0, 1], [0, 1])
plt.plot([0, 1], [profit_threshold, profit_threshold])
plt.legend(['Worst case prediction vs actual results', 'Threshold for profit'])
plt.show()
