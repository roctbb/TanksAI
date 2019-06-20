var ctx, canvas;
var width = 1200;
var height = 720;
var textures = {};
var tileSize = 40;
var fetchTimeoutId = undefined;
var animationFrames = 15;
var $$ = {
    original_map: undefined,
    map: undefined,
    players: undefined,
    animationIntervalId: undefined,
    tick: 0
};

function equalNames(name1, name2) {
    if (typeof name1 !== "string") return false;
    if (typeof name2 !== "string") return false;
    if (name1 === name2) return true;
    if (name1 === name2.split('(')[0]) return true;  // Some bicycles
    return false;
}

function estimateMovement(map, x, y) {
    var p = map[x][y];
    var name = p.name;
    if (name in $$.players) {
        var suffix = 1;
        while ((name + '(' + suffix.toString() + ')') in $$.players) suffix++;
        name = name + '(' + suffix.toString() + ')';
    }
    var action = 'stay';
    if ($$.original_map !== undefined) {
        if (x > 0 && equalNames(p.name, $$.original_map[x - 1][y].name)) {
            action = 'go_right';
        } else if (x < map.length - 1 && equalNames(name, $$.original_map[x + 1][y].name)) {
            action = 'go_left';
        } else if (y > 0 && equalNames(p.name, $$.original_map[x][y - 1].name)) {
            action = 'go_down';
        } else if (y < map[x].length - 1 && equalNames(name, $$.original_map[x][y + 1].name)) {
            action = 'go_up';
        }
    }
    $$.players[name] = {
        x: x, y: y, life: p['life'], hit: p['hit'], action: action
    }
}

function checkDifference(map) {
    if ($$.original_map === undefined) return true;
    for (var x = 0; x < map.length; x++) {
        for (var y = 0; y < map[x].length; y++) {
            if (map[x][y] === $$.original_map[x][y]) continue;
            if (typeof map[x][y] === "string" || typeof $$.original_map[x][y] === "string") return true;
            if (!equalNames(map[x][y].name, $$.original_map[x][y].name)) return true;
            if (map[x][y].life !== $$.original_map[x][y].life) return true;
        }
    }
    return false;
}

function preprocessing(map) {
    if (width !== window.innerWidth || height !== window.innerHeight) {
        width = window.innerWidth;
        height = window.innerHeight;
        if (18.0 / 30 * width < height) {
            // fit horizontal
            canvas.height = width * 18.0 / 30;
            canvas.width = width;
        } else {
            // fit vertical
            canvas.height = height;
            canvas.width = height * 30 / 18.0;
        }
        tileSize = canvas.width / 30.0;
        ctx.font = (tileSize / 3.8).toString() + "px Arial";
    }

    $$.map = [];
    $$.players = {};
    for (var x = 0; x < map.length; x++) {
        var map_row = [];
        for (var y = 0; y < map[x].length; y++) {
            var map_cell = [];
            if (map[x][y] !== '@' && $$.original_map !== undefined && $$.original_map[x][y] === '@') {  // Someone picked up the coin
                map_cell.push('@');
            }
            switch (map[x][y]) {
                case '#':
                    map_cell.push('#');
                    break;
                case '@':
                    map_cell.push('@');
                    if ((x > 0 && (map[x - 1][y] === '&larr;' || map[x - 1][y] === '&rarr;')) ||
                        (x < map.length - 1 && (map[x + 1][y] === '&larr;' || map[x + 1][y] === '&rarr;'))) {
                        map_cell.push('-');
                    }
                    if ((y > 0 && (map[x][y - 1] === '&uarr;' || map[x][y - 1] === '&darr;')) ||
                        (y < map[0].length - 1 && (map[x][y + 1] === '&uarr;' || map[x][y + 1] === '&darr;'))) {
                        map_cell.push('|');
                    }
                    break;
                case '&larr;':
                case '&rarr;':
                    map_cell.push('-');
                    if ((y > 0 && (map[x][y - 1] === '&uarr;' || map[x][y - 1] === '&darr;')) ||
                        (y < map[0].length - 1 && (map[x][y + 1] === '&uarr;' || map[x][y + 1] === '&darr;'))) {
                        map_cell.push('|');
                    }
                    break;
                case '&uarr;':
                case '&darr;':
                    map_cell.push('|');
                    if ((x > 0 && (map[x - 1][y] === '&larr;' || map[x - 1][y] === '&rarr;')) ||
                        (x < map.length - 1 && (map[x + 1][y] === '&larr;' || map[x + 1][y] === '&rarr;'))) {
                        map_cell.push('-');
                    }
                    break;
                case '.':
                    break;
                default:
                    estimateMovement(map, x, y);
                    map_cell.push('*');
            }
            map_row.push(map_cell);
        }
        $$.map.push(map_row);
    }
    ctx.save();
    $$.original_map = map;
}

