const DATA_ENDPOINT = "https://api.prizepicks.com/game_types";
const headers = {
    "Content-Type": "application/json"
};
const payload = { // TODO: ACTUALLY ADD PAYLOAD LOGIC
  new_wager: {
    amount_bet_cents: 0,
    picks: [
      { wager_type: "over", projection_id: "3562308" },
      { wager_type: "over", projection_id: "3562319" },
      { wager_type: "over", projection_id: "3562258" },
      { wager_type: "over", projection_id: "3562267" }
    ],
    pick_protection: false
  },
  lat: null,
  lng: null,
  game_mode: "pickem",
  token: "your_token_here"
};

fetch(DATA_ENDPOINT, {
    method: "POST",
    headers: headers,
    body: JSON.stringify(payload)
  })
    .then(response => {
      if (response.ok) {
        return response.json();
      } else {
        return response.text().then(text => {
          throw new Error(`${response.status}: ${text}`);
        });
      }
    })
    .then(data => {
      console.log(data);
      // TODO: PROCESS DATA
    })
    .catch(error => {
      console.error("Error:", error);
    });