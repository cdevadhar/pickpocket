from nba_api.stats.endpoints import playergamelogs
from nba_api.stats.static import players
import unicodedata
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

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


def process_line(data):
    try:
        # Get the JSON payload. Expects player, statType, line
        playerName = data['player']
        if (playerName in accented_players):
            playerName = accented_players[playerName]
        player = players.find_players_by_full_name(playerName)[0]
        gamelogs = playergamelogs.PlayerGameLogs(player_id_nullable=player['id'], season_nullable="2024-25")
        pra = gamelogs.get_data_frames()[0][['PTS', 'REB', 'AST']]
        stats = None
        statType = data['statType']
        if (statType=='PTS' or statType=='REB' or statType=='AST'):
            stats = pra[data['statType']]
        elif (statType=='PRA'):
            stats = pra.sum(axis=1)
        hitLine = stats>float(data['line'])
        return {"games": int(hitLine.shape[0]), "hit": int(hitLine.sum()), "percentage": float(hitLine.sum()/hitLine.shape[0])}

    except Exception as e:
        print(e)
        return {"error": str(e)}
    
@app.route('/checkParlay', methods=['POST'])
def process_parlay():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON provided"}), 400
        parlay = data["parlay"]
        probabilities = []
        for pick in parlay:
            processed_pick = process_line(pick)
            probabilities.append(processed_pick)
        print(probabilities)
        payouts = data["payouts"]
        ev = 0
        for i in range(0, 2**len(probabilities)):
            bitshit = i
            hits = 0
            currentProb = 1
            for j in range (0, len(probabilities)):
                if (bitshit & 1):
                    currentProb = currentProb * probabilities[j]['percentage']
                    hits+=1
                else:
                    currentProb = currentProb * (1-probabilities[j]['percentage'])
                bitshit = bitshit >> 1
            index = len(probabilities)-hits
            if (index>=len(payouts)):
                ev-=currentProb
            else:
                ev+=currentProb*payouts[index]
            print({"hits": hits, "probability": currentProb})
        return {"probabilities": probabilities, "ev": ev}
    except Exception as e:
        print(e)
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # Run the Flask server
    app.run(debug=True)