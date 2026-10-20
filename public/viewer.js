const $ = (selector) => document.querySelector(selector);
const NS = 'http://www.w3.org/2000/svg';
const shareId = location.hash.slice(1);
const validLink = /^[a-f0-9]{48}$/.test(shareId);
const apiBase = `api/${validLink ? shareId : 'invalid'}/`;
let model = null;
let view = { x: 0, y: 0, width: 420, height: 297 };
let fullView = { ...view };
let mode = 'navigate';
let startPoint = null;
let previewPoint = null;
let measurements = [];
let drag = null;
let frame = null;
let pdfPage = null;
let pdfDocument = null;
let renderTask = null;
let pdfTimer = null;
let pdfGeneration = 0;
let lastPdfView = null;
let cartoucheKey = '';
const pointers = new Map();

async function request(path, options = {}) {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 20000);
  try {
    const response = await fetch(apiBase + path, { credentials: 'same-origin', cache: 'no-store', signal: controller.signal, ...options });
    const body = await response.json();
    if (!response.ok) throw new Error(body.error || 'Consultation indisponible.');
    return body;
  } finally { clearTimeout(timeout); }
}

function clearView() {
  model = null;
  $('#viewer').hidden = true;
  $('#access').hidden = false;
  $('#published-overlay').replaceChildren();
  $('#cartouche').replaceChildren();
  $('#plan-image').removeAttribute('href');
  $('#pdf-layer').replaceChildren();
  $('#local-measures').replaceChildren();
  clearTimeout(pdfTimer);
  pdfGeneration += 1;
  renderTask?.cancel();
  pdfDocument?.destroy();
  pdfDocument = null; pdfPage = null; lastPdfView = null;
  measurements = []; startPoint = null; previewPoint = null;
  cartoucheKey = ''; setMode('navigate');
}

async function openView() {
  model = await request('state');
  fullView = { x: 0, y: 0, width: model.width, height: model.height };
  view = { ...fullView };
  const markup = new DOMParser().parseFromString(model.overlaySvg, 'image/svg+xml').documentElement;
  $('#published-overlay').replaceChildren(...Array.from(markup.childNodes).map((node) => document.importNode(node, true)));
  $('#plan-name').textContent = model.name || 'Plan publié';
  $('#published-date').textContent = `Version publiée le ${new Date(model.publishedAt * 1000).toLocaleString('fr-FR')}`;
  $('#access').hidden = true;
  $('#viewer').hidden = false;
  $('#cartouche').hidden = matchMedia('(max-width:700px)').matches;
  $('#title-toggle').setAttribute('aria-expanded', String(!$('#cartouche').hidden));
  const image = $('#plan-image');
  image.setAttribute('width', model.width);
  image.setAttribute('height', model.height);
  const planUrl = apiBase + `snapshot/${model.revision}/plan`;
  if (model.planType === 'application/pdf') {
    const pdfjs = await import('./assets/pdfjs/pdf.js');
    pdfjs.GlobalWorkerOptions.workerSrc = './assets/pdfjs/pdf.worker.js';
    pdfDocument = await pdfjs.getDocument({ url: planUrl, withCredentials: true, isEvalSupported: false, enableScripting: false }).promise;
    pdfPage = await pdfDocument.getPage(1);
  } else {
    image.setAttribute('href', planUrl);
  }
  image.onerror = () => { $('#viewer-message').textContent = 'Le fond de plan est indisponible. Actualisez ou demandez un nouveau lien.'; };
  fitView();
}

$('#access-form').addEventListener('submit', async (event) => {
  event.preventDefault();
  $('#open-plan').disabled = true;
  $('#access-message').textContent = '';
  try {
    if (!validLink) throw new Error('Le lien de consultation est invalide.');
    await request('unlock', { method: 'POST', headers: { 'Content-Type': 'application/json', 'X-Crobard-View': '1' }, body: JSON.stringify({ code: $('#access-code').value }) });
    $('#access-code').value = '';
    await openView();
  } catch (error) { clearView(); $('#access-message').textContent = error.message; }
  finally { $('#open-plan').disabled = false; }
});

