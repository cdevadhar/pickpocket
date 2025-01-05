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

const statNameToAbbrev = {"Points" : "PTS", "Rebounds": "REB", "Assists": "AST", "Blks+Stls": "BLK+STL", "Rebs+Asts": "REB+AST", "Pts+Asts": "PTS+AST", "Pts+Rebs": "PTS+REB", "Pts+Rebs+Asts": "PTS+REB+AST", "Blocked Shots": "BLK", "Steals": "STL", "Turnovers": "TOV", "Free Throws Made": "FTM", "FG Made": "FGM", "3-PT Made": "FG3M", "3-PT Attempted": "FG3A", "FT Attempted": "FTA", "FG Attempted": "FGA", "Offensive Rebounds": "OREB", "Defensive Rebounds": "DREB", "Fantasy Score": "FS"}

const mutationObserver = new MutationObserver(() => {
    const picked = document.querySelectorAll('li.entry-prediction .player');

    if (picked.length == 0) {
        prevParlay = []
        prevPayouts = []
        return;
    }

    const payoutArea = document.querySelector(".entry-predictions-game-type");

    const selectedPayout = payoutArea ? payoutArea.querySelector("button.selected") : null;
    
    const payouts = selectedPayout ? [...selectedPayout.querySelectorAll("span.payout-multiplier")].map(element => parseFloat(element.textContent.split("X")[0])) : [];

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

    prevParlay = parlay;
    prevPayouts = payouts;

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

        let ev = document.querySelector(".expected-value");
        if (ev) ev.remove();

        let wr = document.querySelector(".win-rate");
        if (wr) wr.remove();

        let worstEV = document.querySelector(".worst-expected-value");
        if (worstEV) worstEV.remove();

        let worstWR = document.querySelector(".worst-win-rate");
        if (worstWR) worstWR.remove();

        let midEV = document.querySelector(".mid-expected-value");
        if (midEV) midEV.remove();

        let midWR = document.querySelector(".mid-win-rate");
        if (midWR) midWR.remove();

        if (payouts.length == 0 || !selectedPayout) {
            return;
        }

        let payoutOdds = payoutArea.querySelectorAll(".payout-odds");
        for (const po of payoutOdds) {
            po.remove();
        }

        let winrate = 0;
        let worstWinRate = 0;
        let midWinRate = 0;
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
                if ("worstPayoutOdds" in data){
                    worstWinRate += data['worstPayoutOdds'][i];
                }
                if ("midPayoutOdds" in data){
                    midWinRate += data['midPayoutOdds'][i];
                }
            }
        }

        const analytics = document.createElement("div");
        analytics.style.display = "flex";
        analytics.style.padding = "0px 5px";
        payoutArea.append(analytics);

        ev = document.createElement("div");
        const displayEV = Math.round((data['ev'] + Number.EPSILON) * 100) / 100;
        ev.textContent = `Raw Expected Multiplier (EM): ${displayEV}X`;
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

        wr = document.createElement("div");
        const displayWR = Math.round((winrate + Number.EPSILON) * 10000) / 100;
        wr.textContent = `Raw Break-Even Rate (BER): ${displayWR}%`;
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

        if (!("worstEV" in data)) {
            return;
        }

        // console.log("HERE")
        // console.log(data)

        const midCaseAnalytics = document.createElement("div");
        midCaseAnalytics.style.display = "flex";
        midCaseAnalytics.style.padding = "0px 5px";
        payoutArea.append(midCaseAnalytics);

        midEV = document.createElement("div");
        const displayMidEV = Math.round((data['midEV'] + Number.EPSILON) * 100) / 100;
        midEV.textContent = `Moderately Adjusted EM: ${displayMidEV}X`;
        midEV.classList.add("mid-expected-value");
        midEV.style.padding = "10px"; 
        midEV.style.border = 'medium solid BLACK';
        midEV.style.borderRadius = "10px";
        midEV.style.flex = 1;
        if (displayMidEV < 1) {
            midEV.style.backgroundColor='#e43245';
            midEV.style.color = '#f0f0f7';
        } else if (displayMidEV < 1.1) {
            midEV.style.backgroundColor='#ffbb33';
            midEV.style.color = 'BLACK';
        }
        else {
            midEV.style.backgroundColor='#6eff00';
            midEV.style.color = 'BLACK';
        }
        // console.log(data["payoutodds"]);
        midCaseAnalytics.append(midEV);

        midWR = document.createElement("div");
        const displaymidWR = Math.round((midWinRate + Number.EPSILON) * 10000) / 100;
        midWR.textContent = `Moderately Adjusted BER: ${displaymidWR}%`;
        midWR.classList.add("mid-win-rate");
        midWR.style.padding = "10px"; 
        midWR.style.border = 'medium solid BLACK';
        midWR.style.borderRadius = "10px";
        midWR.style.flex = 1;
        if (displaymidWR < 50) {
            midWR.style.backgroundColor='#e43245';
            midWR.style.color = '#f0f0f7';
        } else if (displaymidWR < 60) {
            midWR.style.backgroundColor='#ffbb33';
            midWR.style.color = 'BLACK';
        }
        else {
            midWR.style.backgroundColor='#6eff00';
            midWR.style.color = 'BLACK';
        }
        // console.log(data["payoutodds"]);
        midCaseAnalytics.append(midWR);

        const worstCaseAnalytics = document.createElement("div");
        worstCaseAnalytics.style.display = "flex";
        worstCaseAnalytics.style.padding = "0px 5px";
        payoutArea.append(worstCaseAnalytics);

        worstEV = document.createElement("div");
        const displayWorstEV = Math.round((data['worstEV'] + Number.EPSILON) * 100) / 100;
        worstEV.textContent = `Worst-Case Adjusted EM: ${displayWorstEV}X`;
        worstEV.classList.add("worst-expected-value");
        worstEV.style.padding = "10px"; 
        worstEV.style.border = 'medium solid BLACK';
        worstEV.style.borderRadius = "10px";
        worstEV.style.flex = 1;
        if (displayWorstEV < 1) {
            worstEV.style.backgroundColor='#e43245';
            worstEV.style.color = '#f0f0f7';
        } else if (displayWorstEV < 1.1) {
            worstEV.style.backgroundColor='#ffbb33';
            worstEV.style.color = 'BLACK';
        }
        else {
            worstEV.style.backgroundColor='#6eff00';
            worstEV.style.color = 'BLACK';
        }
        // console.log(data["payoutodds"]);
        worstCaseAnalytics.append(worstEV);

        worstWR = document.createElement("div");
        const displayWorstWR = Math.round((worstWinRate + Number.EPSILON) * 10000) / 100;
        worstWR.textContent = `Worst-Case Adjusted BER: ${displayWorstWR}%`;
        worstWR.classList.add("worst-win-rate");
        worstWR.style.padding = "10px"; 
        worstWR.style.border = 'medium solid BLACK';
        worstWR.style.borderRadius = "10px";
        worstWR.style.flex = 1;
        if (displayWorstWR < 50) {
            worstWR.style.backgroundColor='#e43245';
            worstWR.style.color = '#f0f0f7';
        } else if (displayWorstWR < 60) {
            worstWR.style.backgroundColor='#ffbb33';
            worstWR.style.color = 'BLACK';
        }
        else {
            worstWR.style.backgroundColor='#6eff00';
            worstWR.style.color = 'BLACK';
        }
        // console.log(data["payoutodds"]);
        worstCaseAnalytics.append(worstWR);

    }).catch(err => {
        console.log(err)
    });
})

// console.log("pickpocket active");
mutationObserver.observe(document.body, { childList: true, subtree: true })
