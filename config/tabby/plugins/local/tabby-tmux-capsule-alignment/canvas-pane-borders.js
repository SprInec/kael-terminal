'use strict';

const frameOsc = 7757;
const extendedFlag = 1 << 28;
const paletteFlag = 0x01000000;
const rgbFlag = 0x02000000;
const left = 1;
const right = 2;
const up = 4;
const down = 8;
const topTitleMode = 1;
const bottomTitleMode = 3;
const frameModeMask = 3;
const floatingFrameFlag = 4;
const fallbackBorder = /^[─│┌┐└┘├┤┬┴┼╭╮╰╯╴╵╶╷]$/u;

function readEdge(field, count) {
    if (!field) return null;
    const match = /^([1-9a-f]):([0-9a-f]+)$/.exec(field);
    if (!match || (match[2].length !== 8 && match[2].length !== count * 8)) return undefined;
    return { mask: parseInt(match[1], 16), colors: match[2] };
}

function attachPaneBorders(terminal) {
    const service = terminal._core?._bufferService;
    if (!service || !terminal.parser?.registerOscHandler) return null;
    const frames = new WeakMap();
    const subscription = terminal.parser.registerOscHandler(frameOsc, message => {
        const fields = message.split(';');
        if (fields.length !== 7 || fields.slice(0, 4).some(field => !/^\d+$/.test(field))) return true;
        const [column, row, count, flags] = fields.slice(0, 4).map(Number);
        if (row >= terminal.rows || count < 1 || column + count > terminal.cols ||
            flags > (floatingFrameFlag | frameModeMask)) return true;
        const mode = flags & frameModeMask;
        const floating = Boolean(flags & floatingFrameFlag);

        const buffer = service.buffer;
        const line = buffer.lines.get(buffer.ybase + row);
        if (!line?.loadCell || !line.setCell || column + count > line.length) return true;
        const edges = fields.slice(4).map(field => readEdge(field, count));
        if (edges.includes(undefined)) return true;

        const cell = terminal.buffer.active.getNullCell();
        const defaultAttributes = cell.extended;
        const titleRow = mode === topTitleMode || mode === bottomTitleMode;
        for (let offset = 0; offset < count; offset++) {
            const x = column + offset;
            cell.extended = defaultAttributes;
            line.loadCell(x, cell);
            const attributes = cell.extended.clone();
            const boxGlyph = titleRow && fallbackBorder.test(cell.getChars());
            frames.set(attributes, { mode, edges, offset, boxGlyph, floating });
            // BufferLine replaces this reference on a normal write, including clears and overlays.
            cell.extended = attributes;
            cell.bg |= extendedFlag;
            line.setCell(x, cell);
        }
        return true;
    });

    return {
        dispose: () => subscription.dispose(),
        visibleFrames(first, last) {
            const result = new Map();
            const buffer = service.buffer;
            if (buffer.ydisp !== buffer.ybase) return result;
            for (let row = first; row <= last; row++) {
                const line = buffer.lines.get(buffer.ydisp + row);
                if (!line?._extendedAttrs || !line.getBg) continue;
                const rowFrames = new Map();
                for (const [column, attributes] of Object.entries(line._extendedAttrs)) {
                    const x = Number(column);
                    if (x >= terminal.cols || !(line.getBg(x) & extendedFlag)) continue;
                    const frame = frames.get(attributes);
                    if (frame) rowFrames.set(x, frame);
                }
                if (rowFrames.size) result.set(row, rowFrames);
            }
            return result;
        },
    };
}

function edgeColor(edge, offset, colors) {
    const start = edge.colors.length === 8 ? 0 : 8 * offset;
    const value = parseInt(edge.colors.slice(start, start + 8), 16);
    if (value & rgbFlag) return '#' + edge.colors.slice(start + 2, start + 8);
    if (value & paletteFlag) return colors.ansi[value & 255]?.css ?? colors.foreground.css;
    if (value === 8) return colors.foreground.css;
    if (value === 9) return colors.background.css;
    const index = value >= 90 && value <= 97 ? value - 82 : value;
    return colors.ansi[index]?.css ?? colors.foreground.css;
}

