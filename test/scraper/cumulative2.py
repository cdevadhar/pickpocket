import os
import json
import matplotlib.pyplot as plt
import numpy as np
import math

# SIMMING STANDARD ONLY PICKS
profit_threshold = 0.5744
# simulating parlays on each day
money_power = 1000
money_daily_power = [1000]
money_flex = 1000
money_daily_flex = [1000]
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
        money_power = money_power-moneyIn+moneyBack

        totalFlexes = math.comb(len(keys), 3)
        flexesHit3 = math.comb(numHit, 3)
        flexesHit2 = parlaysHit*(len(keys)-numHit)
        moneyInFlex = totalFlexes*5
        moneyBackFlex = flexesHit3*2.25+flexesHit2*1.25
        money_flex = money_flex-moneyInFlex+moneyBackFlex
        print("Money left for power:", money_power)
        # print("Money left for flex:", money_flex)
    money_daily_power.append(money_power)
    money_daily_flex.append(money_flex)
    days.append(day)
    day+=1
plt.plot(days, money_daily_power)
# plt.plot(days, money_daily_flex)
plt.xlabel("Day of simulation")
plt.ylabel("Money")
# plt.legend(["Power", "Flex"])
plt.show()
# plotting expected vs actual for all
all_analytics = []
for filename in os.listdir('analyticsFiles/standardOnly'):
    f = os.path.join('analyticsFiles/standardOnly', filename)
    analytics = json.load(open(f))
    all_analytics.extend(analytics)

sorted_analytics = sorted(all_analytics, key=lambda x: x['lower_percentage_under'])
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
        if (result['lower_percentage_under']>prob_higher):
            break
        if (result['lower_percentage_under']<prob_lower):
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
plt.plot([0, 1], [1, 0])
plt.plot([0, 1], [1-profit_threshold, 1-profit_threshold])
plt.legend(['Worst case prediction vs actual results', 'Threshold for profit'])
plt.show()
