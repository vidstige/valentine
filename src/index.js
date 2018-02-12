require("../style.css");
const heart = require('../static/heart.png');

function main() {
    var c = document.getElementById("target");
    var ctx = c.getContext("2d");
    var img = new Image();
    img.onload = function() {
        ctx.drawImage(img, 0, 0);
    };
    img.src = heart;
}

document.addEventListener("DOMContentLoaded", function(event) { 
    main();
});