function titledTopColumns(columns) {
    // A title can span several packets. Align its entire edge, including both corners.
    const titled = new Set();
    let start = 0;
    let end = -1;
    let hasTitle = false;
    let previous;
    function finish() {
        if (hasTitle) {
            for (let column = start; column <= end; column++) titled.add(column);
        }
        hasTitle = false;
    }

    for (const [column, frame] of columns) {
        const edge = frame.edges[1];
        if (!edge || !(edge.mask & left) || column !== end + 1 ||
            !(previous?.edges[1]?.mask & right) || previous.floating !== frame.floating) {
            finish();
            start = column;
        }
        previous = frame;
        if (!edge) continue;
        end = column;
        hasTitle ||= frame.mode === topTitleMode;
    }
    finish();
    return titled;
}

function drawHorizontal(context, mask, x, y, width, height, gap, stroke, upper, inset = gap) {
    const lineY = y + (upper ? inset : height - inset - stroke);
    if (mask === (left | right)) {
        context.fillRect(x, lineY, width, stroke);
        return;
    }
    const stem = mask & right ? width - gap - stroke : gap;
    if (mask & right) context.fillRect(x + stem, lineY, width - stem, stroke);
    else context.fillRect(x, lineY, stem + stroke, stroke);
    if (upper) context.fillRect(x + stem, y, stroke, inset);
    else context.fillRect(x + stem, lineY + stroke, stroke, inset);
}

function drawFrames(layer, dimensions, rows, topShift) {
    const { width, height } = dimensions.device.cell;
    const pixelRatio = dimensions.device.canvas.width / dimensions.css.canvas.width;
    const stroke = Math.min(width, Math.floor(height / 2), Math.max(1, Math.round(pixelRatio)));
    // Mirror the side strokes so both have the same whole-pixel clearance as the horizontal strokes.
    const gap = Math.min(Math.floor((width - stroke) / 2), Math.floor((height - 2 * stroke) / 2));
    const colors = layer._themeService.colors;
    const context = layer._ctx;
    context.save();
    try {
        for (const [row, columns] of rows) {
            const y = row * height;
            const titled = titledTopColumns(columns);
            for (const [column, { edges: [upper, lower, side], offset, mode, boxGlyph, floating }] of columns) {
                const x = column * width;
                if (upper) {
                    context.fillStyle = edgeColor(upper, offset, colors);
                    drawHorizontal(context, upper.mask, x, y, width, height, gap, stroke, true);
                }
                if (lower && (mode !== topTitleMode || boxGlyph)) {
                    context.fillStyle = edgeColor(lower, offset, colors);
                    const inset = titled.has(column) ? Math.floor((height - stroke) / 2) : gap;
                    drawHorizontal(context, lower.mask, x, y, width, height, gap, stroke, false,
                        inset + (row === 0 && !floating ? topShift : 0));
                }
                if (side) {
                    context.fillStyle = edgeColor(side, offset, colors);
                    const stem = side.mask & right ? width - gap - stroke : gap;
                    const length = side.mask & down ? height : Math.floor(height / 2);
                    context.fillRect(x + stem, y + (side.mask & up ? 0 : height - length), stroke, length);
                }
            }
        }
    } finally {
        context.restore();
    }
}

function withCanvasPaneBorders(layer, dimensions, rows, title, draw) {
    if (!rows.size || !layer._themeService?.colors || !dimensions.css.canvas.width) return draw();
    const drawBackground = layer._drawBackground;
    const drawChars = layer._drawChars;
    const context = layer._ctx;
    const titleContext = title.canvas?.getContext('2d') ?? context;
    const titleOffset = (title.canvas ? title.headroom : 0) - title.shift;
    layer._drawBackground = function (first, last) {
        drawBackground.call(this, first, last);
        drawFrames(this, dimensions, rows, title.shift);
    };
    layer._drawChars = function (cell, column, row) {
        const frame = rows.get(row)?.get(column);
        if (frame?.mode === 0 || frame?.boxGlyph) return;
        if (row === 0 && title.shift && frame?.mode === topTitleMode && !frame.floating) {
            // Keep the native glyphs intact when the title extends above the main canvas.
            this._ctx = titleContext;
            titleContext.save();
            titleContext.translate(0, titleOffset);
            try {
                return drawChars.call(this, cell, column, row);
            } finally {
                titleContext.restore();
                this._ctx = context;
            }
        }
        return drawChars.call(this, cell, column, row);
    };
    try {
        return draw();
    } finally {
        layer._drawBackground = drawBackground;
        layer._drawChars = drawChars;
    }
}

module.exports = { attachPaneBorders, withCanvasPaneBorders };
