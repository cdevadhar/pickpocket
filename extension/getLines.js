let prevParlay = [];
let prevPayouts = [];
function arraysEqual(a, b) {
    if (a === b) return true;
    if (a == null || b == null) return false;
    if (a.length !== b.length) return false;
    for (var i = 0; i < a.length; ++i) {
        if (typeof a[i] == "object" && typeof b[i]=="object") {
            for (const key of Object.keys(a[i])) {
                if (a[i][key]!=b[i][key]) return false;
            }
            for (const key of Object.keys(b[i])) {
                if (a[i][key]!=b[i][key]) return false;
            }
        }
        else if (a[i] !== b[i]) return false;
    }
    return true;
}

const statNameToAbbrev = {"Points" : "PTS", "Rebounds": "REB", "Assists": "AST", "Blks+Stls": "BLK+STL", "Rebs+Asts": "REB+AST", "Pts+Asts": "PTS+AST", "Pts+Rebs": "PTS+REB", "Pts+Rebs+Asts": "PTS+REB+AST", "Blocked Shots": "BLK", "Steals": "STL", "Turnovers": "TOV", "Free Throws Made": "FTM", "FG Made": "FGM", "3-PT Made": "FG3M", "3-PT Attempted": "FG3A", "FG Attempted": "FGA"}

