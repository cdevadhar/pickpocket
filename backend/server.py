from nba_api.stats.endpoints import playergamelogs
from nba_api.stats.static import players
import unicodedata
import time
import requests
import traceback
from bs4 import BeautifulSoup
from flask import Flask, request, jsonify
from flask_cors import CORS
import numpy as np
import scipy.stats as stats
from datetime import date, timedelta
import os
import pandas as pd

def ks_normal_test(sample, mean, std_dev):
    _, p_value = stats.kstest(sample, 'norm', args=(mean, std_dev))
    return p_value

def truncated_normal_pdf(x, mean, std_dev):
    a = (0 - mean) / std_dev
    b = np.inf
    return stats.truncnorm.pdf(x, a, b, loc=mean, scale=std_dev)

def lowest_mean_and_std(sample, threshold, step=0.1):
    mean = np.mean(sample)
    std_dev = np.std(sample)
    while True:
        p = ks_normal_test(sample, mean, std_dev)
        if p < threshold:
            return mean+step, std_dev
        mean -= step

def highest_mean_and_std(sample, threshold, step=0.1):
    mean = np.mean(sample)
    std_dev = np.std(sample)
    while True:
        p = ks_normal_test(sample, mean, std_dev)
        if p < threshold:
            return mean+step, std_dev
        mean += step

def prob_under_for_std_dist(x, mean, std_dev):
    if std_dev == 0:
        std_dev = 0.01
    a = (0 - mean) / std_dev
    b = np.inf
    return stats.truncnorm.cdf(x, a, b, loc=mean, scale=std_dev)

def prob_over_for_std_dist(x, mean, std_dev):
    return 1-prob_under_for_std_dist(x, mean, std_dev)

app = Flask(__name__)
CORS(app)

lastInjuryUpdate = None
injuries = {}

STATS_LIST = ['PTS', 'REB', 'AST', 'STL', 'BLK', 'FTM', 'FGM', 'FG3M', 'TOV', 'FGA', "FG3A", "OREB", "DREB", "FTA"]
NBA_ABBREVIATIONS = nba_teams = {
    "ATL": "Atlanta Hawks",
    "BOS": "Boston Celtics",
    "CHA": "Charlotte Hornets",
    "CHI": "Chicago Bulls",
    "CLE": "Cleveland Cavaliers",
    "DAL": "Dallas Mavericks",
    "DEN": "Denver Nuggets",
    "DET": "Detroit Pistons",
    "GSW": "Golden State Warriors",
    "HOU": "Houston Rockets",
    "IND": "Indiana Pacers",
    "LAC": "Los Angeles Clippers",
    "LAL": "Los Angeles Lakers",
    "MEM": "Memphis Grizzlies",
    "MIA": "Miami Heat",
    "MIL": "Milwaukee Bucks",
    "MIN": "Minnesota Timberwolves",
    "NOP": "New Orleans Pelicans",
    "NYK": "New York Knicks",
    "BKN": "Brooklyn Nets",
    "OKC": "Oklahoma City Thunder",
    "ORL": "Orlando Magic",
    "PHI": "Philadelphia 76ers",
    "PHX": "Phoenix Suns",
    "POR": "Portland Trail Blazers",
    "SAC": "Sacramento Kings",
    "SAS": "San Antonio Spurs",
    "TOR": "Toronto Raptors",
    "UTA": "Utah Jazz",
    "WAS": "Washington Wizards"
}

def has_accent(word):
    normalized = unicodedata.normalize('NFD', word)
    return any(unicodedata.category(char) == 'Mn' for char in normalized)
def remove_accents(word):
    normalized = unicodedata.normalize('NFD', word)
    return ''.join(char for char in normalized if unicodedata.category(char) != 'Mn')

all_players = players.get_active_players()
accented_players = {}
for player in all_players:
    if (has_accent(player['full_name'])):
        no_accents = remove_accents(player['full_name'])
        accented_players[no_accents] = player['full_name']

