const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const { test } = require('node:test');

const source = fs.readFileSync(path.join(__dirname, 'douyuex.js'), 'utf8');
const code = source.slice(source.indexOf('function initExStarRecommend()'), source.indexOf('\nfunction s()'));
const key = 'Ex_StarRecommend_Run';

function harness({ worker = false, controller = false, countdown = false, limit = false, apiFailure = false, room = '123', roomList = [456, 456, 'bad'], setup = () => {}, store = new Map() } = {}) {
    if ((worker || controller) && !store.has(key)) store.set(key, { token: 'test', ownerBeat: Date.now() });
    const intervals = [];
    const clicks = [];
    const opened = [];
    const navigations = [];
    const logs = [];
    const session = new Map();
    const events = new Map();
    let command;
    let claimed = false;
    let closed = false;
    let offset = 0;
    const node = (name, content = '') => ({
        isConnected: true, textContent: content, disabled: false,
        getClientRects: () => [1], getAttribute: () => null,
        click() { clicks.push(name); if (name === 'claim') claimed = true; },
        querySelector(selector) {
            if (selector.includes('boxIcon')) return icon;
            if (selector.includes('boxHeadline')) return headline;
            if (selector.includes('boxContent')) return counter;
            if (selector.includes('container__')) return entry;
            return null;
        },
        querySelectorAll(selector) {
            if (selector.includes('singleBagOpened')) return claimed ? [success] : [];
            if (selector.includes('singleBag--btn')) return [button];
            if (selector.includes('pop--close')) return [close];
            return [];
        }
    });
    const icon = node('icon');
    const headline = node('headline', countdown ? '倒计时' : '可领取');
    const counter = node('counter', countdown ? '00:20' : '');
    const entry = node('entry');
    const item = node('item');
    const popup = node('popup');
    const button = node('claim', '立即领取');
    const success = node('success');
    const close = node('close');
    const message = node('message', '今日红包已达上限');
    const ui = { item, headline, counter, popup, button, bag: node('bag'), items: [item], hasButton: true, hasBag: false };
    ui.bag.click = () => { clicks.push('bag'); claimed = true; };
    popup.querySelectorAll = selector => {
        if (selector.includes('singleBagOpened')) return claimed ? [success] : [];
        if (selector.includes('singleBag--btn')) return ui.hasButton ? [button] : [];
        if (selector.includes('singleBag')) return ui.hasBag ? [ui.bag] : [];
        if (selector.includes('pop--close')) return [close];
        return [];
    };
    setup(ui);
    const document = {
        readyState: 'complete', body: {}, head: { appendChild() {} },
        documentElement: { setAttribute() {}, removeAttribute() {} },
        getElementById: () => null, createElement: () => ({}), querySelector: () => null,
        querySelectorAll(selector) {
            if (selector.includes('activeItem')) return ui.items;
            if (selector.includes('pop--inner')) return [popup];
            if (selector.includes('dy-Message')) return limit ? [message] : [];
            return [];
        }
    };
    const location = {
        hostname: 'www.douyu.com', pathname: '/' + room, search: worker ? '?exStarWorker=test' : controller ? '?exStarController=test' : '',
        replace: url => navigations.push(url)
    };
    const window = { addEventListener: (name, callback) => events.set(name, callback), close() { closed = true; } };
    window.top = window.self = window;
    vm.runInNewContext(code, {
        window, location, document, URLSearchParams, DOMException, AbortController,
        Date: class extends Date { static now() { return Date.now() + offset; } },
        console: { log: message => logs.push(message) }, crypto: { randomUUID: () => 'test' },
        getComputedStyle: () => ({ visibility: 'visible' }), MutationObserver: class { observe() {} },
        sessionStorage: { getItem: name => session.get(name) || null, setItem: (name, value) => session.set(name, value), removeItem: name => session.delete(name) },
        GM_getValue: (name, fallback) => store.has(name) ? store.get(name) : fallback,
        GM_setValue: (name, value) => store.set(name, value), GM_deleteValue: name => store.delete(name),
        GM_registerMenuCommand: (label, callback) => { command = callback; },
        GM_openInTab(url, options) {
            const tab = { url, options, close() { this.closed = true; } };
            opened.push(tab);
            return tab;
        },
        GM_xmlhttpRequest(options) {
            queueMicrotask(() => options.onload({ status: apiFailure ? 500 : 200, response: {
                error: 0, data: { redBagList: roomList.map(rid => ({ rid })) }
            } }));
            return { abort() {} };
        },
        setTimeout, clearTimeout,
        setInterval: callback => { intervals.push(callback); return intervals.length; }, clearInterval() {}
    });
    return { store, clicks, opened, navigations, logs, ui, toggle: () => command(),
        tick: (advance = 0) => { offset += advance; intervals.forEach(callback => callback()); }, closed: () => closed,
        pagehide: (persisted = false) => events.get('pagehide')({ persisted }) };
}

