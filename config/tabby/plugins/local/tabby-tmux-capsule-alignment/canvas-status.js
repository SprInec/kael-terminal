'use strict';

const yaziBackground = 0x171b16;
const yaziModes = new Map([[0xb1e969, ' NOR '], [0xd7c183, ' SEL '], [0xe6a091, ' UNS ']]);
const yaziSegmentColors = new Set([...yaziModes.keys(), 0x3b452c, 0x293322]);
const rightArrow = '';
const leftArrow = '';
const thinArrow = '';
const paneEdges = new Set(['│', '┃', '└', '┗', '╰', '╵', '╹']);
const largerIcons = new Set('󰢮');
const logos = new Set(['󸂀', '󸂁']);
const gitSymbols = new Set(['', '✓', '●', '↑', '↓']);

function readCells(line, cell, columns) {
    const cells = [];
    for (let column = 0; column < columns; column++) {
        if (!line.getCell(column, cell)) break;
        cells.push({
            text: cell.getChars(),
            background: cell.isBgRGB() ? cell.getBgColor() : undefined,
            foreground: cell.isFgRGB() ? cell.getFgColor() : undefined,
        });
    }
    return cells;
}

function markArrows(cells, barBackground, segmentColors) {
    cells.forEach((cell, column) => {
        const { text, foreground, background } = cell;
        if (text === rightArrow || text === leftArrow) {
            const segment = cells[column + (text === rightArrow ? -1 : 1)];
            cell.solid = foreground === segment?.background && foreground !== background &&
                (segmentColors.has(foreground) || segmentColors.has(background));
        }
        cell.thin = text === thinArrow && foreground === 0x48533e && background === barBackground;
    });
}

function findTmuxStatus(line, cell, columns, buffer, row) {
    if (!line.getCell(0, cell)?.isBgRGB()) return null;
    const cells = readCells(line, cell, columns);
    const sessionBackground = cells[0].background;
    const sessionEnd = cells.findIndex(({ background }) => background !== sessionBackground);
    const boundary = cells[sessionEnd];
    if (boundary?.text !== rightArrow || boundary.foreground !== sessionBackground ||
        !cells.slice(0, sessionEnd).some(({ text }) => text === '')) return null;

    // The bar fills the right edge. The session, prefix and active window use other backgrounds.
    const barBackground = cells.at(-1).background;
    if (barBackground === undefined) return null;
    const segmentColors = new Set();
    for (const { background } of cells) {
        if (background !== undefined && background !== barBackground) segmentColors.add(background);
    }
    markArrows(cells, barBackground, segmentColors);
    const paneCell = buffer.getLine(buffer.viewportY + row - 1)?.getCell(0, cell);
    return { cells, barBackground, segmentColors, alignToPane: paneEdges.has(paneCell?.getChars()) };
}

function findYaziStatus(line, cell, columns) {
    if (!/ (NOR|SEL|UNS) /.test(line.translateToString(true))) return null;
    const row = readCells(line, cell, columns);
    const cells = [];
    // The mode and its outgoing arrow identify the start, including within a split pane.
    for (let column = 5; column < row.length; column++) {
        const { text, foreground, background } = row[column];
        const mode = yaziModes.get(foreground);
        if (text !== rightArrow || !mode || !yaziSegmentColors.has(background)) continue;

        const first = column - mode.length;
        const label = row.slice(first, column);
        if (label.some(cell => cell.background !== foreground) || label.map(cell => cell.text).join('') !== mode) continue;

        let end = first;
        while (end < row.length && (row[end].background === yaziBackground || yaziSegmentColors.has(row[end].background))) {
            cells[end] = row[end];
            end++;
        }
        column = end - 1;
    }
    if (!cells.length) return null;
    markArrows(cells, yaziBackground, yaziSegmentColors);
    return { cells, barBackground: yaziBackground, segmentColors: yaziSegmentColors };
}

function findStatuses(terminal, first, last) {
    const statuses = new Map();
    const buffer = terminal.buffer.active;
    if (terminal.hasSelection() || buffer.viewportY !== buffer.baseY) return statuses;
    const cell = buffer.getNullCell();
    for (let row = first; row <= last; row++) {
        const line = buffer.getLine(buffer.viewportY + row);
        if (!line) continue;
        const yazi = findYaziStatus(line, cell, terminal.cols);
        const status = yazi ?? (row === terminal.rows - 1 ? findTmuxStatus(line, cell, terminal.cols, buffer, row) : null);
        if (status) statuses.set(row, status);
    }
    return statuses;
}

function color(rgb) {
    return `#${rgb.toString(16).padStart(6, '0')}`;
}

function drawSegments(context, { cells, barBackground, segmentColors, geometry }) {
    const { width, height, top, centerY, inset, left, scale } = geometry;
    context.save();
    for (const [column, cell] of cells.entries()) {
        if (!cell) continue;
        const x = column * width;
        const y = top + inset;
        const bottom = top + height - inset;
        if (segmentColors.has(cell.background)) {
            const start = column === 0 ? left : 0;
            context.fillStyle = color(barBackground);
            context.fillRect(x, top, width, height);
            context.fillStyle = color(cell.background);
            context.fillRect(x + start, y, width - start, bottom - y);
        }
        if (cell.solid || cell.thin) {
            const margin = cell.thin ? width * 0.2 : 0;
            const pointsLeft = cell.text === leftArrow;
            const baseX = x + (pointsLeft ? width : margin);
            const tipX = x + (pointsLeft ? 0 : width - margin);
            context.beginPath();
            context.moveTo(baseX, y);
            context.lineTo(tipX, centerY);
            context.lineTo(baseX, bottom);
            if (cell.thin) {
                context.strokeStyle = color(cell.foreground);
                context.lineWidth = Math.max(1, scale);
                context.stroke();
            } else {
                context.fillStyle = color(cell.foreground);
                context.fill();
            }
        }
    }
    context.restore();
}