const mutationObserver = new MutationObserver(() => {
    const picked = document.querySelectorAll('li.entry-prediction .player');
    const payoutArea = document.querySelector(".entry-predictions-game-type");
    if (!payoutArea){
        prevParlay = []
        prevPayouts = []
        return;
    }
    const selectedPayout = payoutArea.querySelector("button.selected");
    if (!selectedPayout) {
        prevParlay = []
        prevPayouts = []
        return;
    }
    const payouts = [...selectedPayout.querySelectorAll("span.payout-multiplier")].map(element => parseFloat(element.textContent.split("X")[0]));
    if (payouts.length == 0) {
        prevParlay = []
        prevPayouts = []
        return;
    }
    const parlay = [];
    // console.log(selectedPayout);
    for (const pick of picked) {
        const name = pick.querySelector('h3').innerHTML;
        const team = pick.querySelector('p.team-position').textContent.split(" - ")[0].slice(-3);
        const opposition = pick.textContent.split(/@ |vs /)[1].slice(0,3);
        const projection = pick.querySelector('.projected-score>.score').textContent;
        const statType = pick.querySelectorAll('.projected-score>div')[1].children[0].innerHTML;
        const overUnderContainer = pick.parentElement.parentElement.querySelector(".over-under");
        const overUnder = overUnderContainer.querySelector("button.selected").textContent.toLowerCase();
        // console.log(name+" "+projection + " "+statType);
        const leg_obj = {"player": name, "line": projection, "statType": statNameToAbbrev[statType], "pick": overUnder, "team": team, "opposition": opposition}
        parlay.push(leg_obj);
    }
    if (arraysEqual(prevParlay, parlay) && arraysEqual(payouts, prevPayouts)) return;
    // console.log(parlay);
    // console.log(payouts);
    const parlayObj = {"parlay": parlay, "payouts": payouts};
    fetch("http://127.0.0.1:5000/checkParlay", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify(parlayObj)
    }).then((res) => {
        return res.json();
    }).then(data => {
        const overUnderContainers = document.querySelectorAll(".over-under");
        // console.log(data);
        // console.log(data["injurystatuses"]);
        const probs = data['probabilities'];
        for (let i=0; i<picked.length; i++) {
            const prob = probs[i];
            const status = data["injurystatuses"][i];
            const existingProj = overUnderContainers[i].querySelector(".hitrate-pickpocket");
            if (existingProj) existingProj.remove();
            const proj = document.createElement("div");
            const displayedProj = Math.round((prob["percentage"] + Number.EPSILON) * 100)
            proj.textContent = `${displayedProj}% (${prob["hit"]}/${prob["games"]})`;
            proj.classList.add('hitrate-pickpocket');
            if (displayedProj < 40){
                proj.style.color = '#e43245';
            }
            else if (displayedProj < 60){
                proj.style.color = '#ffbb33';
            }
            else {
                proj.style.color = "#6eff00";
            }
            proj.style.padding = "5px 3px";
            overUnderContainers[i].append(proj);

            const buttons = overUnderContainers[i].querySelectorAll("button");
            buttons.forEach(button => {
                button.style.flexShrink = '0'; // Prevent shrinking
              });

            const existingStatus = picked[i].querySelector(".injury-status");
            if (existingStatus) existingStatus.remove();

            const availabilityIndicator = document.createElement('button');
            availabilityIndicator.textContent = status;
            availabilityIndicator.style.fontSize = 'small';
            if (status == "Out"){
                availabilityIndicator.style.color = '#e43245';
            }
            else if (status == "Day-To-Day"){
                availabilityIndicator.style.color = '#ffbb33';
            }
            else {
                availabilityIndicator.style.color = "#6eff00";
            }
            availabilityIndicator.classList.add('injury-status');

            picked[i].append(availabilityIndicator);
        }

        let payoutOdds = payoutArea.querySelectorAll(".payout-odds");
        for (const po of payoutOdds) {
            po.remove();
        }

        let winrate = 0;
        const payoutsElements = selectedPayout.querySelectorAll("div.payout");
        for (let i = 0; i < payoutsElements.length; i++) {
            const odds = document.createElement("div");
            const displayOdds = Math.round((data['payoutodds'][i] + Number.EPSILON) * 10000) / 100;
            odds.textContent = `(${displayOdds}%)`;
            odds.classList.add("payout-odds");
            odds.style.borderRadius = "3px";
            odds.style.padding = "3px 2px";
            odds.style.backgroundColor='#6eff00';
            odds.style.color = 'BLACK';
            odds.style.fontSize = 'small';
            odds.style.fontWeight = "bold";
            payoutsElements[i].append(odds);

            if (payouts[i] >= 1){
                winrate += data['payoutodds'][i];
            }
        }

        const analytics = document.createElement("div");
        analytics.style.display = "flex";
        analytics.style.padding = "0px 5px";
        payoutArea.append(analytics);

        let ev = payoutArea.querySelector(".expected-value");
        if (ev) ev.remove();
        ev = document.createElement("div");
        const displayEV = Math.round((data['ev'] + Number.EPSILON) * 100) / 100;
        ev.textContent = `Expected Multiplier: ${displayEV}X`;
        ev.classList.add("expected-value");
        ev.style.padding = "10px"; 
        ev.style.border = 'medium solid BLACK';
        ev.style.borderRadius = "10px";
        ev.style.flex = 1;
        if (displayEV < 1) {
            ev.style.backgroundColor='#e43245';
            ev.style.color = '#f0f0f7';
        } else if (displayEV < 1.1) {
            ev.style.backgroundColor='#ffbb33';
            ev.style.color = 'BLACK';
        }
        else {
            ev.style.backgroundColor='#6eff00';
            ev.style.color = 'BLACK';
        }
        // console.log(data["payoutodds"]);
        analytics.append(ev);

        let wr = payoutArea.querySelector(".win-rate");
        if (wr) wr.remove();
        wr = document.createElement("div");
        const displayWR = Math.round((winrate + Number.EPSILON) * 10000) / 100;
        wr.textContent = `Break-Even Rate: ${displayWR}%`;
        wr.classList.add("win-rate");
        wr.style.padding = "10px"; 
        wr.style.border = 'medium solid BLACK';
        wr.style.borderRadius = "10px";
        wr.style.flex = 1;
        if (displayWR < 50) {
            wr.style.backgroundColor='#e43245';
            wr.style.color = '#f0f0f7';
        } else if (displayWR < 60) {
            wr.style.backgroundColor='#ffbb33';
            wr.style.color = 'BLACK';
        }
        else {
            wr.style.backgroundColor='#6eff00';
            wr.style.color = 'BLACK';
        }
        // console.log(data["payoutodds"]);
        analytics.append(wr);
    }).catch(err => {
        console.log(err)
    });
    prevParlay = parlay;
    prevPayouts = payouts;
})

// console.log("pickpocket active");
mutationObserver.observe(document.body, { childList: true, subtree: true })