const flush = () => new Promise(resolve => setImmediate(resolve));

test('menu opens the red bag room directly and explicit stop closes it', async () => {
    const run = harness();
    assert.equal(run.opened.length, 0);
    run.toggle();
    await flush();
    assert.equal(run.opened.length, 1);
    assert.equal(run.opened[0].url, 'https://www.douyu.com/456?exStarWorker=test');
    assert.equal(run.opened[0].options.active, true);
    assert.equal(run.opened[0].options.setParent, false);
    const controller = harness({ worker: true, countdown: true, room: '456', store: run.store });
    run.toggle();
    assert.equal(run.store.has(key), false);
    controller.tick();
    assert.equal(controller.closed(), true);
    assert.equal(controller.opened.length, 0);
    assert.equal(run.opened[0].closed, true);
});

test('worker claims once then navigates in the same tab', async () => {
    const run = harness({ worker: true });
    await new Promise(resolve => setTimeout(resolve, 1100));
    assert.equal(run.clicks.filter(name => name === 'claim').length, 1);
    assert.equal(run.closed(), false);
    assert.deepEqual(run.navigations, ['https://www.douyu.com/456?exStarWorker=test']);
    assert.equal(run.opened.length, 0);
    assert(run.store.get(key).visited['123'] > 0);
    assert(run.logs.some(message => message.includes('到账以平台记录为准')));
});

test('worker recognizes decorated clock and Chinese seconds countdowns', async () => {
    for (const counterText of ['开奖倒计时 00：00', '剩余 0秒']) {
        const run = harness({ worker: true, countdown: true, setup(ui) { ui.counter.textContent = counterText; } });
        await new Promise(resolve => setTimeout(resolve, 1100));
        assert.equal(run.clicks.filter(name => name === 'claim').length, 1);
        assert.equal(run.navigations.length, 1);
    }
});

test('worker waits for a replaced activity component and reads ready state from content', async () => {
    const run = harness({ worker: true, countdown: true });
    run.ui.item.isConnected = false;
    run.ui.items = [];
    await new Promise(resolve => setTimeout(resolve, 300));
    assert.equal(run.closed(), false);
    assert.equal(run.store.get(key).workerDone, undefined);
    run.ui.items = [{ ...run.ui.item, isConnected: true }];
    run.ui.counter.textContent = '立即领取';
    await new Promise(resolve => setTimeout(resolve, 1400));
    assert.equal(run.clicks.filter(name => name === 'claim').length, 1);
    assert.equal(run.navigations.length, 1);
});

test('worker waits for popup countdown then clicks at zero seconds', async () => {
    const run = harness({ worker: true, setup(ui) { ui.button.textContent = '1秒后打开'; } });
    assert.equal(run.clicks.length, 0);
    run.ui.button.textContent = '0秒后打开';
    await new Promise(resolve => setTimeout(resolve, 1400));
    assert.equal(run.clicks.filter(name => name === 'claim').length, 1);
    assert.equal(run.navigations.length, 1);
});