function zoom() { return fullView.width / view.width; }
function fitView() {
  if (!model) return;
  const ratio = $('#stage').clientWidth / Math.max(1, $('#stage').clientHeight);
  const width = Math.max(model.width, model.height * ratio);
  fullView = { x: (model.width - width) / 2, y: (model.height - width / ratio) / 2, width, height: width / ratio };
  view = { ...fullView };
  update();
}
function planPoint(event) {
  const box = $('#drawing').getBoundingClientRect();
  return { x: view.x + (event.clientX - box.left) / box.width * view.width, y: view.y + (event.clientY - box.top) / box.height * view.height };
}
function setZoom(value, point = { x: view.x + view.width / 2, y: view.y + view.height / 2 }) {
  const next = Math.max(1, Math.min(50, value));
  const ratio = zoom() / next;
  view = { x: point.x - (point.x - view.x) * ratio, y: point.y - (point.y - view.y) * ratio, width: view.width * ratio, height: view.height * ratio };
  schedule();
}
function schedule() {
  if (frame !== null) return;
  frame = requestAnimationFrame(() => { frame = null; update(); });
}
function update() {
  if (!model) return;
  $('#drawing').setAttribute('viewBox', `${view.x} ${view.y} ${view.width} ${view.height}`);
  $('#zoom-label').textContent = `${zoom().toLocaleString('fr-FR', { maximumFractionDigits: 1 })}×`;
  $('#published-overlay').querySelectorAll('[data-fixed]').forEach((node) => node.setAttribute('transform', `translate(${node.dataset.x} ${node.dataset.y}) scale(${1 / zoom()})`));
  renderCartouche(); renderMeasurements();
  if (pdfPage) {
    if (lastPdfView) {
      const scale = $('#stage').clientWidth / view.width;
      $('#pdf-layer canvas')?.style.setProperty('transform', `translate(${(lastPdfView.x - view.x) * scale}px,${(lastPdfView.y - view.y) * scale}px) scale(${lastPdfView.width / view.width})`);
    }
    clearTimeout(pdfTimer);
    pdfGeneration += 1;
    renderTask?.cancel();
    pdfTimer = setTimeout(renderPdf, 180);
  }
}

async function renderPdf() {
  if (!pdfPage || !model) return;
  const generation = pdfGeneration;
  const nextView = { ...view };
  const stage = $('#stage');
  const canvas = document.createElement('canvas');
  const ratio = Math.min(devicePixelRatio || 1, 2, 4096 / Math.max(stage.clientWidth, stage.clientHeight));
  canvas.width = Math.ceil(stage.clientWidth * ratio); canvas.height = Math.ceil(stage.clientHeight * ratio);
  canvas.style.width = `${stage.clientWidth}px`; canvas.style.height = `${stage.clientHeight}px`;
  const scale = canvas.width / view.width;
  const base = pdfPage.getViewport({ scale: 1 });
  const fit = Math.min(model.width / base.width, model.height / base.height);
  const offsetX = (model.width - base.width * fit) / 2;
  const offsetY = (model.height - base.height * fit) / 2;
  const task = pdfPage.render({ canvasContext: canvas.getContext('2d', { alpha: false }), viewport: pdfPage.getViewport({ scale: fit * scale }), transform: [1, 0, 0, 1, (offsetX - view.x) * scale, (offsetY - view.y) * scale] });
  renderTask = task;
  try {
    await task.promise;
    if (generation !== pdfGeneration || !model) return;
    $('#pdf-layer').replaceChildren(canvas); lastPdfView = nextView;
  } catch (error) {
    if (error.name !== 'RenderingCancelledException' && generation === pdfGeneration) $('#viewer-message').textContent = 'Affichage PDF interrompu. Actualisez la page.';
  } finally { if (renderTask === task) renderTask = null; }
}

