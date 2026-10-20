const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const source = fs.readFileSync(`${__dirname}/../app.js`, 'utf8');
const context = vm.createContext({
  Math, Number, Set,
  state: { calibration: { metersPerNativeUnit: 2 }, measurements: [], circles: [], merges: [], overzoneMerges: [], signals: [], suppressedOverzones: [] },
  activeTool: 'measure', pendingMeasurementPoint: null, measurementPreviewPoint: null,
  selectedCircleIds: new Set(), selectedMergeIds: new Set(), selectedSignalIds: new Set(), selectedOverzoneKeys: new Set(), selectedMeasurementIds: new Set(),
  scale: 1, saved: 0, canvasHint: {}, NS: 'http://www.w3.org/2000/svg',
  measurementLayer: { children: [], replaceChildren() { this.children = []; }, append(element) { this.children.push(element); } },
  document: { createElementNS() { return { attrs: {}, dataset: {}, setAttribute(key, value) { this.attrs[key] = value; }, addEventListener() {} }; } },
});
vm.runInContext(`
  function mapScale() { return scale; }
  function svgPointFromEvent(event) { return event.point; }
  function uid() { return 'measurement-test'; }
  function setTool(tool) { activeTool = tool; }
  function renderZones() { renderMeasurements(); }
  function renderTitleBlock() {}
  function saveState() { saved += 1; }
  function removeCirclesFromOverzoneMerges() {}
`, context);
for (const name of ['formatDistance', 'measurementDistance', 'measurementCross', 'renderMeasurements', 'selectMeasurement', 'placeMeasurement', 'deleteSelection']) {
  const start = source.indexOf(`function ${name}(`);
  assert.notEqual(start, -1, name);
  const end = source.indexOf('\n}', start) + 2;
  vm.runInContext(source.slice(start, end), context);
}
const click = (x, y) => ({ point: { x, y }, target: { closest: () => false } });
context.placeMeasurement(click(10, 20));
assert.equal(context.state.measurements.length, 0);
assert.equal(context.measurementLayer.children.length, 1);
assert.ok(context.measurementLayer.children[0].innerHTML.includes('<path'));
assert.ok(!context.measurementLayer.children[0].innerHTML.includes('<circle'));

context.measurementPreviewPoint = { x: 13, y: 24 };
context.renderMeasurements();
assert.equal(context.state.measurements.length, 0, 'Live preview must never be saved');
assert.match(context.measurementLayer.children[0].innerHTML, /10 m/);

context.placeMeasurement(click(13, 24));
assert.equal(context.state.measurements.length, 1);
assert.equal(context.measurementDistance(context.state.measurements[0]), 10);
assert.equal(context.activeTool, 'select');
assert.equal(context.saved, 1);
assert.equal(context.pendingMeasurementPoint, null);

for (const scale of [1, 10, 50]) {
  context.scale = scale;
  context.renderMeasurements();
  const markup = context.measurementLayer.children[0].innerHTML;
  assert.match(markup, /10 m/);
  assert.ok(markup.includes(`scale(${1 / scale})`), 'Endpoint and label sizes must compensate plan zoom');
  assert.ok(markup.includes('measurement-hit'));
  assert.ok(!markup.includes('<circle'));
}

context.selectMeasurement({ currentTarget: { dataset: { measurementId: 'measurement-test' } }, stopPropagation() {} });
assert.equal(context.selectedMeasurementIds.size, 1);
context.deleteSelection();
assert.equal(context.state.measurements.length, 0);
assert.equal(context.selectedMeasurementIds.size, 0);
assert.equal(context.saved, 2);
console.log('Measurements: two-click creation, live preview, calibrated distance, zoom and selection/deletion passed.');
