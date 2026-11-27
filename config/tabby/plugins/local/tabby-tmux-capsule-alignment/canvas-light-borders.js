'use strict';

const patchedAtlases = new WeakSet();
const lightBorders = new Set(Array.from('─│┌┐└┘├┤┬┴┼╭╮╰╯╴╵╶╷', glyph => glyph.charCodeAt(0)));

function patchCanvasLightBorders(atlas) {
    const context = atlas?._tmpCtx;
    const config = atlas?._config;
    if (typeof atlas?._drawToCache !== 'function' || !config || config.customGlyphs === false ||
        typeof context?.arcTo !== 'function' || patchedAtlases.has(atlas)) return;

    const drawToCache = atlas._drawToCache;
    atlas._drawToCache = function (character) {
        const code = typeof character === 'string' && character.length === 1 ?
            character.charCodeAt(0) : character;
        if (!lightBorders.has(code)) return drawToCache.apply(this, arguments);

        const { moveTo, lineTo, bezierCurveTo, stroke } = context;
        const width = Math.max(1, Math.round(config.devicePixelRatio));
        // A whole-pixel stroke needs an integer center when even and a half-pixel center when odd.
        const snap = width % 2 === 0 ? Math.floor : value => value;
        const radius = Math.min(
            Math.floor((config.deviceCellWidth - width) / 2),
            Math.floor((config.deviceCellHeight - width) / 2),
        ) - width;
        const restore = () => {
            context.moveTo = moveTo;
            context.lineTo = lineTo;
            context.bezierCurveTo = bezierCurveTo;
            context.stroke = stroke;
        };
        context.moveTo = function (x, y) {
            moveTo.call(this, snap(x), snap(y));
        };
        context.lineTo = function (x, y) {
            lineTo.call(this, snap(x), snap(y));
        };
        context.bezierCurveTo = function (firstX, firstY, turnX, turnY, endX, endY) {
            if (radius > 0 && firstX === turnX && turnY === endY) {
                // Leave a straight segment at each edge of the cell.
                this.arcTo(snap(turnX), snap(turnY), snap(endX), snap(endY), radius);
                lineTo.call(this, snap(endX), snap(endY));
            } else {
                bezierCurveTo.call(this, snap(firstX), snap(firstY), snap(turnX), snap(turnY), snap(endX), snap(endY));
            }
        };
        context.stroke = function () {
            restore();
            this.lineWidth = width;
            return stroke.apply(this, arguments);
        };
        try {
            return drawToCache.apply(this, arguments);
        } finally {
            restore();
        }
    };
    patchedAtlases.add(atlas);
    atlas.clearTexture?.();
}

module.exports = { patchCanvasLightBorders };
