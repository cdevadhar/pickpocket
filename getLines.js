
let prevPicks = [];
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
    const picks = document.querySelectorAll(".entry-prediction")
    if (picks.length==0) return;
    if (arraysEqual(picks, prevPicks)) return;
    let parlay = [];
    for (const pick of picks) {
        const player = pick.querySelector("h3").innerHTML;
        let line = pick.querySelector(".score").children[0];
        if (line.children) line = line.children[0];
        line = line.innerHTML;
        const statType = pick.querySelector(".break-words").innerHTML;
        console.log(player+" "+line+" "+statType);
        parlay.append({"Player": player, "Line": line, "Stat Type": statType});
    }
    const parlayJSON = {"parlay": parlay, "payout": "TODO"};
    // send json to server
    prevPicks = picks;
})

console.log("pickpocket active");
mutationObserver.observe(document.body, { childList: true, subtree: true })

function gradeParlay() {
}