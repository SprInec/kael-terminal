'use strict';

// Buffer DECSET 2026 frames before xterm parses them. This keeps transport
// packet boundaries from exposing intermediate cursor positions in xterm 5.
// Escape strings are tracked so embedded sequences in OSC/DCS remain data.
class SyncFrameBatcher {
    constructor(emit, options = {}) {
        this.emit = emit;
        this.setTimer = options.setTimeout || setTimeout;
        this.clearTimer = options.clearTimeout || clearTimeout;
        this.timeout = options.timeout || 1000;
        this.limit = options.limit || 1024 * 1024;
        this.state = 'ground';
        this.sequence = '';
        this.stringKind = '';
        this.active = false;
        this.frame = '';
        this.plain = '';
        this.timer = null;
    }

    append(text) {
        if (this.active) {
            this.frame += text;
            if (this.frame.length > this.limit) this.finish(true);
        } else {
            this.plain += text;
        }
    }

    flushPlain() {
        if (!this.plain) return;
        const text = this.plain;
        this.plain = '';
        this.emit(text);
    }

    start(sequence) {
        if (this.active) {
            this.append(sequence); // DECSET is idempotent, not nested.
            return;
        }
        this.flushPlain();
        this.active = true;
        this.frame = sequence;
        this.timer = this.setTimer(() => this.finish(true), this.timeout);
    }

    finish(forced = false) {
        if (!this.active) return;
        if (this.timer !== null) this.clearTimer(this.timer);
        this.timer = null;
        this.active = false;
        const text = this.frame + (forced ? '\x1b[?2026l' : '');
        this.frame = '';
        this.emit(text);
    }

    feed(text) {
        for (const char of text) {
            switch (this.state) {
            case 'ground':
                if (char === '\x1b') {
                    this.sequence = char;
                    this.state = 'escape';
                } else if (char === '\x9b') {
                    this.sequence = char;
                    this.state = 'csi';
                } else if ('\x90\x98\x9d\x9e\x9f'.includes(char)) {
                    this.append(char);
                    this.stringKind = char === '\x9d' ? 'osc' : 'other';
                    this.state = 'string';
                } else {
                    this.append(char);
                }
                break;
            case 'escape':
                if (char === '[') {
                    this.sequence += char;
                    this.state = 'csi';
                } else if (']P_^X'.includes(char)) {
                    this.append(this.sequence + char);
                    this.sequence = '';
                    this.stringKind = char === ']' ? 'osc' : 'other';
                    this.state = 'string';
                } else if (char === '\x1b') {
                    this.append(this.sequence);
                    this.sequence = char;
                } else {
                    this.append(this.sequence + char);
                    this.sequence = '';
                    this.state = 'ground';
                }
                break;
            case 'csi': {
                this.sequence += char;
                if (char >= '@' && char <= '~') {
                    const sequence = this.sequence;
                    this.sequence = '';
                    this.state = 'ground';
                    if (/^(?:\x1b\[|\x9b)\?2026h$/.test(sequence)) {
                        this.start(sequence);
                    } else {
                        this.append(sequence);
                        if (/^(?:\x1b\[|\x9b)\?2026l$/.test(sequence)) this.finish();
                    }
                } else if (char === '\x18' || char === '\x1a' || this.sequence.length > 256) {
                    this.append(this.sequence);
                    this.sequence = '';
                    this.state = 'ground';
                } else if (char === '\x1b') {
                    this.append(this.sequence.slice(0, -1));
                    this.sequence = char;
                    this.state = 'escape';
                }
                break;
            }
            case 'string':
                this.append(char);
                if (char === '\x1b') this.state = 'string-escape';
                else if (char === '\x9c' || char === '\x18' || char === '\x1a' ||
                    (char === '\x07' && this.stringKind === 'osc')) this.state = 'ground';
                break;
            case 'string-escape':
                this.append(char);
                if (char === '\\' || char === '\x9c' || char === '\x18' || char === '\x1a') this.state = 'ground';
                else if (char !== '\x1b') this.state = 'string';
                break;
            }
        }
        this.flushPlain();
    }

    dispose() {
        if (this.timer !== null) this.clearTimer(this.timer);
        this.timer = null;
        this.active = false;
        this.frame = this.plain = this.sequence = '';
    }
}

module.exports = { SyncFrameBatcher };
