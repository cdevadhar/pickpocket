const mutationObserver = new MutationObserver(() => {
    const picks = document.querySelectorAll('li#test-projection-li')
    for (const pick of picks) {
        const name = pick.querySelector('h3').innerHTML;
        const line = pick.querySelector('.heading-md').children[0].innerHTML;
        const statType = pick.querySelector('.break-words').innerHTML;
        console.log(name+" "+line+" "+statType);
    }

    console.log("Picked:");
    const picked = document.querySelectorAll('li.entry-prediction .player')
    for (const pick of picked) {
        const name = pick.querySelector('h3').innerHTML;
        const projection = pick.querySelector('.projected-score>.score').textContent;
        const statType = pick.querySelectorAll('.projected-score>div')[1].innerHTML;
        console.log(name+" "+projection + " "+statType);
    }
})

console.log("pickpocket active");
mutationObserver.observe(document.body, { childList: true, subtree: true })
