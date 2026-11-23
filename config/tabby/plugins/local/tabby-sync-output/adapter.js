'use strict';
const { SyncFrameBatcher } = require('./frame-batcher');

function attachSyncOutput(frontend, logger = console) {
    const terminal = frontend?.xterm;
    const service = terminal?._core?.coreService || terminal?._core?._coreService;
    if (!terminal?.parser?.registerCsiHandler || !service?.triggerDataEvent ||
        typeof frontend.write !== 'function') return null;
    if (frontend.__syncOutputAdapter) return frontend.__syncOutputAdapter;

    const originalWrite = frontend.write;
    let queue = Promise.resolve();
    let disposed = false;
    const batcher = new SyncFrameBatcher(text => {
        queue = queue.catch(error => logger.warn('Sync output write failed', error))
            .then(() => disposed ? undefined : originalWrite.call(frontend, text));
        // A watchdog flush has no caller awaiting the promise.
        queue.catch(() => {});
    });
    const wrappedWrite = function (text) {
        if (typeof text !== 'string') return originalWrite.call(this, text);
        batcher.feed(text);
        return queue;
    };
    frontend.write = wrappedWrite;

    // tmux probes this mode when attaching. Advertise support only after the
    // write adapter is installed; no blanket terminal-features override needed.
    const query = terminal.parser.registerCsiHandler(
        { prefix: '?', intermediates: '$', final: 'p' }, params => {
            if (params.length !== 1 || params[0] !== 2026) return false;
            service.triggerDataEvent(`\x1b[?2026;${batcher.active ? 1 : 2}$y`);
            return true;
        });

    const adapter = {
        dispose() {
            disposed = true;
            query.dispose();
            batcher.dispose();
            if (frontend.write === wrappedWrite) frontend.write = originalWrite;
            delete frontend.__syncOutputAdapter;
        },
    };
    frontend.__syncOutputAdapter = adapter;
    return adapter;
}

module.exports = { attachSyncOutput };
