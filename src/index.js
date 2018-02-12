require("../style.css");
const heart = require('../static/heart.png');

function start(img) {
    const c = document.getElementById("target");
    const ctx = c.getContext("2d");
    ctx.drawImage(img, 0, 0);
}

function load() {
    const img = new Image();
    img.onload = function() { start(this); };
    img.src = heart;
}

document.addEventListener("DOMContentLoaded", load);

