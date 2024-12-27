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

statNameToAbbrev = {"Points" : "PTS", "Rebounds": "REB", "Assists": "AST", "Pts+Rebs+Asts": "PRA"}

const mutationObserver = new MutationObserver(() => {
    const picked = document.querySelectorAll('li.entry-prediction .player');
    const payoutArea = document.querySelector(".entry-predictions-game-type");
    if (!payoutArea) return;
    const selectedPayout = payoutArea.querySelector("button.selected");
    if (!selectedPayout) return;

    const parlay = [];
    if (arraysEqual(prevPicked, picked) && selectedPayout === prevPayout) return;
    for (const pick of picked) {
        const name = pick.querySelector('h3').innerHTML;
        const projection = pick.querySelector('.projected-score>.score').textContent;
        const statType = pick.querySelectorAll('.projected-score>div')[1].children[0].innerHTML;
        // console.log(name+" "+projection + " "+statType);

        leg_obj = {"player": name, "line": projection, "statType": statNameToAbbrev[statType]}

        if (!pick.querySelector(".hitrate-pickpocket")){
            const res =  fetch("http://127.0.0.1:5000/checkLine", {
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
                const proj = document.createElement("div");
                proj.textContent = `${Math.round((data["percentage"] + Number.EPSILON) * 100) / 100}% (${data["hit"]}/${data["games"]})`;
                proj.classList.add('selected', 'hitrate-pickpocket');
                pick.append(proj);
            });
        }
    }
    
    const hitCounts = [...selectedPayout.querySelectorAll("span.player-count")].map(element => element.textContent.split(" ")[0]);
    const payouts = [...selectedPayout.querySelectorAll("span.payout-multiplier")].map(element => element.textContent.split("X")[0]);
    // console.log(hitCounts);
    // console.log(payouts);
    payoutPairs = [];
    for (let i=0; i<hitCounts.length; i++) {
        payoutPairs.push({"numCorrect": parseInt(hitCounts[i]), "payoutMultiplier": parseFloat(payouts[i])});
    }
    hitRates =[]

    // TODO: USE PAYOUTS TO CALC EV
    
    prevPicked = picked;
    prevPayout = selectedPayout;
})

// console.log("pickpocket active");
mutationObserver.observe(document.body, { childList: true, subtree: true })
