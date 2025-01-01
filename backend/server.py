from nba_api.stats.endpoints import playergamelogs
from nba_api.stats.static import players
import unicodedata
import time
import requests
import traceback
from bs4 import BeautifulSoup
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

lastInjuryUpdate = None
injuries = {}

STATS_LIST = ['PTS', 'REB', 'AST', 'STL', 'BLK', 'FTM', 'FGM', 'FG3M', 'TOV', 'FGA', "FG3A"]
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
        player = players.find_players_by_full_name(playerName)[0]
        gamelogs = playergamelogs.PlayerGameLogs(player_id_nullable=player['id'], season_nullable="2024-25")
        queried_stats = gamelogs.get_data_frames()[0][STATS_LIST]
        stats = 0
        statType = data['statType']
        if statType in STATS_LIST:
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
        
        return {"games": int(hitLine.shape[0]), "hit": int(hitLine.sum()), "percentage": float(hitLine.sum()/hitLine.shape[0]), "injurystatus": status}

    except Exception as e:
        print(e)
        return {"error": str(e)}
    
@app.route('/checkHit', methods=['POST'])
def check_hit():
    process_line(request.get_json(), checking_last_game=True)
    
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
        return {"probabilities": probabilities, "payoutodds": payoutOdds, "ev": ev, "injurystatuses": injuryStatuses}
    except Exception as e:
        print(e)
        tb = traceback.extract_tb(e.__traceback__)
        print("Exception occurred on line", tb[-1].lineno)
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # Run the Flask server
    app.run(debug=True)