test('worker opens the bag when the popup has no separate button', async () => {
    const run = harness({ worker: true, setup(ui) { ui.hasButton = false; ui.hasBag = true; } });
    await new Promise(resolve => setTimeout(resolve, 1100));
    assert.equal(run.clicks.filter(name => name === 'bag').length, 1);
    assert.equal(run.navigations.length, 1);
});

test('empty discovery waits in the current tab and retries after cooldown', async () => {
    const run = harness({ worker: true, room: '456' });
    await new Promise(resolve => setTimeout(resolve, 1100));
    assert.equal(run.navigations.length, 0);
    assert.equal(run.closed(), false);
    assert(run.logs.some(message => message.includes('15秒后重试')));
    run.tick(15000);
    await flush();
    assert.equal(run.navigations.length, 0, 'recent room is not reopened');
    run.tick(46000);
    await flush();
    assert.deepEqual(run.navigations, ['https://www.douyu.com/456?exStarWorker=test']);
    run.tick(60000);
    await flush();
    assert.equal(run.navigations.length, 1, 'navigation is not repeated before pagehide');
    run.toggle();
});

test('explicit stop cancels countdown before clicking', async () => {
    const run = harness({ worker: true, countdown: true });
    run.store.delete(key);
    run.tick();
    await flush();
    assert.equal(run.closed(), true);
    assert.equal(run.clicks.length, 0);
    assert.equal(run.navigations.length, 0);
});

test('daily limit stops globally without submitting a claim', async () => {
    const run = harness({ worker: true, limit: true });
    await flush();
    assert.equal(run.store.has(key), false);
    assert.equal(run.clicks.length, 0);
    assert.equal(run.navigations.length, 0);
});

test('discovery failure is visible and does not open a worker', async () => {
    const run = harness({ apiFailure: true });
    run.toggle();
    await flush();
    assert.equal(run.opened.length, 0);
    assert(run.logs.some(message => message.includes('HTTP 500')));
    run.toggle();
});

test('closing original room leaves red bag controller running through navigation', async () => {
    const original = harness();
    original.toggle();
    await flush();
    const controller = harness({ worker: true, room: '456', countdown: true, store: original.store, roomList: [789] });
    original.pagehide();
    assert.equal(original.opened[0].closed, undefined, 'original page must not close controller');
    controller.ui.counter.textContent = '00:00';
    await new Promise(resolve => setTimeout(resolve, 1400));
    assert.deepEqual(controller.navigations, ['https://www.douyu.com/789?exStarWorker=test']);
    controller.pagehide();
    assert(original.store.has(key), 'navigation preserves run state');
    const next = harness({ worker: true, room: '789', store: original.store, roomList: [456, 900] });
    await new Promise(resolve => setTimeout(resolve, 1100));
    assert.equal(next.clicks.filter(name => name === 'claim').length, 1);
    assert.deepEqual(next.navigations, ['https://www.douyu.com/900?exStarWorker=test']);
    assert.equal(next.opened.length, 0);
    next.toggle();
});

test('turning off from another room stops the red bag controller', async () => {
    const original = harness();
    original.toggle();
    await flush();
    const controller = harness({ worker: true, countdown: true, store: original.store });
    const anotherRoom = harness({ store: original.store });
    anotherRoom.toggle();
    controller.tick();
    await flush();
    assert.equal(controller.clicks.length, 0);
    assert.equal(controller.closed(), true);
});

test('legacy controller URLs become combined claim and navigation pages', async () => {
    const worker = harness({ controller: true });
    await new Promise(resolve => setTimeout(resolve, 1100));
    assert.equal(worker.clicks.filter(name => name === 'claim').length, 1);
    assert.equal(worker.closed(), false);
    assert.equal(worker.opened.length, 0);
    assert.deepEqual(worker.navigations, ['https://www.douyu.com/456?exStarWorker=test']);
});
