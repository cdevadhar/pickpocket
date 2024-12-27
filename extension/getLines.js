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
        parlay.push(leg_obj);
    }

    const payouts = [...selectedPayout.querySelectorAll("span.payout-multiplier")].map(element => parseFloat(element.textContent.split("X")[0]));
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
            if (!picked[i].querySelector(".hitrate-pickpocket")){
                const proj = document.createElement("div");
                proj.textContent = `${Math.round((prob["percentage"] + Number.EPSILON) * 100)}% (${prob["hit"]}/${prob["games"]})`;
                proj.classList.add('selected', 'hitrate-pickpocket');
                picked[i].append(proj);
            }
        }
        let ev = payoutArea.querySelector(".expected-value");
        if (ev) ev.remove();
        ev = document.createElement("div");
        ev.textContent = `Expected Value: ${data['ev']}`
        ev.classList.add("expected-value");
        payoutArea.append(ev);
       
       
    })
    prevPicked = picked;
    prevPayout = selectedPayout;
})

// console.log("pickpocket active");
mutationObserver.observe(document.body, { childList: true, subtree: true })
