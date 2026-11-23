'use strict';

const { Injectable, NgModule } = require('@angular/core');
const { TerminalDecorator } = require('tabby-terminal');
const { attachCapsuleAlignment } = require('./renderer');

class CapsuleAlignmentDecorator extends TerminalDecorator {
    constructor() {
        super();
        this.adapters = new Map();
    }

    attach(tab) {
        if (this.adapters.has(tab)) return;
        const adapter = attachCapsuleAlignment(tab.frontend);
        if (adapter) this.adapters.set(tab, adapter);
    }

    detach(tab) {
        this.adapters.get(tab)?.dispose();
        this.adapters.delete(tab);
        super.detach(tab);
    }
}

Injectable()(CapsuleAlignmentDecorator);

class CapsuleAlignmentModule {}
NgModule({
    providers: [{ provide: TerminalDecorator, useClass: CapsuleAlignmentDecorator, multi: true }],
})(CapsuleAlignmentModule);

module.exports = { default: CapsuleAlignmentModule };