def process_line(data, checking_last_game=False):
    try:
        # print(data)
        # print("requesting")
        playerName = data['player']
        if (playerName in accented_players):
            playerName = accented_players[playerName]
        todayDate = date.today()
        today = todayDate.strftime("%Y-%m-%d")
        playerDataDirectory = "../test/scraper/playerData/"+today
        playerDataFile = playerDataDirectory+"/"+playerName+".csv"
        queried_stats = None
        print(playerDataDirectory)
        if (os.path.exists(playerDataFile)):
            print("stats are already saved")
            print(playerDataFile)
            queried_stats = pd.read_csv(playerDataFile)
        else:
            print("requesting")
            player = players.find_players_by_full_name(playerName)[0]
            gamelogs = playergamelogs.PlayerGameLogs(player_id_nullable=player['id'], season_nullable="2024-25")
            queried_stats = gamelogs.get_data_frames()[0][STATS_LIST]
            if (os.path.exists(playerDataDirectory)):
                print("saving to a file")
                # save to a file
                queried_stats.to_csv(playerDataDirectory+'/'+playerName+'.csv', index=False)
        stats = 0
        statType = data['statType']
        if statType == "FS":
            stats = queried_stats["PTS"] + (1.2 * queried_stats["REB"]) + (1.5 * queried_stats["AST"]) + (3 * queried_stats["BLK"]) + (3 * queried_stats["STL"]) - queried_stats["TOV"]
        elif statType in STATS_LIST:
            stats = queried_stats[statType]
        elif "+" in statType:
            statType = statType.split("+")
            queried_stats = queried_stats[statType]
            stats = queried_stats.sum(axis=1)
        if checking_last_game:
            stats = int(stats.iloc[0])
        if (data["pick"]=="more"):
            hitLine = stats>float(data['line'])
        else:
            hitLine = stats<float(data['line'])
        if checking_last_game:
            return hitLine
        
        status = "Healthy"
        if NBA_ABBREVIATIONS[data["team"]] in injuries and data["player"] in injuries[NBA_ABBREVIATIONS[data["team"]]]:
            status = injuries[NBA_ABBREVIATIONS[data["team"]]][data["player"]]

        ret = {"games": int(hitLine.shape[0]), "hit": int(hitLine.sum()), "percentage": float(hitLine.sum()/hitLine.shape[0]), "injurystatus": status}
        if "PTS" in statType:
            wc_lowest_mean, wc_std_dev = lowest_mean_and_std(stats.values, 0.05)
            wc_highest_mean, _ = highest_mean_and_std(stats.values, 0.05)

            mc_lowest_mean, mc_std_dev = lowest_mean_and_std(stats.values, 0.2)
            mc_highest_mean, _ = highest_mean_and_std(stats.values, 0.2)

            if data["pick"]=="more":
                worstcase = prob_over_for_std_dist(float(data['line']), wc_lowest_mean, wc_std_dev)
                midcase = prob_over_for_std_dist(float(data['line']), mc_lowest_mean, mc_std_dev)
            else:
                worstcase = prob_under_for_std_dist(float(data['line']), wc_highest_mean, wc_std_dev)
                midcase = prob_under_for_std_dist(float(data['line']), mc_highest_mean, mc_std_dev)
            ret["worstcase"] = worstcase
            ret["midcase"] = midcase
        return ret

    except Exception as e:
        print(e)
        return {"error": str(e)}
    
@app.route('/checkHit', methods=['POST'])
def check_hit():
    return process_line(request.get_json(), checking_last_game=True)
    
def update_injuries():
    global lastInjuryUpdate
    global injuries
    now = time.time()
    if lastInjuryUpdate is None or now - lastInjuryUpdate > 3600:
        try: 
            injuries = {}
            lastInjuryUpdate = now
            res = requests.get("https://www.espn.com/nba/injuries", headers={"User-Agent": "curl/7.64.1"})
            soup = BeautifulSoup(res.text, "html.parser")
            teams = soup.select("div.ResponsiveTable.Table__league-injuries")
            for team in teams:
                name = team.select_one("span.injuries__teamName")
                # print("Team Name: ", name.text)
                injuries[name.text] = {}
                players = [{x.text: y.text} for x, y in zip(team.select("td.col-name"), team.select("td.col-stat"))]
                for player in players:
                    # print(player)
                    injuries[name.text].update(player)
        except requests.RequestException as e:
            print(f"Error fetching injury updates: {e}")
    
@app.route('/checkParlay', methods=['POST'])
def process_parlay():
    try:
        update_injuries()
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON provided"}), 400
        parlay = data["parlay"]
        probabilities = []
        injuryStatuses = []
        for pick in parlay:            
            processed_pick = process_line(pick)
            probabilities.append(processed_pick)
            injuryStatuses.append(processed_pick["injurystatus"])
        # print(injuryStatuses)
        # print(probabilities)
        payouts = data["payouts"]
        if len(payouts) == 0:
            return {"probabilities": probabilities, "injurystatuses": injuryStatuses}
        payoutOdds, ev = calc_evs(probabilities, payouts)
        ret = {"probabilities": probabilities, "payoutodds": payoutOdds, "ev": ev, "injurystatuses": injuryStatuses}

        worstcases = []
        for prob in probabilities:
            if "worstcase" in prob:
                worstcases.append({"percentage": prob["worstcase"]})
            else:
                return ret
        worstPayoutOdds, worstEV = calc_evs(worstcases, payouts)
        ret["worstPayoutOdds"] = worstPayoutOdds
        ret["worstEV"] = worstEV
        return ret
    except Exception as e:
        print(e)
        tb = traceback.extract_tb(e.__traceback__)
        print("Exception occurred on line", tb[-1].lineno)
        return jsonify({"error": str(e)}), 500
    
def calc_evs(probabilities, payouts):
    payoutOdds = [0 for _ in payouts]
    ev = 0
    for bitshit in range(0, 2**len(probabilities)):
        hits = 0
        currentProb = 1
        for j in range (0, len(probabilities)):
            if (bitshit & 1):
                currentProb = currentProb * probabilities[j]['percentage']
                hits+=1
            else:
                # print(currentProb)
                # print(probabilities[j])
                currentProb = currentProb * (1-probabilities[j]['percentage'])
            bitshit = bitshit >> 1
        i = len(probabilities)-hits
        if (i<len(payouts)):
            payoutOdds[i] += currentProb
            ev += currentProb*payouts[i]
        # print({"hits": hits, "probability": currentProb})
    return payoutOdds, ev

if __name__ == '__main__':
    # Run the Flask server
    app.run(debug=True)