function drawStatusIcon(layer, cell, column, cells, { width, height, centerY, inset }, isLogo) {
    const { text, foreground } = cells[column];
    if (foreground === undefined || cell.isInverse() || cell.isDim() || cell.isInvisible()) return false;

    const font = layer._getFont(!!cell.isBold(), !!cell.isItalic());
    const context = layer._ctx;
    context.save();
    try {
        context.font = font;
        context.textBaseline = 'alphabetic';
        context.textAlign = 'left';
        let metrics = context.measureText(text);
        if (!isLogo) {
            const pixelSize = /(\d+(?:\.\d+)?)px(?=\s)/;
            const match = font.match(pixelSize);
            if (!match) return false;
            const normalSize = Number(match[1]);
            const space = neighbour => cells[neighbour]?.text === ' ' ? width * 0.4 : 0;
            const maxWidth = width + 2 * Math.min(space(column - 1), space(column + 1));
            const widthFit = maxWidth / (metrics.actualBoundingBoxLeft + metrics.actualBoundingBoxRight);
            const heightFit = (height - 2 * inset) / (metrics.actualBoundingBoxAscent + metrics.actualBoundingBoxDescent);
            const size = Math.min(Math.round(normalSize * 1.18), Math.floor(normalSize * Math.min(widthFit, heightFit)));
            if (!(size > normalSize)) return false;

            context.font = font.replace(pixelSize, `${size}px`);
            metrics = context.measureText(text);
        }
        const x = Math.round((column + 0.5) * width + (metrics.actualBoundingBoxLeft - metrics.actualBoundingBoxRight) / 2);
        const y = Math.round(centerY + (metrics.actualBoundingBoxAscent - metrics.actualBoundingBoxDescent) / 2);
        context.fillStyle = color(foreground);
        context.fillText(text, x, y);
        if (isLogo) {
            // Strengthen the partly covered pixels of thin strokes at the same size and position.
            context.globalAlpha *= 0.35;
            context.fillText(text, x, y);
        }
        return true;
    } finally {
        context.restore();
    }
}

function centerAtlasIcon(context, centerY, draw) {
    const drawImage = context.drawImage;
    context.drawImage = function (image, sx, sy, sw, sh, dx, dy, dw, dh) {
        const y = Math.round(centerY - dh / 2);
        return drawImage.call(this, image, sx, sy, sw, sh, dx, y, dw, dh);
    };
    try {
        return draw();
    } finally {
        context.drawImage = drawImage;
    }
}

function withCanvasStatuses(renderer, layer, statuses, draw) {
    const { width, height } = renderer.dimensions.device.cell;
    const scale = height / renderer.dimensions.css.cell.height;
    const context = layer._ctx;
    context.save();
    context.font = layer._getFont(false, false);
    context.textBaseline = 'ideographic';
    // Use cap height and tabular digits as the optical center while keeping one text baseline.
    const metrics = context.measureText('H0');
    context.restore();
    const nativeTextCenter = layer._deviceCharTop + layer._deviceCharHeight +
        (metrics.actualBoundingBoxDescent - metrics.actualBoundingBoxAscent) / 2;

    for (const [row, status] of statuses) {
        const top = row * height;
        // At fractional display scales the canvas can end partway through the last device pixel row.
        const rowHeight = Math.min(height, context.canvas.height - top);
        if (rowHeight <= 0) {
            statuses.delete(row);
            continue;
        }
        const inset = Math.min(Math.round(scale), Math.floor((rowHeight - 1) / 2));
        status.geometry = { width, height: rowHeight, inset, scale, top, centerY: top + rowHeight / 2,
            left: status.alignToPane ? Math.floor(width / 2) : 0,
            textShift: Math.round(rowHeight / 2 - nativeTextCenter) };
    }

    const drawBackground = layer._drawBackground;
    const drawChars = layer._drawChars;
    layer._drawBackground = function (first, last) {
        drawBackground.call(this, first, last);
        for (const [row, status] of statuses) {
            if (first <= row && row <= last) drawSegments(context, status);
        }
    };
    layer._drawChars = function (cell, column, line) {
        const status = statuses.get(line);
        const current = status?.cells[column];
        if (!current) return drawChars.call(this, cell, column, line);
        if (current.solid || current.thin) return;
        const { cells, geometry } = status;
        const { centerY, inset, textShift, top } = geometry;
        const render = () => drawChars.call(this, cell, column, line);
        const isLogo = logos.has(current.text);
        const isStatusIcon = isLogo || largerIcons.has(current.text);
        if (isStatusIcon && drawStatusIcon(layer, cell, column, cells, geometry, isLogo)) return;
        if (isStatusIcon || gitSymbols.has(current.text)) return centerAtlasIcon(context, centerY, render);
        if (!textShift || !current.text || current.text === ' ' || current.text === '│') return render();

        context.save();
        context.beginPath();
        context.rect(0, top + inset, context.canvas.width, geometry.height - 2 * inset);
        context.clip();
        context.translate(0, textShift);
        try {
            return render();
        } finally {
            context.restore();
        }
    };
    try {
        return draw();
    } finally {
        layer._drawBackground = drawBackground;
        layer._drawChars = drawChars;
    }
}

module.exports = { findStatuses, withCanvasStatuses };
