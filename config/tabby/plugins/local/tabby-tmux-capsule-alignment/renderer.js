'use strict';

const { patchCanvasLightBorders } = require('./canvas-light-borders');
const { patchCanvasUnderline } = require('./canvas-underline');
const { findStatuses, withCanvasStatuses } = require('./canvas-status');
const { attachPaneBorders, withCanvasPaneBorders } = require('./canvas-pane-borders');

const leftCap = '\ue0b6';
const rightCap = '\ue0b4';
const barBackground = 0x171b16;
const sessionBackground = 0xb1e969;
const windowBackground = 0x293322;
const roundedSessionBackground = 0x232b20;
const roundedWindowBackground = 0x252e20;
const sessionColors = new Set([sessionBackground, roundedSessionBackground]);
const windowColors = new Set([windowBackground, roundedWindowBackground]);

function findCapsules(terminal, row) {
    if (terminal.hasSelection()) return [];
    const buffer = terminal.buffer.active;
    if (buffer.viewportY !== buffer.baseY) return [];
    const line = buffer.getLine(buffer.viewportY + row);
    const cell = buffer.getNullCell();
    if (line?.getCell(0, cell)?.getChars() !== leftCap) return [];
    if (!cell.isFgRGB() || !sessionColors.has(cell.getFgColor())) return [];

    const capsules = [];
    let start = -1;
    let color;
    for (let column = 0; column < terminal.cols; column++) {
        if (!line.getCell(column, cell)) break;
        const bg = cell.isBgRGB() ? cell.getBgColor() : -1;
        if (start >= 0 && bg === color) continue;
        if (bg === barBackground && cell.isFgRGB()) {
            const fg = cell.getFgColor();
            const char = cell.getChars();
            if (start >= 0 && column > start + 1 && char === rightCap && fg === color) {
                capsules.push({ start, end: column, color });
                if (windowColors.has(color)) break;
            }
            if (char === leftCap && (sessionColors.has(fg) || windowColors.has(fg))) {
                start = column;
                color = fg;
                continue;
            }
        }
        start = -1;
    }
    return capsules;
}

function geometry(dimensions, row, capsules) {
    const { width, height } = dimensions.device.cell;
    const scale = height / dimensions.css.cell.height;
    return capsules.map(({ start, end, color }) => {
        const x = start * width;
        const y = row * height;
        const boxWidth = (end - start + 1) * width;
        const rounded = color === roundedSessionBackground || color === roundedWindowBackground;
        const padding = Math.round(2 * scale);
        const inset = rounded ? Math.min(padding, Math.floor((height - 3) / 2)) :
            Math.min(Math.max(2, padding), height - 2);
        const fillHeight = rounded ? height - 2 * inset : height - inset;
        const radius = rounded ? Math.min(Math.round(4 * scale), fillHeight / 2, boxWidth / 2) :
            Math.min(width, fillHeight / 2);
        return { x, y, width: boxWidth, height, inset, fillHeight, radius, color };
    });
}

function cssColor(color) {
    return '#' + color.toString(16).padStart(6, '0');
}

function withCanvasCapsules(renderer, layer, row, capsules, draw) {
    const drawBackground = layer._drawBackground;
    const drawChars = layer._drawChars;
    layer._drawBackground = function (first, last) {
        drawBackground.call(this, first, last);
        const context = this._ctx;
        context.save();
        for (const box of geometry(renderer.dimensions, row, capsules)) {
            context.fillStyle = cssColor(barBackground);
            context.fillRect(box.x, box.y, box.width, box.height);
            context.fillStyle = cssColor(box.color);
            context.beginPath();
            context.roundRect(box.x, box.y + box.inset, box.width, box.fillHeight, box.radius);
            context.fill();
        }
        context.restore();
    };
    layer._drawChars = function (cell, column, line) {
        if (line === row && capsules.some(capsule => column === capsule.start || column === capsule.end)) return;
        drawChars.call(this, cell, column, line);
    };
    try {
        return draw();
    } finally {
        layer._drawBackground = drawBackground;
        layer._drawChars = drawChars;
    }
}

