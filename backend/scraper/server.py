from flask import Flask, request
from flask_cors import CORS
import datetime
import json

app = Flask(__name__)
CORS(app)

@app.route("/add-json", methods=['POST'])
def add_json():
    try:
        data = request.get_json()["data"]
        if data is None:
            return {"error": "Invalid JSON data"}, 400
    
        day = str(datetime.datetime.now()).split(" ")[0]

        with open(f'nbaDataJsons/{day}.json', 'w') as f:
            json.dump(data, f)
    except Exception as e:
        return {"error": str(e)}, 400
    
    return {"message": "JSON data saved successfully"}, 200

if __name__ == '__main__':
    # Run the Flask server
    app.run(debug=True, port=8080)