function node(tag, text, parent, className) {
  const element = document.createElement(tag);
  if (text !== null) element.textContent = text;
  if (className) element.className = className;
  parent.append(element); return element;
}
function distance(value) { return !Number.isFinite(value) ? '—' : `${value.toLocaleString('fr-FR', { maximumFractionDigits: 1 })} m`; }
function renderCartouche() {
  const visible = model.zones.filter((z) => z.x + z.radius >= view.x && z.x - z.radius <= view.x + view.width && z.y + z.radius >= view.y && z.y - z.radius <= view.y + view.height);
  const teams = model.teams.filter((team) => !model.zones.length || visible.some((z) => z.team === team.id));
  const lastVisible = new Map();
  visible.forEach((zone) => lastVisible.set(zone.team, zone));
  const key = JSON.stringify([model.revision, teams.map((t) => [t.id, lastVisible.get(t.id)]), view.width, $('#stage').clientWidth]);
  if (key === cartoucheKey) return;
  cartoucheKey = key;
  const panel = $('#cartouche'); panel.replaceChildren();
  const logo = node('img', null, panel); logo.src = model.logo || 'assets/onyx-logo.png'; logo.alt = model.client || 'ONYX';
  if (model.client) node('p', model.client, panel);
  node('h2', 'PLAN DE CONTRÔLE GAMMAGRAPHIQUE', panel);
  node('p', `Date : ${model.date}`, panel); node('p', `Localisation : ${model.location || '—'}`, panel);
  teams.forEach((configured) => {
    const last = lastVisible.get(configured.id);
    const team = Number.isFinite(last?.distance) ? { ...configured, distance: last.distance, threshold: last.threshold, attenuated: last.attenuated } : configured;
    const row = node('div', null, panel, 'team'); row.style.setProperty('--team-color', team.color);
    node('strong', team.company, row);
    node('p', `Tirs : ${team.start.replace(':', 'h')} → ${team.end.replace(':', 'h')}`, row);
    node('p', `${team.isotope} · ${team.activity} ${team.unit} · ${team.attenuated ? 'att. 1/250' : 'sans atténuation'}`, row);
    node('p', `${team.threshold === 'manual' ? 'Balisage manuel' : team.threshold === 25 ? 'Balisage 25 µSv/1h' : 'Balisage 2,5 µSv/h'} : ${distance(team.distance)}`, row);
    if (team.overDistance !== null) node('p', `Surbalisage de sécurité : ${distance(team.overDistance)}`, row);
  });
  const raw = view.width / Math.max(1, $('#stage').clientWidth) * model.metersPerUnit * 30;
  const power = 10 ** Math.floor(Math.log10(raw));
  const segment = (raw / power >= 5 ? 5 : raw / power >= 2 ? 2 : 1) * power;
  node('p', 'Échelle graphique — mètres', panel);
  const bar = node('div', null, panel, 'scale');
  bar.style.width = `${segment * 4 / model.metersPerUnit / view.width * $('#stage').clientWidth}px`;
  for (let i = 0; i < 4; i++) node('span', null, bar);
  node('p', `0 — ${distance(segment * 4)}`, panel);
  [['Réalisé par', model.author], ['Validé par', model.validator]].forEach(([label, person]) => {
    if (!person) return;
    const row = node('div', null, panel, 'person');
    node('p', `${label} : ${person.name || '—'}`, row); node('p', `Fonction : ${person.role || '—'}`, row);
    if (person.signature) { const image = node('img', null, row); image.src = person.signature; image.alt = `Signature — ${label.toLowerCase()}`; }
  });
}

function renderMeasurements() {
  const layer = $('#local-measures'); layer.replaceChildren();
  const unit = view.width / Math.max(1, $('#stage').clientWidth);
  function svg(tag, attrs, text) {
    const element = document.createElementNS(NS, tag);
    Object.entries(attrs).forEach(([key, value]) => element.setAttribute(key, value));
    if (text) element.textContent = text;
    layer.append(element); return element;
  }
  function cross(p) { const r = 4 * unit; svg('path', { d: `M${p.x-r} ${p.y-r}l${2*r} ${2*r}m${-2*r} 0l${2*r} ${-2*r}` }); }
  const items = [...measurements];
  if (startPoint && previewPoint) items.push([startPoint, previewPoint]);
  items.forEach(([a, b]) => {
    svg('line', { x1: a.x, y1: a.y, x2: b.x, y2: b.y }); cross(a); cross(b);
    svg('text', { x: (a.x+b.x)/2, y: (a.y+b.y)/2 - 12*unit, 'font-size': 13*unit, 'stroke-width': 3*unit }, distance(Math.hypot(b.x-a.x,b.y-a.y)*model.metersPerUnit));
  });
  if (startPoint) cross(startPoint);
  $('#clear-measures').hidden = !measurements.length && !startPoint;
}
function setMode(next) {
  mode = next; startPoint = null; previewPoint = null;
  $('#stage').classList.toggle('measuring', mode === 'measure');
  $('#measure').setAttribute('aria-pressed', String(mode === 'measure'));
  $('#hint').textContent = mode === 'measure' ? 'Choisissez deux points. Mesures temporaires, sans modification du plan.' : 'Glissez pour déplacer. Molette ou boutons pour zoomer.';
  if (model) renderMeasurements();
}

