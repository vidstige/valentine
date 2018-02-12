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
                particles.push({
                    x: x, y: y, a: a,
                    rx: Math.random() - 0.5, ry: Math.random() - 0.5
                });
            }
        }
    }
    
    function f(t, duration, cutoff) {
        const rt = (t % duration) / duration;
        if (rt < cutoff) {
            return rt / cutoff;
        }
        return 0;
    }

    function animate(t) {
        const backbuffer = new ImageData(canvas.width, canvas.height);
        const cx = (backbuffer.width - img.width) / 2;
        const cy = (backbuffer.height - img.height) / 2;
        const duration = 4000;
        for (var i = 0; i < particles.length; i++) {
            const px = particles[i].x;
            const py = particles[i].y;
            const rx = particles[i].rx;
            const ry = particles[i].ry;
            const phase = -px * 10;
            const alpha = Math.PI * f(t + phase, duration, 0.3);
            const x = cx + px + Math.sin(alpha) * 180 * rx;
            const y = cy + py + Math.sin(alpha) * 400 * ry;
            const a = particles[i].a;
            const offset = 4 * (Math.trunc(x) + Math.trunc(y) * backbuffer.width);
            backbuffer.data[offset + 0] = 0xd3;
            backbuffer.data[offset + 1] = 0x17;
            backbuffer.data[offset + 2] = 0xe8;
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

