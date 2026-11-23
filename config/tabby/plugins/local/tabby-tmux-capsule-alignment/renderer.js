'use strict';

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

function attachCapsuleAlignment(frontend) {
    const terminal = frontend?.xterm;
    const service = terminal?._core?._renderService;
    if (!service?.setRenderer) return null;
    let unpatchRenderer;

    function patchRenderer(renderer) {
        unpatchRenderer?.();
        unpatchRenderer = undefined;
        if (!renderer?.renderRows) return;
        const original = renderer.renderRows;
        const renderRows = function (first, last) {
            const draw = () => original.call(this, first, last);
            const row = terminal.rows - 1;
            const layer = this._renderLayers?.[0];
            const rectangles = this._rectangleRenderer?.value;
            const glyphs = this._glyphRenderer?.value;
            const canvas = last >= row && layer?._drawBackground && layer?._drawChars && layer?._ctx?.roundRect;
            const webgl = rectangles?._addRectangle && glyphs?.render &&
                glyphs._vertices?.attributes?.length === 11 * terminal.cols * terminal.rows;
            const dimensions = this.dimensions;
            if ((!canvas && !webgl) || !dimensions?.css?.cell?.height ||
                !(dimensions?.device?.cell?.height >= 4) || !(dimensions.device.cell.width >= 1)) return draw();
            const capsules = findCapsules(terminal, row);
            if (!capsules.length) return draw();
            if (canvas) return withCanvasCapsules(this, layer, row, capsules, draw);
            return withWebglCapsules(this, rectangles, glyphs, terminal, row, capsules, draw);
        };
        renderer.renderRows = renderRows;
        unpatchRenderer = () => {
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
            if (service.setRenderer === setAlignedRenderer) service.setRenderer = setRenderer;
        },
    };
}

module.exports = { attachCapsuleAlignment };
