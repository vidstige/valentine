require("../style.css");
const heart = require('../static/heart.png');

function start(image) {
    const canvas = document.getElementById("target");
    const ctx = canvas.getContext("2d");
    
    // Get image data
    ctx.drawImage(image, 0, 0);
    const img = ctx.getImageData(0, 0, 128, 128);
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // Convert to coordinates
    const particles = [];
    var c = 0;
    for (var y = 0; y < img.height; y++) {
        for (var x = 0; x < img.width; x++) {
            var r = img.data[c++];
            var g = img.data[c++];
            var b = img.data[c++];
            var a = img.data[c++];
            if (a > 0) {
                particles.push({x: x, y: y, a: a});
            }
        }
    }
    
    function animate(t) {
        const backbuffer = new ImageData(canvas.width, canvas.height);
        const cx = (backbuffer.width - img.width) / 2;
        const cy = (backbuffer.height - img.height) / 2;
        for (var i = 0; i < particles.length; i++) {
            const x = cx + particles[i].x;
            const y = cy + particles[i].y;
            const a = particles[i].a;
            const offset = 4 * (x + y * backbuffer.width);
            backbuffer.data[offset + 0] = 0;
            backbuffer.data[offset + 1] = 0;
            backbuffer.data[offset + 2] = 0;
            backbuffer.data[offset + 3] = a;
            
        }
        ctx.putImageData(backbuffer, 0, 0);
        requestAnimationFrame(animate);
    }
    requestAnimationFrame(animate);
}

function load() {
    const img = new Image();
    img.onload = function() { start(this); };
    img.src = heart;
}

document.addEventListener("DOMContentLoaded", load);