function withWebglCapsules(renderer, rectangles, glyphs, terminal, row, capsules, draw) {
    const renderBackgrounds = rectangles.renderBackgrounds;
    const renderGlyphs = glyphs.render;
    rectangles.renderBackgrounds = function () {
        const vertices = this._vertices;
        const originalCount = vertices.count;
        const boxes = geometry(renderer.dimensions, row, capsules);
        const addedCount = boxes.reduce((count, box) => count + 1 + 3 * box.fillHeight, 0);
        const capacity = (originalCount + addedCount) * 8;
        if (vertices.attributes.length < capacity) {
            const grown = new Float32Array(capacity);
            grown.set(vertices.attributes);
            vertices.attributes = grown;
        }

        const rectangle = (x, y, width, height, rgb, alpha = 1) => {
            if (width <= 0 || alpha <= 0) return;
            this._addRectangle(vertices.attributes, 8 * vertices.count++, x, y, width, height,
                (rgb >> 16) / 255, (rgb >> 8 & 255) / 255, (rgb & 255) / 255, alpha);
        };
        for (const box of boxes) {
            rectangle(box.x, box.y, box.width, box.height, barBackground);
            for (let y = 0; y < box.fillHeight; y++) {
                const dy = Math.max(0, box.radius - y - 0.5, y + 0.5 - (box.fillHeight - box.radius));
                const edge = box.radius - Math.sqrt(Math.max(0, box.radius ** 2 - dy ** 2));
                const whole = Math.ceil(edge);
                const alpha = whole - edge;
                const lineY = box.y + box.inset + y;
                rectangle(box.x + whole, lineY, box.width - 2 * whole, 1, box.color);
                rectangle(box.x + whole - 1, lineY, 1, 1, box.color, alpha);
                rectangle(box.x + box.width - whole, lineY, 1, 1, box.color, alpha);
            }
        }
        try {
            return renderBackgrounds.call(this);
        } finally {
            vertices.count = originalCount;
        }
    };
    glyphs.render = function (model) {
        const attributes = this._vertices.attributes;
        const saved = [];
        for (const { start, end } of capsules) {
            for (const column of [start, end]) {
                // The WebGL glyph instance stores width at offset 2 of 11 floats.
                const index = 11 * (row * terminal.cols + column) + 2;
                saved.push([index, attributes[index]]);
                attributes[index] = 0;
            }
        }
        try {
            return renderGlyphs.call(this, model);
        } finally {
            for (const [index, width] of saved) attributes[index] = width;
        }
    };
    try {
        return draw();
    } finally {
        rectangles.renderBackgrounds = renderBackgrounds;
        glyphs.render = renderGlyphs;
    }
}

function isOuterFrame(columns, edge) {
    let found = false;
    for (const frame of columns?.values() ?? []) {
        if (frame.floating) continue;
        if (frame.edges[1 - edge]) return false;
        found ||= Boolean(frame.edges[edge]);
    }
    return found;
}

function prepareTopTitleCanvas(layer, dimensions, headroom, existing) {
    const source = layer._ctx.canvas;
    const parent = source.parentElement;
    if (!parent) return undefined;
    const canvas = existing ?? parent.ownerDocument.createElement('canvas');
    const scale = dimensions.device.cell.height / dimensions.css.cell.height;
    const height = dimensions.device.cell.height + headroom;
    if (canvas.width !== source.width) canvas.width = source.width;
    if (canvas.height !== height) canvas.height = height;
    canvas.className = 'kael-pane-title-layer';
    canvas.style.position = 'absolute';
    canvas.style.pointerEvents = 'none';
    canvas.style.top = `-${headroom / scale}px`;
    canvas.style.width = `${dimensions.css.canvas.width}px`;
    canvas.style.height = `${height / scale}px`;
    if (canvas.parentElement !== parent) parent.appendChild(canvas);
    canvas.getContext('2d').clearRect(0, 0, source.width, height);
    return canvas;
}

