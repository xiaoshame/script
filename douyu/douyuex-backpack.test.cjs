const { readFileSync } = require('node:fs');
const { join } = require('node:path');
const { runInNewContext } = require('node:vm');
const assert = require('node:assert/strict');
const { test } = require('node:test');

const source = readFileSync(join(__dirname, 'douyuex.js'), 'utf8');
const resolver = source.slice(source.indexOf('function resolveDouyuRoomId('), source.indexOf('\nfunction s()'));
const toolbarStart = source.indexOf('} function d() {') + 2;
const toolbarSetup = source.indexOf('    var i = document.createElement("div"), l = (i.className = "ChatToolBar-DanmakuTail"', toolbarStart);
const toolbarHelpers = source.slice(toolbarStart, toolbarSetup);
const toolbarMount = source.slice(toolbarSetup).match(/mountSignIn\(e\.querySelector\("\.ex-panel__wrap"\)\);/)[0];

function setup({ page = {}, playerId, scripts = [] } = {}) {
    const requests = [];
    const notices = [];
    const canonical = { href: 'https://www.douyu.com/55524' };
    const document = {
        createElement: () => ({}),
        querySelector(selector) {
            if (selector.includes('[data-room-id]') && playerId) return { getAttribute: () => playerId };
            if (selector.includes('canonical')) return canonical;
            return null;
        },
        scripts: scripts.map(textContent => ({ textContent })),
        getElementById: id => ({ value: id.endsWith('_cnt') ? '2' : '268' }),
    };
    const signIns = [];
    const handlers = runInNewContext(`${resolver}\n${toolbarHelpers}\nconst icons = [];\nconst e = { querySelector: () => ({ prepend: icon => icons.push(icon) }) };\n${toolbarMount}\nreturn { sendBackpackGifts, loadCurrentBackpack, icons };\n}\nd()`, {
        document,
        Ar: class {
            constructor(icon) { this.icon = icon; }
            click(fn) { this.icon.click = fn; }
            longClick(fn) { this.icon.longClick = fn; }
        },
        Wn: mode => signIns.push(mode),
        unsafeWindow: page,
        location: { pathname: '/55524' },
        confirm: () => true,
        b: async () => {},
        pt: (id, callback) => { requests.push(['list', id]); callback({}); },
        Ut: async (...args) => { requests.push(['gift', ...args]); return { msg: 'success' }; },
        T: (message, type) => notices.push([message, type]),
    });
    return { ...handlers, requests, notices, signIns };
}

test('toolbar initialization mounts sign-in without executing it', () => {
    const h = setup();
    assert.equal(h.icons.length, 1);
    assert.match(h.icons[0].innerHTML, /一键签到/);
    assert.deepEqual(h.signIns, []);
    h.icons[0].click();
    h.icons[0].longClick();
    assert.deepEqual(h.signIns, [false, true]);
});

test('backpack reads and sends using the real ID rather than the alias or canonical URL', async () => {
    const h = setup({ page: { room_id: 594613 } });
    h.loadCurrentBackpack((_, id) => assert.equal(id, '594613'));
    await h.sendBackpackGifts();
    assert.deepEqual(h.requests, [['list', '594613'], ['gift', '268', 1, '594613'], ['gift', '268', 1, '594613']]);
});

test('another room can resolve its real ID from the player or stream configuration without a mapping', async () => {
    for (const options of [{ playerId: '912345' }, { scripts: ['const stream = getLegacyFirstStream({ roomID: 912345, nonce: "x" });'] }]) {
        const h = setup(options);
        await h.sendBackpackGifts();
        assert.deepEqual(h.requests.map(request => request[3]), ['912345', '912345']);
    }
});

test('the alias alone does not authorize backpack requests', async () => {
    const h = setup();
    h.loadCurrentBackpack(() => assert.fail('unexpected backpack response'));
    await h.sendBackpackGifts();
    assert.deepEqual(h.requests, []);
    assert.deepEqual(h.notices.map(notice => notice[1]), ['error', 'error']);
});
