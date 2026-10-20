const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const root = `${__dirname}/..`;
const source = fs.readFileSync(`${root}/app.js`, 'utf8');
const controls = new Map();
const context = vm.createContext({
  console, Math, Number, Map, Set, Date,
  state: {
    showTitleBlock: true, orientation: 'landscape', sheetMargin: 5, planZoom: 500,
    panX: 14, panY: -22, calibration: { metersPerNativeUnit: 2 }, planDate: '2026-10-20',
    location: 'Un emplacement extrêmement long dont toutes les informations doivent rester affichées sans dépasser du cadre',
    client: 'Un client avec un très long intitulé',
    author: { name: 'Un auteur dont le nom est particulièrement long', role: 'Une fonction très détaillée qui doit rester lisible' },
    validatorEnabled: true, validator: { name: 'Validateur', role: 'CRP', signature: { dataUrl: 'data:image/png;base64,example' } },
    interventions: [{ id: 't1', company: 'Une société avec un nom très long et complet', isotope: 'Ir-192', activity: 40, unit: 'Ci', attenuation: true, color: '#287dc0', scheduleStart: '00:00', scheduleEnd: '04:00', overEnabled: true, overDistance: 50, overColor: '#287dc0' }],
    circles: [
      { interventionId: 't1', radius: 18, threshold: 2.5, attenuated: true },
      { interventionId: 't1', radius: 18, threshold: 2.5, attenuated: true },
      { interventionId: 't1', radius: 8, threshold: 25, attenuated: true },
      { interventionId: 't1', radius: 35, threshold: 'manual', attenuated: false },
      { interventionId: 't1', radius: 50, threshold: 'manual', attenuated: false },
    ],
  },
  titleBlock: { style: {}, attributes: {}, setAttribute(k, v) { this.attributes[k] = v; } },
  document: {
    createElement() { return { getContext() { return { measureText(text) { return { width: text.length * Number.parseFloat(this.font.split(' ')[1]) * 0.58 }; } }; } }; },
    querySelector(selector) { if (!controls.has(selector)) controls.set(selector, {}); return controls.get(selector); },
  },
  updates: 0, finalizations: 0,
});
vm.runInContext(fs.readFileSync(`${root}/assets/balisage.js`, 'utf8'), context);
vm.runInContext(`
  function escapeText(value) { return String(value).replaceAll('&', '&amp;').replaceAll('<', '&lt;'); }
  function formatTime(value) { return value.replace(':', 'h'); }
  function circleIsVisible(circle) { return !circle.hidden; }
  function radiusMeters() { return 99; }
  function scheduleInteractionUpdate() { updates++; }
  function finalizeNavigation() { finalizations++; }
`, context);
for (const name of ['formatDistance', 'mapScale', 'metersPerPlanUnit', 'metersToPlanUnits', 'niceScaleSegment', 'titleBlockFont', 'titleBlockText', 'personRowMarkup', 'visibleInterventionsForTitleBlock', 'renderTitleBlock', 'setPlanZoom', 'resetPlanView']) {
  const start = source.indexOf(`function ${name}(`);
  const end = source.indexOf('\n}', start) + 2;
  assert.ok(start >= 0 && end > start, name);
  vm.runInContext(source.slice(start, end), context);
}
let entries = vm.runInContext('CrobardBalisage.entries(state.circles, {})', context);
assert.deepEqual(Array.from(entries, (e) => [e.threshold, e.distance]), [[2.5, 18], [25, 8], ['manual', 35], ['manual', 50]]);
assert.equal(vm.runInContext("CrobardBalisage.entries([{ threshold: 25, distance: NaN }], {}).length", context), 0);
context.state.circles[1].hidden = true;
context.renderTitleBlock();
const markup = context.titleBlock.innerHTML;
assert.match(markup, /Balisage 2,5 µSv\/h : 18 m/);
assert.match(markup, /Balisage 25 µSv\/1h : 8\.0 m/);
assert.match(markup, /Balisage manuel : 35 m/);
assert.match(markup, /Balisage manuel : 50 m/);
assert.match(markup, /Surbalisage de sécurité/);
assert.match(markup, /Réalisé par/);
assert.match(markup, /Validé par/);
assert.match(markup, /data:image\/png/);
assert.match(markup, /rx="3"/);
assert.ok(!markup.includes('stroke="#17212b"'), 'No table separators');
assert.ok(markup.includes('<tspan'), 'Long labels must wrap');

const calibration = JSON.stringify(context.state.calibration);
const circles = JSON.stringify(context.state.circles);
context.resetPlanView();
assert.equal(context.state.planZoom, 100);
assert.equal(context.state.panX, 0); assert.equal(context.state.panY, 0);
assert.equal(controls.get('#plan-zoom').value, 1);
assert.equal(controls.get('#settings-zoom').value, 1);
assert.equal(context.updates, 1); assert.equal(context.finalizations, 1);
assert.equal(JSON.stringify(context.state.calibration), calibration);
assert.equal(JSON.stringify(context.state.circles), circles);
console.log('Cartouche: distinct markings, wrapped content, signatures and reset-to-fit passed.');
