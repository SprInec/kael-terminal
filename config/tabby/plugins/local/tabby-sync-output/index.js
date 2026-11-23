'use strict';
const { Injectable, NgModule } = require('@angular/core');
const { TerminalDecorator } = require('tabby-terminal');
const { attachSyncOutput } = require('./adapter');

class SyncOutputDecorator extends TerminalDecorator {
    constructor() {
        super();
        this.adapters = new Map();
    }
    attach(tab) {
        const adapter = attachSyncOutput(tab.frontend, tab.logger || console);
        if (adapter) this.adapters.set(tab, adapter);
    }
    detach(tab) {
        this.adapters.get(tab)?.dispose();
        this.adapters.delete(tab);
        super.detach(tab);
    }
}
Injectable()(SyncOutputDecorator);

class SyncOutputModule {}
NgModule({
    providers: [{ provide: TerminalDecorator, useClass: SyncOutputDecorator, multi: true }],
})(SyncOutputModule);

module.exports = { default: SyncOutputModule };
