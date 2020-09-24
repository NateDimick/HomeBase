function ensureNumbers() {
    let nums = document.querySelectorAll(".number");
    let allGood = true;
    nums.forEach(n => {
        if (n.value === ''){
            allGood = false;
        }
    });
    if (!allGood) {
        document.getElementById('submit').disabled = true;
    } else {
        document.getElementById('submit').disabled = false;
    }
}
setInterval(ensureNumbers, 100);