function raiseStatusRow(layer, dimensions, row, shift) {
    const context = layer._ctx;
    const { width, height } = context.canvas;
    const top = row * dimensions.device.cell.height;
    const rowHeight = height - top;
    if (rowHeight <= shift) return;

    context.save();
    context.beginPath();
    context.rect(0, top - shift, width, rowHeight);
    context.clip();
    context.globalCompositeOperation = 'copy';
    context.drawImage(context.canvas, 0, top, width, rowHeight, 0, top - shift, width, rowHeight);
    context.restore();

    if (layer._alpha) {
        context.clearRect(0, height - shift, width, shift);
    } else {
        context.save();
        context.fillStyle = layer._themeService.colors.background.css;
        context.fillRect(0, height - shift, width, shift);
        context.restore();
    }
}

function patchCanvasCursor(renderer) {
    const layer = renderer._renderLayers?.find(layer => typeof layer._clearCursor === 'function');
    if (typeof layer?._clearAll !== 'function') return;

    const clearCursor = layer._clearCursor;
    const clear = function () {
        // A cursor on the trailing half of a wide glyph can paint pixels even
        // though xterm records a cell width of zero and clears an empty rectangle.
        if (this._state?.width === 0 && this._state.style) this._clearAll();
        return clearCursor.call(this);
    };
    // Clear any marks left before the decorator attached, then reset cursor state.
    layer._clearAll();
    layer._clearCursor();
    layer._clearCursor = clear;
    return () => {
        if (layer._clearCursor === clear) layer._clearCursor = clearCursor;
    };
}

