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

function start(image, image2) {
    const canvas = document.getElementById("target");
    const ctx = canvas.getContext("2d");

    const foreground = color2obj(getComputedStyle(canvas).color);
    
    const particles = getParticles(ctx, image);
    for (var i = 0; i < particles.length; i++) {
        particles[i].rx = Math.random() - 0.5;
        particles[i].ry = Math.random() - 0.5;
    }
    const particles2 = getParticles(ctx, image2);
    console.log(particles.length, particles2.length);
    
    const mapping = getRandomMapping(particles.length, particles2.length);
    console.log(mapping);

    function f(t, duration, cutoff) {
        const rt = (t % duration) / duration;
        if (rt < cutoff) {
            return rt / cutoff;
        }
        return 0;
    }

    function animate(t) {
        const backbuffer = new ImageData(canvas.width, canvas.height);
        const cx = (backbuffer.width - image.width) / 2;
        const cy = (backbuffer.height - image.height) / 2;
        const duration = 4000;
        
        for (var i = 0; i < particles.length; i++) {
            const px = particles[i].x;
            const py = particles[i].y;
            const rx = particles[i].rx;
            const ry = particles[i].ry;
            const phase = -px * 10;

            const j = mapping[i];
            const px2 = particles2[j].x;
            const py2 = particles2[j].y;
            const k = (Math.sin(t / 1000) + 1)/2;
            const x = cx + lerp(px2, px, k);
            const y = cy + lerp(py2, py, k);
            const a = lerp(particles2[j].a, particles[i].a, k);

            const offset = 4 * (Math.trunc(x) + Math.trunc(y) * backbuffer.width);
            backbuffer.data[offset + 0] = foreground.r;
            backbuffer.data[offset + 1] = foreground.g;
            backbuffer.data[offset + 2] = foreground.b;
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

