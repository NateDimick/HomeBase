window.onload = () => {
    let numInput = document.getElementById("num-dice");
    numInput.addEventListener("change", (event) => {
        if (parseInt(numInput.value < 1)) {
            numInput.value = 1;
        }
    })
    let result = document.getElementById("roll-result");
    let rollers = Array.from(document.querySelectorAll(".roll"));
    rollers.forEach(r => {
        r.addEventListener("click", async () => {
            result.innerHTML = "--- <br> ---";
            let num = parseInt(r.firstElementChild.innerHTML);
            console.log(num);
            let url = `https://www.random.org/integers/?min=1&max=${num}&num=${numInput.value}&col=${numInput.value}&rnd=new&format=plain&base=10`;
            console.log(url);
            let resp = await fetch(url, {"mode": "cors"});
            //console.log(resp, resp.text());
            let respText = await resp.text();
            console.log(respText);
            respText = respText.trim().split("\t");
            console.log(respText);
            let sum = 0;
            respText.forEach(n => {
                sum += parseInt(n);
            })
            result.innerHTML = `${sum} <br> (${respText.join(', ')})`;
        });
    });
};