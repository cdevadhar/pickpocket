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

const statNameToAbbrev = {"Points" : "PTS", "Rebounds": "REB", "Assists": "AST", "Blks+Stls": "BLK+STL", "Rebs+Asts": "REB+AST", "Pts+Asts": "PTS+AST", "Pts+Rebs": "PTS+REB", "Pts+Rebs+Asts": "PTS+REB+AST", "Blocked Shots": "BLK", "Steals": "STL", "Turnovers": "TOV", "Free Throws Made": "FTM", "FG Made": "FGM", "3-PT Made": "FG3M"}

const mutationObserver = new MutationObserver(() => {
    const picked = document.querySelectorAll('li.entry-prediction .player');
    const payoutArea = document.querySelector(".entry-predictions-game-type");
    if (!payoutArea) return;
    const selectedPayout = payoutArea.querySelector("button.selected");
    if (!selectedPayout) return;
    const payouts = [...selectedPayout.querySelectorAll("span.payout-multiplier")].map(element => parseFloat(element.textContent.split("X")[0]));
    if (payouts.length==0) {
        return;
    }
    const parlay = [];
    // console.log(selectedPayout);
    for (const pick of picked) {
        const name = pick.querySelector('h3').innerHTML;
        const projection = pick.querySelector('.projected-score>.score').textContent;
        const statType = pick.querySelectorAll('.projected-score>div')[1].children[0].innerHTML;
        const overUnderContainer = pick.parentElement.parentElement.querySelector(".over-under");
        const overUnder = overUnderContainer.querySelector("button.selected").textContent.toLowerCase();
        // console.log(name+" "+projection + " "+statType);
        const leg_obj = {"player": name, "line": projection, "statType": statNameToAbbrev[statType], "pick": overUnder}
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
        // console.log(data);
        const probs = data['probabilities'];
        for (let i=0; i<picked.length; i++) {
            const prob = probs[i];
            const existingProj = picked[i].querySelector(".hitrate-pickpocket");
            if (existingProj) existingProj.remove();
            const proj = document.createElement("div");
            proj.textContent = `${Math.round((prob["percentage"] + Number.EPSILON) * 100)}% (${prob["hit"]}/${prob["games"]})`;
            proj.classList.add('selected', 'hitrate-pickpocket');
            picked[i].append(proj);
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
            odds.style.fontWeight = "bold"
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
    })
    prevParlay = parlay;
    prevPayouts = payouts;
})

// console.log("pickpocket active");
mutationObserver.observe(document.body, { childList: true, subtree: true })