$('#zoom-in').onclick = () => setZoom(zoom() + .5);
$('#zoom-out').onclick = () => setZoom(zoom() - .5);
$('#fit').onclick = fitView;
$('#measure').onclick = () => setMode(mode === 'measure' ? 'navigate' : 'measure');
$('#clear-measures').onclick = () => { measurements = []; setMode('navigate'); };
$('#title-toggle').onclick = () => { $('#cartouche').hidden = !$('#cartouche').hidden; $('#title-toggle').setAttribute('aria-expanded', String(!$('#cartouche').hidden)); };
$('#close-view').onclick = async () => {
  try { await request('logout', { method: 'POST', headers: { 'X-Crobard-View': '1' } }); clearView(); }
  catch { $('#viewer-message').textContent = 'Fermeture impossible. Réessayez ou fermez cet onglet.'; }
};
$('#drawing').addEventListener('wheel', (event) => { event.preventDefault(); setZoom(zoom() * (event.deltaY < 0 ? 1.15 : 1/1.15), planPoint(event)); }, { passive: false });
$('#drawing').addEventListener('pointerdown', (event) => {
  if (event.button !== 0) return;
  pointers.set(event.pointerId, { x: event.clientX, y: event.clientY });
  $('#drawing').setPointerCapture(event.pointerId);
  drag = { x: event.clientX, y: event.clientY, view: { ...view }, moved: pointers.size > 1 };
});
$('#drawing').addEventListener('pointermove', (event) => {
  if (mode === 'measure' && startPoint && !drag) { previewPoint = planPoint(event); schedule(); }
  if (!pointers.has(event.pointerId)) return;
  const before = [...pointers.values()];
  pointers.set(event.pointerId, { x: event.clientX, y: event.clientY });
  if (pointers.size === 2) {
    const after = [...pointers.values()];
    const oldDistance = Math.hypot(before[0].x-before[1].x,before[0].y-before[1].y);
    const newDistance = Math.hypot(after[0].x-after[1].x,after[0].y-after[1].y);
    if (oldDistance > 0 && drag) { setZoom(zoom()*newDistance/oldDistance, planPoint(event)); drag.moved = true; }
  } else if (drag) {
    const dx = event.clientX-drag.x, dy = event.clientY-drag.y;
    if (Math.hypot(dx,dy)>4) drag.moved = true;
    view.x = drag.view.x-dx/$('#stage').clientWidth*view.width;
    view.y = drag.view.y-dy/$('#stage').clientHeight*view.height;
    schedule();
  }
});
$('#drawing').addEventListener('pointerup', (event) => {
  pointers.delete(event.pointerId);
  if (drag && !drag.moved && mode === 'measure') {
    const point = planPoint(event);
    if (!startPoint) { startPoint = point; previewPoint = null; }
    else if (Math.hypot(point.x-startPoint.x,point.y-startPoint.y)>1e-8) { measurements.push([startPoint,point]); setMode('navigate'); }
    renderMeasurements();
  }
  drag = null;
  if (pointers.size === 1) {
    const [point] = pointers.values();
    drag = { x: point.x, y: point.y, view: { ...view }, moved: true };
  }
});
$('#drawing').addEventListener('pointercancel', () => { drag = null; pointers.clear(); });
document.addEventListener('keydown', (event) => { if (event.key === 'Escape') setMode('navigate'); });
new ResizeObserver(() => { if (model) fitView(); }).observe($('#stage'));
setInterval(async () => {
  if (!model) return;
  try { await request('status'); }
  catch { clearView(); $('#access-message').textContent = 'Accès interrompu ou expiré. Vérifiez votre connexion puis saisissez à nouveau le code.'; }
}, 60000);
if (validLink) openView().catch((error) => { clearView(); $('#access-message').textContent = error.message; });
else { $('#access-message').textContent = 'Le lien de consultation est invalide.'; $('#open-plan').disabled = true; }