function attachCapsuleAlignment(frontend) {
    const terminal = frontend?.xterm;
    const service = terminal?._core?._renderService;
    if (!service?.setRenderer) return null;
    const paneBorders = attachPaneBorders(terminal);
    const mouse = terminal._core._mouseService;
    const reportMouse = mouse?.getMouseReportCoords;
    let shiftedFooter;
    let unpatchRenderer;

    const reportShiftedMouse = function (...args) {
        const position = reportMouse.apply(this, args);
        if (!position || !shiftedFooter || position.row !== shiftedFooter.row - 1 ||
            position.y < shiftedFooter.start) return position;
        return { ...position, row: shiftedFooter.row, y: position.y + shiftedFooter.shift };
    };
    if (reportMouse) mouse.getMouseReportCoords = reportShiftedMouse;

    function patchRenderer(renderer) {
        unpatchRenderer?.();
        unpatchRenderer = undefined;
        shiftedFooter = undefined;
        terminal.element?.classList.remove('kael-compact-frames');
        if (!renderer?.renderRows) return;
        const unpatchCursor = patchCanvasCursor(renderer);
        const original = renderer.renderRows;
        let topTitleCanvas;
        const renderRows = function (first, last) {
            const drawNative = () => original.call(this, first, last);
            const row = terminal.rows - 1;
            const layer = this._renderLayers?.[0];
            patchCanvasLightBorders(layer?._charAtlas);
            patchCanvasUnderline(layer?._charAtlas);
            const rectangles = this._rectangleRenderer?.value;
            const glyphs = this._glyphRenderer?.value;
            const canvas = layer?._drawBackground && layer?._drawChars && layer?._ctx?.roundRect;
            const webgl = rectangles?._addRectangle && glyphs?.render &&
                glyphs._vertices?.attributes?.length === 11 * terminal.cols * terminal.rows;
            const dimensions = this.dimensions;
            if ((!canvas && !webgl) || !dimensions?.css?.cell?.height ||
                !(dimensions?.device?.cell?.height >= 4) || !(dimensions.device.cell.width >= 1)) return drawNative();
            let frames = canvas ? paneBorders?.visibleFrames(first, last) : undefined;
            let statuses;
            let topShift = 0;
            let topHeadroom = 0;
            let footerShift = 0;
            if (canvas && layer._getFont) {
                statuses = findStatuses(terminal, first, last);
                const height = dimensions.device.cell.height;
                const scale = height / dimensions.css.cell.height;
                if (first === 0) {
                    const outerTop = isOuterFrame(frames?.get(0), 1);
                    const buffer = terminal.buffer.active;
                    if (buffer.viewportY === buffer.baseY) {
                        terminal.element?.classList.toggle('kael-compact-frames', outerTop);
                    }
                    const charTop = layer._deviceCharTop ?? 0;
                    if (outerTop) {
                        topShift = Math.min(Math.round(10 * scale), Math.floor(height / 2), charTop + Math.round(6 * scale));
                        topHeadroom = Math.max(0, topShift - charTop);
                    }
                    if (topHeadroom) {
                        topTitleCanvas = prepareTopTitleCanvas(layer, dimensions, topHeadroom, topTitleCanvas);
                        if (!topTitleCanvas) topShift = charTop;
                    } else {
                        topTitleCanvas?.remove();
                        topTitleCanvas = undefined;
                    }
                }
                if (frames && row > 0 && last >= row - 1) {
                    const status = statuses.get(row) ?? findStatuses(terminal, row, row).get(row);
                    const border = frames.get(row - 1) ?? paneBorders.visibleFrames(row - 1, row - 1).get(row - 1);
                    if (reportMouse && status?.alignToPane && isOuterFrame(border, 0)) {
                        footerShift = Math.min(Math.round(7 * scale), Math.floor(height / 3));
                    }
                    if (shiftedFooter || footerShift) {
                        // The footer overlaps the preceding row. Repaint both when either changes.
                        first = Math.min(first, row - 1);
                        last = row;
                        frames = paneBorders.visibleFrames(first, last);
                        statuses = findStatuses(terminal, first, last);
                    }
                    shiftedFooter = undefined;
                }
            }
            const title = { shift: topShift, headroom: topHeadroom, canvas: topTitleCanvas };
            const draw = frames ? () => withCanvasPaneBorders(layer, dimensions, frames, title, drawNative) : drawNative;
            if (statuses?.size) {
                const result = withCanvasStatuses(this, layer, statuses, draw);
                if (footerShift) {
                    raiseStatusRow(layer, dimensions, row, footerShift);
                    const shift = Math.round(footerShift * dimensions.css.cell.height / dimensions.device.cell.height);
                    shiftedFooter = { row, shift, start: Math.ceil(row * dimensions.css.cell.height - shift) };
                }
                return result;
            }
            if (last < row) return draw();
            const capsules = findCapsules(terminal, row);
            if (!capsules.length) return draw();
            if (canvas) return withCanvasCapsules(this, layer, row, capsules, draw);
            return withWebglCapsules(this, rectangles, glyphs, terminal, row, capsules, draw);
        };
        renderer.renderRows = renderRows;
        unpatchRenderer = () => {
            unpatchCursor?.();
            topTitleCanvas?.remove();
            if (renderer.renderRows === renderRows) renderer.renderRows = original;
        };
    }

    const setRenderer = service.setRenderer;
    const setAlignedRenderer = function (renderer) {
        patchRenderer(renderer);
        return setRenderer.call(this, renderer);
    };
    service.setRenderer = setAlignedRenderer;
    patchRenderer(service._renderer?.value);
    terminal.refresh(0, terminal.rows - 1);
    return {
        dispose() {
            unpatchRenderer?.();
            paneBorders?.dispose();
            terminal.element?.classList.remove('kael-compact-frames');
            if (mouse?.getMouseReportCoords === reportShiftedMouse) mouse.getMouseReportCoords = reportMouse;
            if (service.setRenderer === setAlignedRenderer) service.setRenderer = setRenderer;
        },
    };
}

module.exports = { attachCapsuleAlignment };
