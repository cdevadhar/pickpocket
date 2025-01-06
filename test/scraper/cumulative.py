import os
import json
import matplotlib.pyplot as plt
import numpy as np

all_analytics = []
for filename in os.listdir('analyticsFiles/all'):
    f = os.path.join('analyticsFiles/all', filename)
    analytics = json.load(open(f))
    all_analytics.extend(analytics)

sorted_analytics = sorted(all_analytics, key=lambda x: x['lower_percentage_over'])
sorted_analytics2 = sorted(all_analytics, key=lambda x: x['emp_percentage'])
print(len(sorted_analytics))
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
plt.show()
