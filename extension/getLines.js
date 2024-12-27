let prevPicked = [];
let prevPayout = null;
function arraysEqual(a, b) {
    if (a === b) return true;
    if (a == null || b == null) return false;
    if (a.length !== b.length) return false;
    for (var i = 0; i < a.length; ++i) {
        if (a[i] !== b[i]) return false;
    }
    return true;
}

const statNameToAbbrev = {"Points" : "PTS", "Rebounds": "REB", "Assists": "AST", "Pts+Rebs+Asts": "PRA"}

const mutationObserver = new MutationObserver(() => {
    const picked = document.querySelectorAll('li.entry-prediction .player');
    const payoutArea = document.querySelector(".entry-predictions-game-type");
    if (!payoutArea) return;
    const selectedPayout = payoutArea.querySelector("button.selected");
    if (!selectedPayout) return;

    const parlay = [];
    const hitOddsPromises = [];
    if (arraysEqual(prevPicked, picked) && selectedPayout === prevPayout) return;
    for (const pick of picked) {
        const name = pick.querySelector('h3').innerHTML;
        const projection = pick.querySelector('.projected-score>.score').textContent;
        const statType = pick.querySelectorAll('.projected-score>div')[1].children[0].innerHTML;
        // console.log(name+" "+projection + " "+statType);

        const leg_obj = {"player": name, "line": projection, "statType": statNameToAbbrev[statType]}

        const fetchProm =  fetch("http://127.0.0.1:5000/checkLine", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify(leg_obj)
        }).then(res =>{
            return res.json();
        }).then(data => {
            // console.log(data);
            parlay.push({...leg_obj, ...data});
            if (!pick.querySelector(".hitrate-pickpocket")){
                const proj = document.createElement("div");
                proj.textContent = `${Math.round((data["percentage"] + Number.EPSILON) * 100) / 100}% (${data["hit"]}/${data["games"]})`;
                proj.classList.add('selected', 'hitrate-pickpocket');
                pick.append(proj);
            }
            return data["percentage"]/100;
        }).catch(err => {console.log(err)});

        hitOddsPromises.push(fetchProm);
    }

    Promise.all(hitOddsPromises).then(hitOdds => {
        const hitCounts = [...selectedPayout.querySelectorAll("span.player-count")].map(element => element.textContent.split(" ")[0]);
        const payouts = [...selectedPayout.querySelectorAll("span.payout-multiplier")].map(element => element.textContent.split("X")[0]);
        // console.log(hitCounts);
        // console.log(payouts);
        // console.log(hitOdds);
        payoutPairs = [];
        for (let i=0; i<hitCounts.length; i++) {
            payoutPairs.push({"numCorrect": parseInt(hitCounts[i]), "payoutMultiplier": parseFloat(payouts[i])});
        }
        
        const x = Math.max(...hitCounts);
        const probForNumHits = [];
        for (let i = 0; i < x+1; i++){
            probForNumHits.push(0);
        }
        // console.log(probForNumHits)
        for (let i = 0; i < (2**x); i++) {
            let bitshit = i >>> 0; // convert to unsigned integer
            let hits = 0;
            let currentProb = 1;
            for (let j = 0; j < x; j++) {
                if (bitshit & 1) {
                    currentProb *= hitOdds[j];
                    hits++;
                }
                else {
                    currentProb *= (1-hitOdds[j])
                }
                bitshit >>>= 1
            }
            // console.log(currentProb)
            probForNumHits[hits] += currentProb;
        }
        // console.log(probForNumHits);
        
        prevPicked = picked;
        prevPayout = selectedPayout;
    })
})

// console.log("pickpocket active");
mutationObserver.observe(document.body, { childList: true, subtree: true })
