'use strict';

const underlineFlag = 1 << 28;
const patchedAtlases = new WeakSet();

function patchCanvasUnderline(atlas) {
    if (typeof atlas?._drawToCache !== 'function' || patchedAtlases.has(atlas)) return;
    const { _tmpCtx: context, _workAttributeData: attributes } = atlas;
    if (!atlas._config || !context || typeof attributes?.getUnderlineVariantOffset !== 'function') return;

    const drawToCache = atlas._drawToCache;
    atlas._drawToCache = function (character, background, foreground, extended, restrictToCellHeight) {
        if (!restrictToCellHeight || !(foreground & underlineFlag)) {
            return drawToCache.apply(this, arguments);
        }

        const { deviceCellHeight, deviceCharHeight, fontSize, devicePixelRatio } = this._config;
        const thickness = Math.max(1, Math.floor(fontSize * devicePixelRatio / 15));
        const paddingBelowGlyph = Math.floor((deviceCellHeight - deviceCharHeight) / 2);
        // Undo xterm's upward offset and place the stroke inside the bottom of the cell.
        const shift = paddingBelowGlyph + 2 * thickness - Math.floor(thickness / 2);

        const { beginPath, moveTo, lineTo } = context;
        const { getUnderlineVariantOffset } = attributes;
        let drawingUnderline = false;
        context.beginPath = function () {
            drawingUnderline = false;
            return beginPath.call(this);
        };
        attributes.getUnderlineVariantOffset = function () {
            // xterm calls this after beginning the underline path and before drawing its strokes.
            drawingUnderline = this.extended.underlineStyle <= 1;
            return getUnderlineVariantOffset.call(this);
        };
        context.moveTo = function (x, y) {
            return moveTo.call(this, x, drawingUnderline ? y + shift : y);
        };
        context.lineTo = function (x, y) {
            return lineTo.call(this, x, drawingUnderline ? y + shift : y);
        };
        try {
            return drawToCache.apply(this, arguments);
        } finally {
            context.beginPath = beginPath;
            context.moveTo = moveTo;
            context.lineTo = lineTo;
            attributes.getUnderlineVariantOffset = getUnderlineVariantOffset;
        }
    };
    patchedAtlases.add(atlas);
    atlas.clearTexture?.();
}

module.exports = { patchCanvasUnderline };
