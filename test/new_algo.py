#!/usr/bin/env python3

import numpy as np
import scipy.stats as stats
import matplotlib.pyplot as plt

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

sample = [35, 27, 23, 43, 37, 20, 30, 13, 21, 30, 23, 26, 32, 35, 21, 18, 30, 31, 30, 25]
# sample = [38, 10, 31, 2, 26, 19, 30, 23, 24, 23, 28, 14, 19, 23, 26, 13, 37, 36, 12, 27, 24, 18, 20, 17]
# sample = [33, 20, 28, 33, 20, 18, 29, 27, 23, 24, 27, 26, 21, 15, 35, 21, 26, 22, 20, 17, 19, 22, 22, 24, 21, 33, 28]
# sample = [12, 11, 5, 9, 5, 6, 10, 17, 8, 13, 17, 13, 18, 16, 6, 11, 7, 6, 12, 18, 6, 4, 12, 2, 16]

lowest_mean, std_dev = lowest_mean_and_std(sample)
actual_mean = np.mean(sample)
line = actual_mean - std_dev
print(f"Line: {line}")
p_value = ks_normal_test(sample, lowest_mean, std_dev)
print(f"Lowest Mean: {lowest_mean}")
print(f"Actual Mean: {actual_mean}")
print(f"Standard Deviation: {std_dev}")
print(f"P-value: {p_value}")

# print(f"Probability Under: {prob_under_for_std_dist(line, lowest_mean, std_dev)}")
print(f"New Worst-Case Probability Over: {prob_over_for_std_dist(line, lowest_mean, std_dev)}")
print(f"Raw Probability Over: {(np.array(sample) > line).sum() / float(len(sample))}")

plt.hist(sample, bins=10, density=True, alpha=0.6, color='g', label=f'Sample Distribution ({round((np.array(sample) > line).sum() / float(len(sample)), 4) * 100}%)')
x = np.linspace(0, max(sample), 1000)
plt.plot(x, truncated_normal_pdf(x, lowest_mean, std_dev), label='Lowest Truncated Normal Distribution', color='r', linestyle='--')
plt.plot(x, truncated_normal_pdf(x, actual_mean, std_dev), label='Actual Normal Distribution', color='b', linestyle='--')
plt.fill_between(x[x >= line], 0, truncated_normal_pdf(x[x >= line], lowest_mean, std_dev),
                 color='red', alpha=0.7, label=f'Probability of Hitting ({round(prob_over_for_std_dist(line, lowest_mean, std_dev), 4) * 100}%)')
plt.xlabel('Value')
plt.ylabel('Frequency')
plt.title('Sample Distribution vs Truncated Normal Distribution')
plt.legend()
plt.show()