function animate() {
    ctx.clearRect(0, 0, width, height);
    for (var x = 0; x < $$.map.length; x++) {
        for (var y = 0; y < $$.map[x].length; y++) {
            for (var k = 0; k < $$.map[x][y].length; k++) {
                switch($$.map[x][y][k]) {
                    case '#':
                        ctx.drawImage(textures['brick'], x * tileSize, y * tileSize, tileSize, tileSize);
                        break;
                    case '@':
                        ctx.drawImage(textures['coin'], x * tileSize, y * tileSize, tileSize, tileSize);
                        break;
                    case '-':
                        ctx.globalAlpha = 1 - $$.tick / animationFrames;
                        ctx.drawImage(textures['horiz'], x * tileSize, y * tileSize, tileSize, tileSize);
                        ctx.globalAlpha = 1.0;
                        break;
                    case '|':
                        ctx.globalAlpha = 1 - $$.tick / animationFrames;
                        ctx.drawImage(textures['verti'], x * tileSize, y * tileSize, tileSize, tileSize);
                        ctx.globalAlpha = 1.0;
                        break;
                }
            }
        }
    }

    for (var name in $$.players) {
        if (!$$.players.hasOwnProperty(name)) continue;
        var p = $$.players[name];
        var baseX = p.x;
        var baseY = p.y;
        switch (p.action) {
            case 'go_left':
                baseX += $$.tick / animationFrames;
                break;
            case 'go_right':
                baseX -= $$.tick / animationFrames;
                break;
            case 'go_up':
                baseY += $$.tick / animationFrames;
                break;
            case 'go_down':
                baseY -= $$.tick / animationFrames;
                break;
        }
        ctx.drawImage(textures['player'], baseX * tileSize, baseY * tileSize, tileSize, tileSize);
        ctx.fillStyle = '#ffffff';
        var w_name = ctx.measureText(name).width;
        var w_life = ctx.measureText(p.life.toString()).width;
        ctx.fillText(name, (baseX + 0.5) * tileSize - w_name / 2, (baseY + 0.3) * tileSize);
        if (p.hit === 1) ctx.fillStyle = '#ff0000';
        ctx.fillText(p.life.toString(), (baseX + 0.5) * tileSize - w_life / 2, (baseY + 0.6) * tileSize);
    }
    $$.tick--;
    if ($$.tick < 0) clearInterval($$.animationIntervalId);
}

function fetchState() {
    var xhr = new XMLHttpRequest();
    xhr.open('GET', '/state', true);
    xhr.send();
    xhr.onreadystatechange = function() {
        if (xhr.readyState !== 4) return;
        var changed = false;
        if (xhr.status === 200) {
            var map = JSON.parse(xhr.responseText);
            if (checkDifference(map)) {
                changed = true;
                preprocessing(map);
                $$.tick = animationFrames;
                $$.animationIntervalId = setInterval(animate, 800 / animationFrames);
            }
        }
        fetchTimeoutId = setTimeout(fetchState, changed ? 900 : 200);
    }
}

function loadTextures() {
    var files = ["player", "grass", "brick", "coin", "horiz", "verti"];
    for (var i = 0; i < files.length; i++) {
        textures[files[i]] = new Image();
        textures[files[i]].src = '/static/res/' + files[i] + '.png';
    }
}

loadTextures();

window.addEventListener('load', function(){
    canvas = document.getElementById('canvas');
    canvas.width = width;
    canvas.height = height;
    ctx = canvas.getContext('2d');
    fetchTimeoutId = setTimeout(fetchState, 600);
});
