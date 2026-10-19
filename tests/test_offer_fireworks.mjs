import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import test from 'node:test';
import vm from 'node:vm';

const template = readFileSync(new URL('../templates/members/confirm_offer.html', import.meta.url), 'utf8');
const script = template.match(/<script>([\s\S]*?)<\/script>/)[1];

function offerPage(confirmed, accepted = true) {
  const elements = new Map();
  const listeners = new Map();
  const frames = [];
  const context2d = new Proxy({}, { get: (target, name) => target[name] ?? (() => {}) });
  const canvas = { style: {}, getContext: () => context2d };
  elements.set('confettiCanvas', canvas);
  let buttonId = confirmed ? 'acceptedBtn' : 'offerBtn';
  const button = {
    disabled: false,
    get id() { return buttonId; },
    set id(value) { elements.delete(buttonId); buttonId = value; elements.set(value, button); },
    addEventListener: (name, callback) => listeners.set(name, callback),
    removeEventListener: (name, callback) => {
      if (listeners.get(name) === callback) listeners.delete(name);
    },
    getBoundingClientRect: () => ({ left: 0, top: 0, width: 300, height: 60 }),
  };
  elements.set(buttonId, button);
  elements.set('toastContainer', {
    insertAdjacentHTML: (_, html) => {
      elements.set(html.match(/id="(toast-\d+)"/)[1], {
        addEventListener() {}, remove() {},
      });
    },
  });
  let ready;
  let posts = 0;
  let toasts = 0;
  const context = vm.createContext({
    document: {
      getElementById: id => elements.get(id),
      addEventListener: (_, callback) => { ready = callback; },
    },
    window: {
      innerWidth: 1000, innerHeight: 800, location: { href: 'https://example.invalid/offer/' },
      matchMedia: () => ({ matches: false }), addEventListener() {},
    },
    bootstrap: { Toast: class { show() { toasts += 1; } } },
    requestAnimationFrame: callback => frames.push(callback),
    fetch: async () => {
      posts += 1;
      return { ok: accepted, json: async () => ({ status: accepted ? 'success' : 'error' }) };
    },
  });
  vm.runInContext(script, context);
  ready();
  return {
    button, canvas,
    click: () => listeners.get('click')({ currentTarget: button }),
    finishAnimation() {
      let rendered = 0;
      while (frames.length) {
        assert.ok(++rendered < 2000, 'Animation must finish');
        frames.shift()();
      }
      assert.equal(canvas.style.display, 'none');
    },
    get posts() { return posts; },
    get toasts() { return toasts; },
  };
}

test('confirmed offers replay after each animation fully finishes without another POST', async () => {
  const page = offerPage(true);
  for (let cycle = 0; cycle < 3; cycle += 1) {
    await page.click();
    assert.equal(page.canvas.style.display, 'block');
    page.finishAnimation();
  }
  assert.equal(page.posts, 0);
});

test('acceptance shows success once and the same button can replay after the canvas hides', async () => {
  const page = offerPage(false);
  assert.match(page.button.innerHTML, /接受offer/);
  await page.click();
  assert.equal(page.button.id, 'acceptedBtn');
  assert.equal(page.button.disabled, false);
  assert.match(page.button.innerHTML, /已接受offer/);
  assert.doesNotMatch(page.button.innerHTML, /再放烟花/);
  assert.equal(page.toasts, 1);
  page.finishAnimation();
  await page.click();
  assert.equal(page.canvas.style.display, 'block');
  page.finishAnimation();
  assert.equal(page.posts, 1);
  assert.equal(page.toasts, 1);
});

test('a failed confirmation keeps the retry button and does not celebrate', async () => {
  const page = offerPage(false, false);
  await page.click();
  assert.equal(page.button.id, 'offerBtn');
  assert.equal(page.button.disabled, false);
  assert.match(page.button.innerHTML, /重试确认/);
  assert.notEqual(page.canvas.style.display, 'block');
  assert.equal(page.posts, 1);
});
