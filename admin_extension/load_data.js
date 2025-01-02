const PICKS_ENDPOINT = "https://api.prizepicks.com/projections?league_id=7";
const PRIVATE_SERVER = "http://localhost:8080/add-json";

fetch(PICKS_ENDPOINT, { method: "GET" })
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
    fetch(PRIVATE_SERVER, {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify(data)
    })
      .then(response => {
        if (response.ok) {
        //   console.log("Data successfully posted to server:", data);
        } else {
          return response.text().then(text => {
            throw new Error(`${response.status}: ${text}`);
          });
        }
      })
      .catch(error => {
        console.error("Error posting to server:", error);
      });
  })
  .catch(error => {
    console.error("Error fetching from PICKS_ENDPOINT:", error);
  });
