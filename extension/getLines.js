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

const mutationObserver = new MutationObserver(() => {
    // const picks = document.querySelectorAll('li#test-projection-li')
    // for (const pick of picks) {
    //     const name = pick.querySelector('h3').innerHTML;
    //     const line = pick.querySelector('.heading-md').children[0].innerHTML;
    //     const statType = pick.querySelector('.break-words').innerHTML;
    //     console.log(name+" "+line+" "+statType);
    // }
    // console.log("Picked:");
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
        console.log(name+" "+projection + " "+statType);
        parlay.push({"player": name, "line": projection, "statType": statType});
    }
    
    const hitCounts = [...selectedPayout.querySelectorAll("span.player-count")].map(element => element.innerHTML.split(" ")[0]);
    const payouts = [...selectedPayout.querySelectorAll("span.payout-multiplier")].map(element => element.innerHTML.split("X")[0]);
    console.log(hitCounts);
    console.log(payouts);
    payoutPairs = [];
    for (let i=0; i<hitCounts.length; i++) {
        payoutPairs.push({"numCorrect": parseInt(hitCounts[i]), "payoutMultiplier": parseFloat(payouts[i])});
    }
    const parlayJSON = {"parlay": parlay, "payouts": payoutPairs};
    console.log(parlayJSON);
    // send this JSON to a server for processing
    
    prevPicked = picked;
    prevPayout = selectedPayout;
})

console.log("pickpocket active");
mutationObserver.observe(document.body, { childList: true, subtree: true })
