require("../style.css");
const heart = require('../static/heart.png');
const volumental = require('../static/volumental.png');

function color2obj(color) {
    const rgb = color.match(/\d+/g);
    return {r: rgb[0], g: rgb[1], b: rgb[2]};
}

function getParticles(ctx, image) {
    // Get image data
    ctx.drawImage(image, 0, 0);
    const img = ctx.getImageData(0, 0, image.width, image.height);
    ctx.clearRect(0, 0, image.width, image.height);

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
    return particles;
}

function getRandomInt(max) {
    return Math.floor(Math.random() * Math.floor(max));
}

// Returns an array of size a, that contains all
// indices 0..b-1 in random order. Some indices may
// appear more than once if a>b
function getRandomMapping(a, b) {
    if (b > a) {
        return null;
    }
    var taken = new Set();
    var m = [];
    for (var i = 0; i < a; i++) {
        var s = getRandomInt(b);
        while (i < b && taken.has(s)) {
            s = getRandomInt(b);
        }
        m[i] = s
        taken.add(s);
    }
    return m;
}

function lerp(a, b, t) {
    return a * t + b * (1-t);
}

function start(image1, image2) {
    const canvas = document.getElementById("target");
    const ctx = canvas.getContext("2d");

    const foreground = color2obj(getComputedStyle(canvas).color);
    const white = {r: 255, g: 255, b: 255};
    const hilite = {
        r: lerp(foreground.r, white.r, 0.6),
        g: lerp(foreground.g, white.r, 0.6),
        b: lerp(foreground.b, white.r, 0.6),
    };

    const p1 = getParticles(ctx, image1);
    const p2 = getParticles(ctx, image2);
   
    const mapping = getRandomMapping(p1.length, p2.length);

    function f(t) {
        const cutoff = 0.4;
        if (t < cutoff) {
            return 0;
        }
        if (t > 1.0 - cutoff) {
            return 1;
        }
        return (t - cutoff) / (1.0 - 2 * cutoff);
    }
    function reverse(t) {
        if (t < 0.5) {
            return t * 2;
        }
        return 1 - ((t - 0.5) * 2);
    }

    function animate(t) {
        const backbuffer = new ImageData(canvas.width, canvas.height);
        const cx1 = (backbuffer.width - image1.width) / 2;
        const cy1 = (backbuffer.height - image1.height) / 2;
        const cx2 = (backbuffer.width - image2.width) / 2;
        const cy2 = (backbuffer.height - image2.height) / 2;

        const duration = 5000;
        
        for (var i = 0; i < p1.length; i++) {
            const j = mapping[i];
            const phase = -p1[i].x / 800;
            //const phase = 0;
            const rt = ((t + phase) % duration) / duration;
            //const k = (Math.cos(2 * Math.PI * f(t + phase, duration, 0.2)) + 1) / 2;
            const k = f(reverse(rt + phase));
            const x = lerp(cx2+p2[j].x, cx1+p1[i].x, k);
            const y = lerp(cy2+p2[j].y, cy1+p1[i].y, k);
            const a = lerp(p2[j].a, p1[i].a, k);
            const k2 = 1.0 - (Math.cos(2* Math.PI * k) + 1) / 2;

            const offset = 4 * (Math.trunc(x) + Math.trunc(y) * backbuffer.width);
            backbuffer.data[offset + 0] = lerp(hilite.r, foreground.r, k2);
            backbuffer.data[offset + 1] = lerp(hilite.g, foreground.g, k2);
            backbuffer.data[offset + 2] = lerp(hilite.b, foreground.b, k2);
            backbuffer.data[offset + 3] = a;
        }
        ctx.putImageData(backbuffer, 0, 0);
        requestAnimationFrame(animate);
    }
    requestAnimationFrame(animate);
}

function load() {
    const images = [heart, volumental];
    var done = [];
    for (var i = 0; i < images.length; i++) {
        const img = new Image();
        img.onload = function() {
            done.push(this);
            if (done.length == images.length) {
                console.log("all loaded");
                start.apply(null, done);
            }            
        };
        img.src = images[i];
    }
}

document.addEventListener("DOMContentLoaded", load);

