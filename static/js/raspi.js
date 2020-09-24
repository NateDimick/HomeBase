async function statusUpdate() {
    let resp = await fetch("/raspi/update");
    let respJSON = await resp.json();
    Object.keys(respJSON).forEach(key => {
        try {
            document.getElementById(key).innerHTML = `${key.split('_')}: ${respJSON[key]}`;
        } catch (error) {
            let newP = document.createElement("p");
            newP.setAttribute("id", key);
            newP.innerHTML = `${key.split('_').join(' ')}: ${respJSON[key]}`;
            document.getElementById("container").appendChild(newP);
        }
    })
}
window.onload = () => {
    setInterval( statusUpdate, 2000);
}