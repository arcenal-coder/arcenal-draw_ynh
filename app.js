const NS = 'http://www.w3.org/2000/svg';
const STORAGE_KEY = 'arcenal-draw-poc-v2';
const ARCHIVE_KEY = 'arcenal-draw-export-archives-v1';
const DOSE_CONSTANTS = { 'Se-75': 55000, 'Ir-192': 130000 };
const COLORS = ['#e2444f', '#287dc0', '#2d9960', '#ef922f', '#7544a8', '#00838f', '#c45100', '#596b23', '#b23a7a', '#536d8f'];
const LETTERS = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J'];

const homeView = document.querySelector('#home-view');
const editorView = document.querySelector('#editor-view');
const sheet = document.querySelector('#sheet');
const sheetFrame = document.querySelector('#sheet-frame');
const pdfLayer = document.querySelector('#pdf-layer');
const sheetBackground = document.querySelector('#sheet-background');
const sheetMargin = document.querySelector('#sheet-margin');
const mapLayer = document.querySelector('#map-layer');
const planPreview = document.querySelector('#plan-preview');
const overzoneLayer = document.querySelector('#overzone-layer');
const zoneLayer = document.querySelector('#zone-layer');
const impactLayer = document.querySelector('#impact-layer');
const signalLayer = document.querySelector('#signal-layer');
const measurementLayer = document.querySelector('#measurement-layer');
const titleBlock = document.querySelector('#title-block');
const circlePanel = document.querySelector('#circle-panel');
const selectionPanel = document.querySelector('#selection-panel');
const signalPanel = document.querySelector('#signal-panel');
const canvasHint = document.querySelector('#canvas-hint');
const calibrationDialog = document.querySelector('#calibration-dialog');
const settingsDialog = document.querySelector('#settings-dialog');
const importStatus = document.querySelector('#import-status');
const importProgressWrap = document.querySelector('#import-progress-wrap');
const importProgress = document.querySelector('#import-progress');
const importProgressLabel = document.querySelector('#import-progress-label');

let activeTool = 'select';
let selectedCircleIds = new Set();
let selectedMergeIds = new Set();
let selectedSignalIds = new Set();
let selectedOverzoneKeys = new Set();
let selectedMeasurementIds = new Set();
let selectedSignalType = 'roadblock';
let pendingMeasurementPoint = null;
let pendingFileName = '';
let pendingPlanImport = null;
let panSession = null;
let serverSaveTimer = null;
let serverProjects = [];
let serverArchives = [];
let reusablePlans = [];
let pdfDocument = null;
let pdfPage = null;
let pdfSourceKey = '';
let pdfRenderTimer = null;
let pdfRenderGeneration = 0;
const pdfTileCache = new Map();

function uid(prefix) {
  return `${prefix}-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 7)}`;
}

function defaultIntervention(index) {
  const examples = [
    { company: 'Société 1', isotope: 'Ir-192', activity: 40, unit: 'Ci' },
    { company: 'Société 2', isotope: 'Se-75', activity: 30, unit: 'Ci' },
    { company: 'Société 3', isotope: 'Ir-192', activity: 0.7, unit: 'TBq' },
    { company: 'Société 4', isotope: 'Se-75', activity: 0.5, unit: 'TBq' },
    { company: 'Société 5', isotope: 'Ir-192', activity: 20, unit: 'Ci' },
  ];
  const example = examples[index] || { company: `Société ${index + 1}`, isotope: index % 2 ? 'Se-75' : 'Ir-192', activity: 20, unit: 'Ci' };
  return { id: uid('intervention'), code: LETTERS[index], color: COLORS[index], attenuation: true, scheduleStart: '00:00', scheduleEnd: '04:00', overEnabled: false, overDistance: 50, overStyle: 'dashed', overColor: COLORS[index], overWidth: 1.2, ...example };
}

function freshState(name = 'Plan de balisage — U662') {
  return {
    projectId: uid('project'),
    name,
    baseName: 'Unité U662 — Rack 600',
    location: 'Unité U662 — Rack 600',
    orientation: 'landscape',
    planZoom: 100,
    panX: 0,
    panY: 0,
    planDate: new Date().toISOString().slice(0, 10),
    sheetMargin: 5,
    zoneOpacity: 25,
    showImpactLabels: true,
    theme: 'system',
    logo: null,
    client: '',
    author: { name: '', role: '', signature: null },
    validatorEnabled: false,
    validator: { name: '', role: '', signature: null },
    calibration: { sourceUnit: 'm', metersPerNativeUnit: 1, method: 'file' },
    interventions: [defaultIntervention(0)],
    circles: [],
    merges: [],
    signals: [],
    measurements: [],
    suppressedOverzones: [],
    updatedAt: new Date().toISOString(),
  };
}

let state = freshState();

function activityTbq(intervention) {
  const value = Number(intervention.activity) || 0;
  return intervention.unit === 'Ci' ? value * 0.037 : value;
}

function radiusMeters(intervention, threshold, attenuated) {
  const factor = attenuated ? 250 : 1;
  return Math.sqrt((DOSE_CONSTANTS[intervention.isotope] * activityTbq(intervention)) / (Number(threshold) * factor));
}

function formatDistance(value) {
  if (!Number.isFinite(value)) return '—';
  return `${value < 10 ? value.toFixed(1) : Math.round(value)} m`;
}

function formatTime(value) {
  return String(value || '--:--').replace(':', 'h');
}

function escapeText(value) {
  return String(value).replace(/[&<>"']/g, (character) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[character]);
}

function saveState() {
  state.updatedAt = new Date().toISOString();
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
  } catch (error) {
    console.warn('Sauvegarde locale indisponible', error);
  }
  document.querySelector('#save-status').textContent = 'Enregistré automatiquement';
  renderRecentProjects();
  scheduleServerSave();
}

function serverAvailable() {
  return ['http:', 'https:'].includes(window.location.protocol);
}

function apiUrl(path) {
  const basePath = window.location.pathname.endsWith('/') ? window.location.pathname : window.location.pathname.replace(/[^/]*$/, '');
  return `${basePath}api/${path.replace(/^\//, '')}`;
}

async function apiRequest(path, options = {}) {
  const response = await fetch(apiUrl(path), { credentials: 'same-origin', ...options });
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(payload.error || `Erreur serveur ${response.status}`);
  return payload;
}

function scheduleServerSave() {
  if (!serverAvailable() || editorView.hidden) return;
  clearTimeout(serverSaveTimer);
  serverSaveTimer = setTimeout(async () => {
    state.projectId ||= uid('project');
    try {
      await apiRequest(`projects/${encodeURIComponent(state.projectId)}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(state),
      });
      document.querySelector('#save-status').textContent = 'Enregistré sur le serveur';
    } catch (error) {
      document.querySelector('#save-status').textContent = 'Sauvegarde locale — serveur indisponible';
    }
  }, 700);
}

function loadArchives() {
  try { return JSON.parse(localStorage.getItem(ARCHIVE_KEY)) || []; } catch (error) { return []; }
}

function searchableDate(value) {
  const date = new Date(value);
  return `${date.toLocaleDateString('fr-FR')} ${date.toLocaleDateString('fr-FR', { dateStyle: 'long' })} ${value || ''}`.toLowerCase();
}

function renderArchives(source = null) {
  const container = document.querySelector('#export-archives');
  const archives = source || loadArchives();
  const search = document.querySelector('#archive-search');
  if (!archives.length) {
    container.innerHTML = '<div class="card-grid"><article class="plan-card"><div class="plan-thumb"><span>PDF</span></div><div class="plan-card-body"><strong>Aucun export archivé</strong><span>Chaque export PDF créera automatiquement une copie ici.</span></div></article></div>';
    search.hidden = true;
    return;
  }
  const normalized = archives.map((archive) => ({ ...archive, exportName: archive.exportName || archive.export_name, exportedAt: archive.exportedAt || archive.created_at, server: Boolean(archive.created_at) }));
  const allDays = [...new Set(normalized.map((archive) => archive.exportedAt.slice(0, 10)))];
  search.hidden = allDays.length <= 3;
  const query = search.value.trim().toLowerCase();
  const visibleDays = query ? allDays : allDays.slice(0, 3);
  const filtered = normalized.filter((archive) => visibleDays.includes(archive.exportedAt.slice(0, 10)) && (!query || `${archive.exportName} ${searchableDate(archive.exportedAt)}`.toLowerCase().includes(query)));
  container.innerHTML = visibleDays.map((day) => {
    const items = filtered.filter((archive) => archive.exportedAt.startsWith(day));
    if (!items.length) return '';
    const cards = items.map((archive) => `<article class="plan-card"><div class="plan-thumb"><span>PDF</span></div><div class="plan-card-body"><strong>${escapeText(archive.exportName)}</strong><span>${new Date(archive.exportedAt).toLocaleString('fr-FR', { dateStyle: 'short', timeStyle: 'short' })}</span><button type="button" data-open-archive="${archive.id}" data-server="${archive.server}">Ouvrir l’archive</button></div></article>`).join('');
    return `<section class="archive-date-group"><h3>${new Date(`${day}T12:00:00`).toLocaleDateString('fr-FR', { dateStyle: 'long' })}</h3><div class="card-grid">${cards}</div></section>`;
  }).join('') || '<p class="empty-search">Aucun export ne correspond à cette recherche.</p>';
  container.querySelectorAll('[data-open-archive]').forEach((button) => button.addEventListener('click', async () => {
    const archive = normalized.find((item) => item.id === button.dataset.openArchive);
    if (!archive) return;
    state = archive.server ? (await apiRequest(`archives/${encodeURIComponent(archive.id)}`)).state : JSON.parse(JSON.stringify(archive.state));
    openEditor();
  }));
}

function loadSavedState() {
  try {
    const saved = JSON.parse(localStorage.getItem(STORAGE_KEY));
    if (saved?.interventions && saved?.circles) return saved;
  } catch (error) {
    console.warn('Projet local illisible', error);
  }
  return null;
}

function renderRecentProjects(source = null) {
  const container = document.querySelector('#recent-projects');
  const search = document.querySelector('#project-search');
  if (source) {
    search.hidden = source.length <= 3;
    const query = search.value.trim().toLowerCase();
    const projects = (query ? source.filter((project) => `${project.name} ${project.location || ''} ${searchableDate(project.updated_at)}`.toLowerCase().includes(query)) : source.slice(0, 3));
    container.innerHTML = projects.map((project) => `<article class="plan-card"><div class="plan-thumb thumb-u662"><span>☁</span></div><div class="plan-card-body"><strong>${escapeText(project.name)}</strong><span>${escapeText(project.location || 'Sans localisation')} · ${new Date(project.updated_at).toLocaleString('fr-FR', { dateStyle: 'short', timeStyle: 'short' })}</span><button type="button" data-server-project="${project.id}">Ouvrir le projet</button></div></article>`).join('') || '<p class="empty-search">Aucun projet ne correspond à cette recherche.</p>';
    container.querySelectorAll('[data-server-project]').forEach((button) => button.addEventListener('click', async () => {
      state = (await apiRequest(`projects/${encodeURIComponent(button.dataset.serverProject)}`)).state;
      openEditor();
    }));
    return;
  }
  const saved = loadSavedState();
  if (!saved) {
    container.innerHTML = '<article class="plan-card"><div class="plan-thumb"><span>—</span></div><div class="plan-card-body"><strong>Aucun projet enregistré</strong><span>Créez un projet à partir d’une base.</span></div></article>';
    return;
  }
  const date = new Date(saved.updatedAt).toLocaleString('fr-FR', { dateStyle: 'short', timeStyle: 'short' });
  container.innerHTML = `<article class="plan-card"><div class="plan-thumb thumb-u662"><span>${saved.circles.length}</span></div><div class="plan-card-body"><strong>${escapeText(saved.name)}</strong><span>${saved.circles.length} zone(s) · ${date}</span><button id="open-saved-project">Ouvrir le projet</button></div></article>`;
  document.querySelector('#open-saved-project').addEventListener('click', () => { state = saved; openEditor(); });
}

function renderReusablePlans(plans) {
  const container = document.querySelector('#exploitable-plans');
  if (!plans.length) {
    container.innerHTML = '<article class="plan-card"><div class="plan-thumb"><span>—</span></div><div class="plan-card-body"><strong>Aucun plan importé</strong><span>Vos plans convertis apparaîtront ici.</span></div></article>';
    return;
  }
  container.innerHTML = plans.map((plan) => `<article class="plan-card"><div class="plan-thumb"><span>${escapeText(plan.extension.replace('.', '').toUpperCase())}</span></div><div class="plan-card-body"><strong>${escapeText(plan.name)}</strong><span>${escapeText(plan.conversion)} · ${new Date(plan.createdAt).toLocaleDateString('fr-FR')}</span><button type="button" data-reuse-plan="${plan.id}">Créer un projet</button></div></article>`).join('');
  container.querySelectorAll('[data-reuse-plan]').forEach((button) => button.addEventListener('click', () => {
    pendingPlanImport = plans.find((plan) => plan.id === button.dataset.reusePlan);
    if (pendingPlanImport) openCalibration(pendingPlanImport.name);
  }));
}

async function refreshServerLibrary() {
  if (!serverAvailable()) return;
  try {
    const [projectData, archiveData, planData] = await Promise.all([apiRequest('projects'), apiRequest('archives'), apiRequest('imports')]);
    serverProjects = projectData.projects || [];
    serverArchives = archiveData.archives || [];
    reusablePlans = planData.plans || [];
    if (serverProjects.length) renderRecentProjects(serverProjects);
    if (serverArchives.length) renderArchives(serverArchives);
    renderReusablePlans(reusablePlans);
  } catch (error) {
    console.warn('Bibliothèque serveur indisponible', error);
  }
}

function openEditor() {
  state.signals ||= [];
  state.measurements ||= [];
  state.projectId ||= uid('project');
  state.panX ||= 0;
  state.panY ||= 0;
  state.planDate ||= new Date().toISOString().slice(0, 10);
  state.location ??= state.baseName || '';
  state.sheetMargin ??= 5;
  state.zoneOpacity ??= 25;
  state.showImpactLabels ??= true;
  state.client ??= '';
  state.theme ??= 'system';
  state.author ||= { name: '', role: '', signature: null };
  state.validatorEnabled ??= false;
  state.validator ||= { name: '', role: '', signature: null };
  state.suppressedOverzones ||= [];
  state.interventions.forEach((item, index) => {
    item.scheduleStart ??= '00:00';
    item.scheduleEnd ??= '04:00';
    item.overEnabled ??= false;
    item.overDistance ??= 50;
    item.overStyle ??= 'dashed';
    item.overColor ??= item.color || COLORS[index];
    item.overWidth ??= 1.2;
  });
  homeView.hidden = true;
  editorView.hidden = false;
  selectedCircleIds.clear();
  selectedMergeIds.clear();
  selectedSignalIds.clear();
  selectedOverzoneKeys.clear();
  selectedMeasurementIds.clear();
  pendingMeasurementPoint = null;
  document.querySelector('#project-name').textContent = state.name;
  document.querySelector('#orientation-select').value = state.orientation;
  document.querySelector('#plan-zoom').value = state.planZoom;
  document.querySelector('#plan-date').value = state.planDate;
  document.querySelector('#plan-location').value = state.location;
  applyTheme(state.theme);
  renderAll();
  renderLogoSettings();
  setTool('select');
}

function openHome() {
  saveState();
  editorView.hidden = true;
  homeView.hidden = false;
  renderRecentProjects();
  renderArchives();
  refreshServerLibrary();
}

function applyTheme(theme) {
  const normalized = ['light', 'dark'].includes(theme) ? theme : 'system';
  document.documentElement.dataset.theme = normalized;
  document.documentElement.style.colorScheme = normalized === 'system' ? 'light dark' : normalized;
  const selector = document.querySelector('#settings-theme');
  if (selector) selector.value = normalized;
}

function setOrientation(orientation) {
  state.orientation = orientation;
  const portrait = orientation === 'portrait';
  const width = portrait ? 297 : 420;
  const height = portrait ? 420 : 297;
  sheet.setAttribute('viewBox', `0 0 ${width} ${height}`);
  sheet.setAttribute('aria-label', `Feuille A3 ${portrait ? 'portrait' : 'paysage'}`);
  sheetBackground.setAttribute('width', width);
  sheetBackground.setAttribute('height', height);
  sheetMargin.setAttribute('x', state.sheetMargin);
  sheetMargin.setAttribute('y', state.sheetMargin);
  sheetMargin.setAttribute('width', width - state.sheetMargin * 2);
  sheetMargin.setAttribute('height', height - state.sheetMargin * 2);
  planPreview.setAttribute('width', width);
  planPreview.setAttribute('height', height);
  sheetFrame.classList.toggle('portrait', portrait);
  sheetFrame.style.setProperty('--sheet-width', `${width}mm`);
  sheetFrame.style.setProperty('--sheet-height', `${height}mm`);
  document.documentElement.style.setProperty('--sheet-width', `${width}mm`);
  document.documentElement.style.setProperty('--sheet-height', `${height}mm`);
  document.querySelector('#print-page-style').textContent = `@page { size: A3 ${orientation}; margin: 0; }`;
  renderTitleBlock();
  if (state.planFile?.previewType === 'application/pdf') queuePdfRender(0);
}

function mapScale() {
  return state.planZoom / 100;
}

function updateMapTransform() {
  const scale = mapScale();
  mapLayer.setAttribute('transform', `translate(${150 + state.panX} ${135 + state.panY}) scale(${scale}) translate(-150 -135)`);
  document.querySelector('#plan-zoom-value').textContent = `${state.planZoom} %`;
  if (state.planFile?.previewType === 'application/pdf') queuePdfRender();
}

function clearPdfRenderer() {
  pdfRenderGeneration += 1;
  pdfDocument = null;
  pdfPage = null;
  pdfSourceKey = '';
  pdfTileCache.clear();
  pdfLayer.replaceChildren();
  pdfLayer.hidden = true;
}

function trimPdfTileCache() {
  while (pdfTileCache.size > 28) pdfTileCache.delete(pdfTileCache.keys().next().value);
}

async function ensurePdfPage(sourceKey) {
  if (pdfSourceKey === sourceKey && pdfPage) return pdfPage;
  clearPdfRenderer();
  pdfSourceKey = sourceKey;
  const pdfjs = await import('./assets/pdfjs/pdf.js');
  pdfjs.GlobalWorkerOptions.workerSrc = './assets/pdfjs/pdf.worker.js';
  pdfDocument = await pdfjs.getDocument({ url: sourceKey, withCredentials: true, rangeChunkSize: 262144 }).promise;
  pdfPage = await pdfDocument.getPage(1);
  return pdfPage;
}

async function renderPdfTiles() {
  const sourceKey = state.planFile?.previewType === 'application/pdf' ? apiUrl(state.planFile.previewUrl) : '';
  if (!sourceKey || editorView.hidden) return;
  const generation = ++pdfRenderGeneration;
  try {
    const page = await ensurePdfPage(sourceKey);
    if (generation !== pdfRenderGeneration && pdfSourceKey !== sourceKey) return;
    const frameWidth = sheetFrame.clientWidth;
    const frameHeight = sheetFrame.clientHeight;
    if (!frameWidth || !frameHeight) return;
    const portrait = state.orientation === 'portrait';
    const logicalWidth = portrait ? 297 : 420;
    const logicalHeight = portrait ? 420 : 297;
    const cssX = frameWidth / logicalWidth;
    const cssY = frameHeight / logicalHeight;
    const baseViewport = page.getViewport({ scale: 1 });
    const fit = Math.min(logicalWidth / baseViewport.width, logicalHeight / baseViewport.height);
    const baseWidth = baseViewport.width * fit;
    const baseHeight = baseViewport.height * fit;
    const baseX = (logicalWidth - baseWidth) / 2;
    const baseY = (logicalHeight - baseHeight) / 2;
    const zoom = mapScale();
    const logicalX = 150 + state.panX + zoom * (baseX - 150);
    const logicalY = 135 + state.panY + zoom * (baseY - 135);
    const displayWidth = baseWidth * zoom * cssX;
    const displayHeight = baseHeight * zoom * cssY;
    const left = logicalX * cssX;
    const top = logicalY * cssY;
    const visibleLeft = Math.max(0, -left);
    const visibleTop = Math.max(0, -top);
    const visibleRight = Math.min(displayWidth, frameWidth - left);
    const visibleBottom = Math.min(displayHeight, frameHeight - top);
    pdfLayer.hidden = false;
    pdfLayer.replaceChildren();
    if (visibleRight <= visibleLeft || visibleBottom <= visibleTop) return;

    const pixelRatio = Math.min(window.devicePixelRatio || 1, 2);
    const renderScale = (displayWidth / baseViewport.width) * pixelRatio;
    const viewport = page.getViewport({ scale: renderScale });
    const tilePixels = 768;
    const tileCss = tilePixels / pixelRatio;
    const firstColumn = Math.floor(visibleLeft / tileCss);
    const lastColumn = Math.floor((visibleRight - 0.01) / tileCss);
    const firstRow = Math.floor(visibleTop / tileCss);
    const lastRow = Math.floor((visibleBottom - 0.01) / tileCss);
    const scaleKey = renderScale.toFixed(4);
    const renders = [];
    for (let row = firstRow; row <= lastRow; row += 1) {
      for (let column = firstColumn; column <= lastColumn; column += 1) {
        const tileX = column * tileCss;
        const tileY = row * tileCss;
        const cssWidth = Math.min(tileCss, displayWidth - tileX);
        const cssHeight = Math.min(tileCss, displayHeight - tileY);
        const key = `${sourceKey}|${scaleKey}|${column}|${row}`;
        let canvas = pdfTileCache.get(key);
        if (!canvas) {
          canvas = document.createElement('canvas');
          canvas.width = Math.ceil(cssWidth * pixelRatio);
          canvas.height = Math.ceil(cssHeight * pixelRatio);
          pdfTileCache.set(key, canvas);
          const context = canvas.getContext('2d', { alpha: false });
          renders.push(page.render({ canvasContext: context, viewport, transform: [1, 0, 0, 1, -Math.round(tileX * pixelRatio), -Math.round(tileY * pixelRatio)] }).promise);
        } else {
          pdfTileCache.delete(key);
          pdfTileCache.set(key, canvas);
        }
        canvas.style.left = `${((left + tileX) / frameWidth) * 100}%`;
        canvas.style.top = `${((top + tileY) / frameHeight) * 100}%`;
        canvas.style.width = `${(cssWidth / frameWidth) * 100}%`;
        canvas.style.height = `${(cssHeight / frameHeight) * 100}%`;
        pdfLayer.append(canvas);
      }
    }
    trimPdfTileCache();
    await Promise.all(renders);
    if (generation !== pdfRenderGeneration) queuePdfRender(0);
  } catch (error) {
    console.error('Affichage PDF impossible', error);
    document.querySelector('#save-status').textContent = `Affichage PDF impossible : ${error.message}`;
  }
}

function queuePdfRender(delay = 45) {
  clearTimeout(pdfRenderTimer);
  pdfRenderTimer = setTimeout(renderPdfTiles, delay);
}

function setPlanImageVisible(visible) {
  planPreview.hidden = !visible;
  planPreview.style.display = visible ? '' : 'none';
}

function fallbackToOriginalPdf() {
  if (state.planFile?.extension !== '.pdf' || !state.planFile.originalUrl) return;
  state.planFile.previewType = 'application/pdf';
  state.planFile.previewUrl = state.planFile.originalUrl;
  setPlanImageVisible(false);
  planPreview.removeAttribute('href');
  queuePdfRender(0);
  document.querySelector('#save-status').textContent = 'SVG indisponible — affichage du PDF original';
  saveState();
}

planPreview.addEventListener('error', fallbackToOriginalPdf);

function renderPlanPreview() {
  const previewPath = state.planFile?.previewUrl;
  if (!previewPath) {
    clearPdfRenderer();
    sheetBackground.setAttribute('fill', '#fff');
    setPlanImageVisible(false);
    planPreview.removeAttribute('href');
    return;
  }
  sheetBackground.setAttribute('fill', 'none');
  if (state.planFile.previewType === 'application/pdf') {
    setPlanImageVisible(false);
    planPreview.removeAttribute('href');
    queuePdfRender(0);
    return;
  }
  clearPdfRenderer();
  planPreview.setAttribute('href', apiUrl(previewPath));
  setPlanImageVisible(true);
}

function niceScaleSegment(rawValue) {
  const exponent = Math.floor(Math.log10(rawValue));
  const fraction = rawValue / (10 ** exponent);
  const nice = fraction >= 5 ? 5 : fraction >= 2 ? 2 : 1;
  return nice * (10 ** exponent);
}

function personRowMarkup(label, person, y, width) {
  const signature = person.signature?.dataUrl ? `<image href="${person.signature.dataUrl}" x="55" y="1" width="24" height="12" preserveAspectRatio="xMidYMid meet"/>` : person.signature?.type === 'application/pdf' ? '<text x="67" y="8" text-anchor="middle" font-size="2.1">SIGNATURE PDF</text>' : '';
  return `<g transform="translate(0 ${y})"><rect width="${width}" height="15" fill="#fff" stroke="#17212b" stroke-width=".32"/><text x="3" y="5" font-size="2.45" font-weight="700">${label} : ${escapeText(person.name || '—')}</text><text x="3" y="10" font-size="2.25">Fonction : ${escapeText(person.role || '—')}</text>${signature}</g>`;
}

function circleIsVisible(circle) {
  const scale = mapScale();
  const sheetWidth = state.orientation === 'portrait' ? 297 : 420;
  const sheetHeight = state.orientation === 'portrait' ? 420 : 297;
  const x = 150 + state.panX + scale * (circle.cx - 150);
  const y = 135 + state.panY + scale * (circle.cy - 135);
  const radius = circle.radius * scale;
  return x + radius >= 0 && x - radius <= sheetWidth && y + radius >= 0 && y - radius <= sheetHeight;
}

function visibleInterventionsForTitleBlock() {
  if (!state.circles.length) return state.interventions;
  const visibleIds = new Set(state.circles.filter(circleIsVisible).map((circle) => circle.interventionId));
  return state.interventions.filter((item) => visibleIds.has(item.id));
}

function renderTitleBlock() {
  const visibleInterventions = visibleInterventionsForTitleBlock();
  const count = visibleInterventions.length;
  const width = 82;
  const headerHeight = 31;
  const footerHeight = 20;
  const peopleHeight = 15 + (state.validatorEnabled ? 15 : 0);
  const sheetHeight = state.orientation === 'portrait' ? 420 : 297;
  const accessoryHeight = state.logo || state.client ? 19 : 0;
  const desiredRowHeight = visibleInterventions.some((item) => item.overEnabled) ? 27 : 23;
  const availableRowsHeight = sheetHeight - state.sheetMargin * 2 - accessoryHeight - headerHeight - footerHeight - peopleHeight;
  const rowHeight = count ? Math.min(desiredRowHeight, availableRowsHeight / count) : 0;
  const height = headerHeight + rowHeight * count + footerHeight + peopleHeight;
  const sheetWidth = state.orientation === 'portrait' ? 297 : 420;
  titleBlock.setAttribute('transform', `translate(${sheetWidth - width - state.sheetMargin} ${sheetHeight - height - state.sheetMargin})`);
  const scale = mapScale();
  const segmentMeters = niceScaleSegment(12 / scale);
  const segmentWidth = segmentMeters * scale;
  const scaleTotal = segmentWidth * 4;
  const displayDate = state.planDate ? new Date(`${state.planDate}T12:00:00`).toLocaleDateString('fr-FR') : '—';
  const rows = visibleInterventions.map((item, index) => {
    const y = headerHeight + index * rowHeight;
    const placed = [...state.circles].reverse().find((circle) => circle.interventionId === item.id && circleIsVisible(circle));
    const threshold = placed?.threshold ?? item.displayThreshold ?? 2.5;
    const attenuated = placed?.attenuated ?? item.attenuation;
    const distance = placed?.radius ?? radiusMeters(item, threshold === 'manual' ? 2.5 : threshold, attenuated);
    const thresholdLabel = threshold === 'manual' ? 'Balisage manuel' : threshold === 25 ? 'Balisage 25 µSv/1h' : 'Balisage 2,5 µSv/h';
    const compact = rowHeight < 24;
    const positions = compact ? { company: 4.2, time: 7.7, source: 11.2, marking: item.overEnabled ? 14.8 : rowHeight - 2.5, over: rowHeight - 1.1 } : { company: 5.5, time: 9.7, source: 13.8, marking: 18.2, over: 24.8 };
    const font = compact ? 1.85 : 2.25;
    const overMarkup = item.overEnabled ? `<line x1="10" y1="${positions.over - .7}" x2="15" y2="${positions.over - .7}" stroke="${item.overColor}" stroke-width="${Math.max(0.3, Math.min(1.4, Number(item.overWidth) || 1.2))}" ${item.overStyle === 'dashed' ? 'stroke-dasharray="1.2 .8"' : ''}/><text x="17" y="${positions.over}" font-size="${compact ? 1.7 : 2.1}">Surbalisage de sécurité : ${formatDistance(Number(item.overDistance))}</text>` : '';
    return `<g transform="translate(0 ${y})"><rect width="${width}" height="${rowHeight}" fill="#fff" stroke="#26353e" stroke-width=".32"/><rect x="2.5" y="2" width="5" height="${Math.max(4, rowHeight - 4)}" rx=".6" fill="${item.color}"/><text x="10" y="${positions.company}" font-size="${compact ? 2.1 : 2.7}" font-weight="700">${item.code} · ${escapeText(item.company)}</text><text x="10" y="${positions.time}" font-size="${font}">Tirs : ${formatTime(item.scheduleStart)} → ${formatTime(item.scheduleEnd)}</text><text x="10" y="${positions.source}" font-size="${font}">${item.isotope} · ${Number(item.activity).toLocaleString('fr-FR')} ${item.unit} · ${attenuated ? 'att. 1/250' : 'sans att.'}</text><text x="10" y="${positions.marking}" font-size="${font}" font-weight="700">${thresholdLabel} : ${formatDistance(distance)}</text>${overMarkup}</g>`;
  }).join('');
  const bars = Array.from({ length: 4 }, (_, index) => `<rect x="${index * segmentWidth}" width="${segmentWidth}" height="3.5" fill="${index % 2 ? '#fff' : '#17212b'}" stroke="#17212b" stroke-width=".3"/>`).join('');
  const peopleY = headerHeight + rowHeight * count + footerHeight;
  const peopleRows = personRowMarkup('Réalisé par', state.author, peopleY, width) + (state.validatorEnabled ? personRowMarkup('Validé par', state.validator, peopleY + 15, width) : '');
  const clientLabel = escapeText(state.client || 'CLIENT');
  const logoMarkup = state.logo?.dataUrl ? `<g transform="translate(0 -19)"><image href="${state.logo.dataUrl}" x="0" y="0" width="24" height="16" preserveAspectRatio="xMinYMid meet"/><text x="28" y="10" font-size="3.4" font-weight="700">${clientLabel}</text></g>` : state.logo?.type === 'application/pdf' ? `<g transform="translate(0 -19)"><text x="0" y="7" font-size="2.4" font-weight="700">LOGO PDF</text><text x="28" y="7" font-size="3.4" font-weight="700">${clientLabel}</text></g>` : state.client ? `<text x="0" y="-7" font-size="3.4" font-weight="700">${clientLabel}</text>` : '';
  titleBlock.innerHTML = `${logoMarkup}<rect width="${width}" height="${height}" fill="#fff" stroke="#17212b" stroke-width=".65"/><rect width="${width}" height="13" fill="#edf1f3" stroke="#17212b" stroke-width=".65"/><path d="M0 22H${width}M0 31H${width}" stroke="#17212b" stroke-width=".32"/><text x="3" y="5" font-size="2.4" fill="#65747d">ARCENAL DRAW</text><text x="${width / 2}" y="9.5" text-anchor="middle" font-size="3.15" font-weight="700">PLAN DE CONTRÔLE GAMMAGRAPHIQUE</text><text x="3" y="19" font-size="2.6">Date : ${displayDate}</text><text x="79" y="19" text-anchor="end" font-size="2.35" font-weight="700">Équipes visibles : ${count}</text><text x="3" y="28" font-size="2.6">Localisation : ${escapeText(state.location || '—')}</text>${rows}<g transform="translate(3 ${headerHeight + rowHeight * count + 4})"><text x="0" y="-1.2" font-size="2.35">Échelle graphique — mètres</text>${bars}<text x="0" y="8" font-size="2.2">0</text><text x="${scaleTotal / 2 - 2}" y="8" font-size="2.2">${segmentMeters * 2}</text><text x="${scaleTotal - 2}" y="8" font-size="2.2">${segmentMeters * 4} m</text></g>${peopleRows}`;
}

function renderCountPicker() {
  const picker = document.querySelector('#count-picker');
  picker.innerHTML = `<span class="count-label">Nombre d’équipes</span><div class="count-stepper"><button type="button" data-count-delta="-1" aria-label="Retirer une équipe" ${state.interventions.length === 1 ? 'disabled' : ''}>−</button><input id="intervention-count" type="number" min="1" max="10" step="1" value="${state.interventions.length}" aria-label="Nombre d’équipes ou sociétés"/><button type="button" data-count-delta="1" aria-label="Ajouter une équipe" ${state.interventions.length === 10 ? 'disabled' : ''}>+</button></div>`;
}

function renderInterventionForms() {
  const container = document.querySelector('#intervention-forms');
  container.innerHTML = state.interventions.map((item, index) => {
    const r25 = radiusMeters(item, 25, item.attenuation);
    const r2_5 = radiusMeters(item, 2.5, item.attenuation);
    return `<article class="intervention-card" style="--intervention-color:${item.color}" data-intervention-id="${item.id}"><div class="intervention-title"><span>${item.code} — ${escapeText(item.company)}</span><input data-field="color" type="color" value="${item.color}" title="Couleur" /></div><div class="intervention-grid"><label class="full">Société<input data-field="company" type="text" value="${escapeText(item.company)}" /></label><label>Radionucléide<select data-field="isotope"><option ${item.isotope === 'Ir-192' ? 'selected' : ''}>Ir-192</option><option ${item.isotope === 'Se-75' ? 'selected' : ''}>Se-75</option></select></label><label>Activité<div class="activity-row"><input data-field="activity" type="number" min="0" step="any" value="${item.activity}" /><select data-field="unit"><option ${item.unit === 'Ci' ? 'selected' : ''}>Ci</option><option ${item.unit === 'TBq' ? 'selected' : ''}>TBq</option></select></div></label><label>Début des tirs<input data-field="scheduleStart" type="time" value="${item.scheduleStart}" /></label><label>Fin des tirs<input data-field="scheduleEnd" type="time" value="${item.scheduleEnd}" /></label><label class="full check-row overzone-toggle"><input data-field="overEnabled" type="checkbox" ${item.overEnabled ? 'checked' : ''} /> Ajouter un surbalisage à chaque impact</label><div class="overzone-settings full ${item.overEnabled ? '' : 'disabled'}"><label>Distance exacte (m)<input data-field="overDistance" type="number" min="0.1" step="0.1" value="${item.overDistance}" ${item.overEnabled ? '' : 'disabled'} /></label><label>Trait<select data-field="overStyle" ${item.overEnabled ? '' : 'disabled'}><option value="dashed" ${item.overStyle === 'dashed' ? 'selected' : ''}>Pointillé</option><option value="solid" ${item.overStyle === 'solid' ? 'selected' : ''}>Continu</option></select></label><label>Épaisseur (mm)<input data-field="overWidth" type="number" min="0.2" max="5" step="0.1" value="${item.overWidth}" ${item.overEnabled ? '' : 'disabled'} /></label><label>Couleur<input data-field="overColor" type="color" value="${item.overColor}" ${item.overEnabled ? '' : 'disabled'} /></label></div><label class="full check-row"><input data-field="attenuation" type="checkbox" ${item.attenuation ? 'checked' : ''} /> Atténuation 1/250 par défaut</label><div class="result-row"><span>2,5 µSv : <strong>${formatDistance(r2_5)}</strong></span><span>25 µSv : <strong>${formatDistance(r25)}</strong></span></div></div></article>`;
  }).join('');
  renderCircleInterventions();
}

function renderCircleInterventions() {
  const container = document.querySelector('#circle-interventions');
  const checked = container.querySelector('input:checked')?.value || state.interventions[0]?.id;
  container.innerHTML = state.interventions.map((item, index) => `<label class="radio-option"><input type="radio" name="circle-intervention" value="${item.id}" ${item.id === checked || (!checked && index === 0) ? 'checked' : ''}/><span class="swatch" style="background:${item.color}"></span><span>${item.code} — ${escapeText(item.company)}</span></label>`).join('');
  updateComputedRadius();
}

function circleSettings() {
  const interventionId = document.querySelector('input[name="circle-intervention"]:checked')?.value || state.interventions[0]?.id;
  const thresholdValue = document.querySelector('input[name="threshold"]:checked')?.value || '2.5';
  const threshold = thresholdValue === 'manual' ? 'manual' : Number(thresholdValue);
  const attenuated = document.querySelector('#circle-attenuation').checked;
  const manualRadius = Math.max(0.1, Number(document.querySelector('#manual-radius').value) || 0.1);
  return { interventionId, threshold, attenuated, manualRadius };
}

function updateComputedRadius() {
  const settings = circleSettings();
  const intervention = state.interventions.find((item) => item.id === settings.interventionId);
  const manual = settings.threshold === 'manual';
  document.querySelector('#manual-radius-row').hidden = !manual;
  document.querySelector('#circle-attenuation-row').hidden = manual;
  document.querySelector('#computed-radius').textContent = manual ? formatDistance(settings.manualRadius) : intervention ? formatDistance(radiusMeters(intervention, settings.threshold, settings.attenuated)) : '—';
}

function circleById(id) {
  return state.circles.find((circle) => circle.id === id);
}

function overzoneKey(interventionId, cx, cy) {
  return `${interventionId}:${Number(cx).toFixed(2)}:${Number(cy).toFixed(2)}`;
}

function renderOverzones() {
  overzoneLayer.innerHTML = '';
  const circlesInMerge = new Set(state.merges.flatMap((merge) => merge.circleIds));
  const groups = state.merges.map((merge) => ({ key: `merge:${merge.id}`, circles: merge.circleIds.map(circleById).filter(Boolean) }));
  state.circles.filter((circle) => !circlesInMerge.has(circle.id)).forEach((circle) => {
    groups.push({ key: overzoneKey(circle.interventionId, circle.cx, circle.cy), circles: [circle] });
  });
  const rendered = new Set();
  groups.forEach((group) => {
    const first = group.circles[0];
    const intervention = state.interventions.find((item) => item.id === first?.interventionId);
    if (!first || !intervention?.overEnabled || state.suppressedOverzones.includes(group.key)) return;
    const uniqueCenters = group.circles.filter((circle) => {
      const centerKey = overzoneKey(intervention.id, circle.cx, circle.cy);
      if (rendered.has(centerKey)) return false;
      rendered.add(centerKey);
      return true;
    });
    if (!uniqueCenters.length) return;
    const overCircles = uniqueCenters.map((circle) => ({ ...circle, radius: Math.max(0.1, Number(intervention.overDistance) || 0.1) }));
    const element = document.createElementNS(NS, overCircles.length > 1 ? 'path' : 'circle');
    if (overCircles.length > 1) element.setAttribute('d', exactUnionPath(overCircles));
    else {
      element.setAttribute('cx', overCircles[0].cx);
      element.setAttribute('cy', overCircles[0].cy);
      element.setAttribute('r', overCircles[0].radius);
    }
    element.setAttribute('fill', 'none');
    element.setAttribute('stroke', intervention.overColor);
    element.setAttribute('stroke-width', Math.max(0.2, Number(intervention.overWidth) || 1.2));
    if (intervention.overStyle === 'dashed') element.setAttribute('stroke-dasharray', '4 2.5');
    element.setAttribute('class', `overzone-circle${selectedOverzoneKeys.has(group.key) ? ' selected' : ''}`);
    element.dataset.overzoneKey = group.key;
    element.addEventListener('click', selectOverzone);
    overzoneLayer.append(element);
  });
}

function renderZones() {
  renderOverzones();
  zoneLayer.innerHTML = '';
  impactLayer.innerHTML = '';
  const circlesInMerge = new Set(state.merges.flatMap((merge) => merge.circleIds));
  state.merges.forEach((merge) => {
    const circles = merge.circleIds.map(circleById).filter(Boolean);
    if (!circles.length) return;
    const path = document.createElementNS(NS, 'path');
    path.setAttribute('d', exactUnionPath(circles));
    path.setAttribute('fill', merge.color);
    path.setAttribute('fill-opacity', String(state.zoneOpacity / 100));
    path.setAttribute('stroke', merge.color);
    path.setAttribute('stroke-width', '1.2');
    path.setAttribute('class', `merged-zone${selectedMergeIds.has(merge.id) ? ' selected' : ''}`);
    path.dataset.mergeId = merge.id;
    path.addEventListener('click', selectMergedZone);
    zoneLayer.append(path);
  });
  state.circles.forEach((circle) => {
    const intervention = state.interventions.find((item) => item.id === circle.interventionId);
    if (!intervention) return;
    if (!circlesInMerge.has(circle.id)) {
      const element = document.createElementNS(NS, 'circle');
      element.setAttribute('cx', circle.cx);
      element.setAttribute('cy', circle.cy);
      element.setAttribute('r', circle.radius);
      element.setAttribute('fill', circle.color || intervention.color);
      element.setAttribute('fill-opacity', String(state.zoneOpacity / 100));
      element.setAttribute('stroke', circle.color || intervention.color);
      element.setAttribute('stroke-width', '1.1');
      element.setAttribute('class', `zone-circle${selectedCircleIds.has(circle.id) ? ' selected' : ''}`);
      element.dataset.circleId = circle.id;
      element.addEventListener('click', selectCircle);
      zoneLayer.append(element);
    }
  });
  const centers = new Map();
  state.circles.forEach((circle) => {
    const key = `${circle.cx.toFixed(2)}:${circle.cy.toFixed(2)}`;
    if (!centers.has(key)) centers.set(key, []);
    centers.get(key).push(circle);
  });
  centers.forEach((circles) => {
    const circle = circles[0];
    const intervention = state.interventions.find((item) => item.id === circle.interventionId);
    const marker = document.createElementNS(NS, 'g');
    marker.setAttribute('class', 'impact-marker');
    marker.setAttribute('transform', `translate(${circle.cx} ${circle.cy}) scale(${1 / mapScale()})`);
    marker.dataset.circleIds = circles.map((item) => item.id).join(',');
    marker.innerHTML = `<image href="assets/symbole-radioactif.png" x="-2" y="-2" width="4" height="4" preserveAspectRatio="xMidYMid slice" clip-path="url(#impact-image-clip)"/>${state.showImpactLabels ? `<text class="zone-label" x="3" y="1" fill="${intervention?.color || '#17212b'}">${intervention?.code || ''}</text>` : ''}`;
    marker.addEventListener('click', selectImpact);
    impactLayer.append(marker);
  });
  renderSignals();
  renderMeasurements();
  updateSelectionPanel();
}

function signalMarkup(type) {
  if (type === 'beacon') return '<image href="assets/gyrophare-orange.png" x="-8" y="-8" width="16" height="16" preserveAspectRatio="xMidYMid meet"/>';
  if (type === 'barrier') return '<image href="assets/barriere-chantier.png" x="-10" y="-6.7" width="20" height="13.4" preserveAspectRatio="xMidYMid meet"/>';
  if (type === 'cone') return '<image href="assets/cone-signalisation.png" x="-8" y="-8" width="16" height="16" preserveAspectRatio="xMidYMid meet"/>';
  return '<image href="assets/panneau-interdiction.png" x="-8" y="-8" width="16" height="16" preserveAspectRatio="xMidYMid meet"/>';
}

function renderSignals() {
  signalLayer.innerHTML = '';
  state.signals.forEach((signal) => {
    const element = document.createElementNS(NS, 'g');
    element.setAttribute('class', `signal-item${selectedSignalIds.has(signal.id) ? ' selected' : ''}`);
    element.setAttribute('transform', `translate(${signal.x} ${signal.y}) scale(${1 / mapScale()})`);
    element.dataset.signalId = signal.id;
    element.innerHTML = `<circle class="selection-ring" r="11"/>${signalMarkup(signal.type)}`;
    element.addEventListener('click', selectSignal);
    signalLayer.append(element);
  });
}

function measurementDistance(measurement) {
  const nativeDistance = Math.hypot(measurement.x2 - measurement.x1, measurement.y2 - measurement.y1);
  return nativeDistance * (Number(state.calibration?.metersPerNativeUnit) || 1);
}

function renderMeasurements() {
  measurementLayer.replaceChildren();
  (state.measurements || []).forEach((measurement) => {
    const midpointX = (measurement.x1 + measurement.x2) / 2;
    const midpointY = (measurement.y1 + measurement.y2) / 2;
    const label = formatDistance(measurementDistance(measurement));
    const labelWidth = Math.max(18, label.length * 2.4 + 5);
    const element = document.createElementNS(NS, 'g');
    element.setAttribute('class', `measurement-item${selectedMeasurementIds.has(measurement.id) ? ' selected' : ''}`);
    element.dataset.measurementId = measurement.id;
    element.innerHTML = `<line x1="${measurement.x1}" y1="${measurement.y1}" x2="${measurement.x2}" y2="${measurement.y2}"/><circle class="measurement-end" cx="${measurement.x1}" cy="${measurement.y1}" r="1.2"/><circle class="measurement-end" cx="${measurement.x2}" cy="${measurement.y2}" r="1.2"/><g class="measurement-label" transform="translate(${midpointX} ${midpointY}) scale(${1 / mapScale()})"><rect x="${-labelWidth / 2}" y="-3.8" width="${labelWidth}" height="7.6" rx="1.5"/><text y="1.25">${label}</text></g>`;
    element.addEventListener('click', selectMeasurement);
    measurementLayer.append(element);
  });
  if (pendingMeasurementPoint) {
    const anchor = document.createElementNS(NS, 'circle');
    anchor.setAttribute('class', 'measurement-anchor');
    anchor.setAttribute('cx', pendingMeasurementPoint.x);
    anchor.setAttribute('cy', pendingMeasurementPoint.y);
    anchor.setAttribute('r', 2);
    measurementLayer.append(anchor);
  }
}

function selectMeasurement(event) {
  event.stopPropagation();
  if (activeTool !== 'select') return;
  const id = event.currentTarget.dataset.measurementId;
  selectedCircleIds.clear(); selectedMergeIds.clear(); selectedSignalIds.clear(); selectedOverzoneKeys.clear();
  if (selectedMeasurementIds.has(id)) selectedMeasurementIds.delete(id); else selectedMeasurementIds.add(id);
  renderZones();
}

function selectCircle(event) {
  event.stopPropagation();
  if (activeTool === 'circle') { placeCircle(event); return; }
  if (activeTool !== 'select') return;
  const id = event.currentTarget.dataset.circleId;
  selectedMergeIds.clear();
  selectedSignalIds.clear();
  selectedOverzoneKeys.clear();
  selectedMeasurementIds.clear();
  if (selectedCircleIds.has(id)) selectedCircleIds.delete(id); else selectedCircleIds.add(id);
  renderZones();
}

function selectMergedZone(event) {
  event.stopPropagation();
  if (activeTool === 'circle') { placeCircle(event); return; }
  if (activeTool !== 'select') return;
  const id = event.currentTarget.dataset.mergeId;
  selectedCircleIds.clear();
  selectedSignalIds.clear();
  selectedOverzoneKeys.clear();
  selectedMeasurementIds.clear();
  if (selectedMergeIds.has(id)) selectedMergeIds.delete(id); else selectedMergeIds.add(id);
  renderZones();
}

function selectSignal(event) {
  event.stopPropagation();
  if (activeTool === 'signal') { placeSignal(event); return; }
  if (activeTool !== 'select') return;
  const id = event.currentTarget.dataset.signalId;
  selectedCircleIds.clear();
  selectedMergeIds.clear();
  selectedOverzoneKeys.clear();
  selectedMeasurementIds.clear();
  if (selectedSignalIds.has(id)) selectedSignalIds.delete(id); else selectedSignalIds.add(id);
  renderZones();
}

function selectImpact(event) {
  event.stopPropagation();
  if (activeTool !== 'select') return;
  const ids = event.currentTarget.dataset.circleIds.split(',');
  const mergeIds = state.merges.filter((merge) => merge.circleIds.some((id) => ids.includes(id))).map((merge) => merge.id);
  selectedCircleIds.clear(); selectedMergeIds.clear(); selectedSignalIds.clear(); selectedOverzoneKeys.clear(); selectedMeasurementIds.clear();
  if (mergeIds.length) mergeIds.forEach((id) => selectedMergeIds.add(id));
  else ids.forEach((id) => selectedCircleIds.add(id));
  renderZones();
}

function selectOverzone(event) {
  event.stopPropagation();
  if (activeTool !== 'select') return;
  const key = event.currentTarget.dataset.overzoneKey;
  selectedCircleIds.clear(); selectedMergeIds.clear(); selectedSignalIds.clear(); selectedMeasurementIds.clear();
  if (selectedOverzoneKeys.has(key)) selectedOverzoneKeys.delete(key); else selectedOverzoneKeys.add(key);
  renderZones();
}

function updateSelectionPanel(message = '') {
  const count = selectedCircleIds.size;
  const mergeCount = selectedMergeIds.size;
  const signalCount = selectedSignalIds.size;
  const overzoneCount = selectedOverzoneKeys.size;
  const measurementCount = selectedMeasurementIds.size;
  const hasSelection = count + mergeCount + signalCount + overzoneCount + measurementCount > 0;
  const selectionMessage = document.querySelector('#selection-message');
  selectionMessage.hidden = !hasSelection;
  selectionMessage.textContent = message || (count ? `${count} zone(s) sélectionnée(s).` : mergeCount ? `${mergeCount} zone(s) fusionnée(s) sélectionnée(s).` : signalCount ? `${signalCount} équipement(s) sélectionné(s).` : overzoneCount ? `${overzoneCount} surbalisage(s) sélectionné(s).` : measurementCount ? `${measurementCount} mesure(s) sélectionnée(s).` : '');
  const interventions = new Set([...selectedCircleIds].map((id) => circleById(id)?.interventionId));
  const mergeButton = document.querySelector('#merge-button');
  const splitButton = document.querySelector('#split-button');
  mergeButton.disabled = count < 2 || interventions.size !== 1;
  mergeButton.hidden = mergeButton.disabled;
  splitButton.disabled = mergeCount === 0;
  splitButton.hidden = splitButton.disabled;
  document.querySelector('#delete-selection').disabled = count + mergeCount + signalCount + overzoneCount + measurementCount === 0;
  const assignmentRow = document.querySelector('#reassign-zone-row');
  assignmentRow.hidden = count + mergeCount === 0;
  if (!assignmentRow.hidden) {
    const selectedIds = new Set([...selectedCircleIds]);
    state.merges.filter((merge) => selectedMergeIds.has(merge.id)).flatMap((merge) => merge.circleIds).forEach((id) => selectedIds.add(id));
    const currentIds = new Set([...selectedIds].map((id) => circleById(id)?.interventionId).filter(Boolean));
    const select = document.querySelector('#reassign-intervention');
    select.innerHTML = state.interventions.map((item) => `<option value="${item.id}">${item.code} — ${escapeText(item.company)}</option>`).join('');
    if (currentIds.size === 1) select.value = [...currentIds][0];
  }
}

function circlesConnected(circles) {
  const reached = new Set([circles[0].id]);
  let changed = true;
  while (changed) {
    changed = false;
    circles.forEach((a) => circles.forEach((b) => {
      if (reached.has(a.id) && !reached.has(b.id) && Math.hypot(a.cx - b.cx, a.cy - b.cy) <= a.radius + b.radius + 0.001) {
        reached.add(b.id); changed = true;
      }
    }));
  }
  return reached.size === circles.length;
}

function pointOn(circle, angle) {
  return { x: circle.cx + Math.cos(angle) * circle.radius, y: circle.cy + Math.sin(angle) * circle.radius };
}

function exposedArcs(circles) {
  const tau = Math.PI * 2;
  const arcs = [];
  circles.forEach((circle, circleIndex) => {
    const angles = [0];
    circles.forEach((other, otherIndex) => {
      if (circleIndex === otherIndex) return;
      const dx = other.cx - circle.cx;
      const dy = other.cy - circle.cy;
      const distance = Math.hypot(dx, dy);
      if (distance >= circle.radius + other.radius - 1e-7 || distance <= Math.abs(circle.radius - other.radius) + 1e-7 || distance === 0) return;
      const direction = Math.atan2(dy, dx);
      const spread = Math.acos((circle.radius ** 2 + distance ** 2 - other.radius ** 2) / (2 * circle.radius * distance));
      [direction - spread, direction + spread].forEach((angle) => angles.push((angle % tau + tau) % tau));
    });
    const ordered = [...new Set(angles.map((angle) => angle.toFixed(10)))].map(Number).sort((a, b) => a - b);
    ordered.forEach((start, index) => {
      const end = index + 1 < ordered.length ? ordered[index + 1] : ordered[0] + tau;
      const midpoint = pointOn(circle, (start + end) / 2);
      const covered = circles.some((other, otherIndex) => otherIndex !== circleIndex && Math.hypot(midpoint.x - other.cx, midpoint.y - other.cy) < other.radius - 1e-6);
      if (!covered) arcs.push({ circle, start, end, startPoint: pointOn(circle, start), endPoint: pointOn(circle, end % tau) });
    });
  });
  return arcs;
}

function arcCommand(arc) {
  const delta = arc.end - arc.start;
  if (delta >= Math.PI * 2 - 1e-6) {
    const opposite = pointOn(arc.circle, arc.start + Math.PI);
    return `A${arc.circle.radius} ${arc.circle.radius} 0 1 1 ${opposite.x.toFixed(3)} ${opposite.y.toFixed(3)} A${arc.circle.radius} ${arc.circle.radius} 0 1 1 ${arc.endPoint.x.toFixed(3)} ${arc.endPoint.y.toFixed(3)}`;
  }
  return `A${arc.circle.radius} ${arc.circle.radius} 0 ${delta > Math.PI ? 1 : 0} 1 ${arc.endPoint.x.toFixed(3)} ${arc.endPoint.y.toFixed(3)}`;
}

function exactUnionPath(circles) {
  const remaining = exposedArcs(circles);
  const paths = [];
  while (remaining.length) {
    const first = remaining.shift();
    let current = first;
    let path = `M${first.startPoint.x.toFixed(3)} ${first.startPoint.y.toFixed(3)} ${arcCommand(first)}`;
    let guard = 0;
    while (Math.hypot(current.endPoint.x - first.startPoint.x, current.endPoint.y - first.startPoint.y) > 0.01 && remaining.length && guard < 1000) {
      guard += 1;
      let bestIndex = 0;
      let bestDistance = Infinity;
      remaining.forEach((candidate, index) => {
        const distance = Math.hypot(candidate.startPoint.x - current.endPoint.x, candidate.startPoint.y - current.endPoint.y);
        if (distance < bestDistance) { bestDistance = distance; bestIndex = index; }
      });
      if (bestDistance > 0.05) break;
      current = remaining.splice(bestIndex, 1)[0];
      path += ` ${arcCommand(current)}`;
    }
    paths.push(`${path} Z`);
  }
  return paths.join(' ');
}

function renderCalibrationStatus() {
  const calibration = state.calibration;
  const text = calibration.metersPerNativeUnit === 1 ? '1 unité = 1 m' : `1 unité = ${calibration.metersPerNativeUnit.toLocaleString('fr-FR')} m`;
  document.querySelector('#calibration-status').textContent = `Calibration : ${text}`;
}

function renderAll() {
  setOrientation(state.orientation);
  updateMapTransform();
  renderPlanPreview();
  renderCountPicker();
  renderInterventionForms();
  renderZones();
  renderTitleBlock();
  renderCalibrationStatus();
}

function setTool(tool) {
  if (tool !== 'measure') pendingMeasurementPoint = null;
  activeTool = tool;
  document.querySelectorAll('.tool').forEach((button) => button.classList.toggle('active', button.dataset.tool === tool));
  circlePanel.hidden = tool !== 'circle';
  selectionPanel.hidden = tool !== 'select';
  signalPanel.hidden = tool !== 'signal';
  document.querySelector('.canvas-area').classList.toggle('can-pan', tool === 'select');
  canvasHint.textContent = tool === 'circle' ? 'Cliquez sur le point d’impact dans le plan.' : tool === 'signal' ? 'Cliquez pour placer l’équipement de signalisation.' : tool === 'measure' ? 'Cliquez sur le premier point de la mesure.' : 'Glissez le fond pour le déplacer. La molette règle son zoom.';
  renderMeasurements();
}

function openSettings() {
  renderLogoSettings();
  if (!settingsDialog.open) settingsDialog.showModal();
}

function svgPointFromEvent(event) {
  const box = sheet.getBoundingClientRect();
  const viewBox = sheet.viewBox.baseVal;
  const paperX = ((event.clientX - box.left) / box.width) * viewBox.width;
  const paperY = ((event.clientY - box.top) / box.height) * viewBox.height;
  const scale = mapScale();
  return { x: 150 + (paperX - 150 - state.panX) / scale, y: 135 + (paperY - 135 - state.panY) / scale };
}

function placeCircle(event) {
  if (activeTool !== 'circle') return;
  if (event.target.closest('#title-block')) return;
  const point = svgPointFromEvent(event);
  const settings = circleSettings();
  const intervention = state.interventions.find((item) => item.id === settings.interventionId);
  if (!intervention) return;
  const manual = settings.threshold === 'manual';
  intervention.displayThreshold = settings.threshold;
  state.circles.push({ id: uid('circle'), cx: point.x, cy: point.y, radius: manual ? settings.manualRadius : radiusMeters(intervention, settings.threshold, settings.attenuated), threshold: settings.threshold, attenuated: manual ? false : settings.attenuated, manualDistance: manual ? settings.manualRadius : null, interventionId: intervention.id, color: intervention.color });
  renderZones(); renderTitleBlock();
  saveState();
}

function placeSignal(event) {
  if (activeTool !== 'signal') return;
  if (event.target.closest('#title-block')) return;
  const point = svgPointFromEvent(event);
  state.signals.push({ id: uid('signal'), type: selectedSignalType, x: point.x, y: point.y });
  renderSignals();
  saveState();
}

function placeMeasurement(event) {
  if (activeTool !== 'measure' || event.target.closest('#title-block')) return;
  const point = svgPointFromEvent(event);
  if (!pendingMeasurementPoint) {
    pendingMeasurementPoint = point;
    canvasHint.textContent = 'Cliquez sur le second point de la mesure.';
    renderMeasurements();
    return;
  }
  if (Math.hypot(point.x - pendingMeasurementPoint.x, point.y - pendingMeasurementPoint.y) < 0.01) return;
  state.measurements.push({ id: uid('measurement'), x1: pendingMeasurementPoint.x, y1: pendingMeasurementPoint.y, x2: point.x, y2: point.y });
  pendingMeasurementPoint = null;
  canvasHint.textContent = 'Mesure ajoutée. Cliquez pour commencer une nouvelle mesure.';
  renderZones();
  saveState();
}

function handleSheetClick(event) {
  if (activeTool === 'circle') placeCircle(event);
  if (activeTool === 'signal') placeSignal(event);
  if (activeTool === 'measure') placeMeasurement(event);
}

function renderLogoSettings() {
  document.querySelector('#settings-orientation').value = state.orientation;
  document.querySelector('#settings-margin').value = state.sheetMargin;
  document.querySelector('#settings-zoom').value = state.planZoom;
  document.querySelector('#settings-opacity').value = String(state.zoneOpacity);
  document.querySelector('#settings-labels').checked = state.showImpactLabels;
  document.querySelector('#client-name').value = state.client;
  document.querySelector('#settings-calibration-status').textContent = document.querySelector('#calibration-status').textContent;
  document.querySelector('#author-name').value = state.author.name;
  document.querySelector('#author-role').value = state.author.role;
  document.querySelector('#validator-enabled').checked = state.validatorEnabled;
  document.querySelector('#validator-settings').hidden = !state.validatorEnabled;
  document.querySelector('#validator-name').value = state.validator.name;
  document.querySelector('#validator-role').value = state.validator.role;
  ['author', 'validator'].forEach((kind) => {
    const signature = state[kind].signature;
    const preview = document.querySelector(`#${kind}-signature-preview`);
    preview.hidden = !signature;
    if (signature) preview.querySelector('strong').textContent = signature.name;
  });
  const preview = document.querySelector('#logo-preview');
  const removeButton = document.querySelector('#remove-logo');
  preview.hidden = !state.logo;
  removeButton.disabled = !state.logo;
  if (!state.logo) return;
  document.querySelector('#logo-name').textContent = state.logo.name;
  document.querySelector('#logo-status').textContent = state.logo.dataUrl ? 'Logo intégré au cartouche' : 'PDF enregistré — conversion visuelle prévue côté serveur';
  const placeholder = `data:image/svg+xml,${encodeURIComponent('<svg xmlns="http://www.w3.org/2000/svg" width="150" height="80"><rect width="100%" height="100%" fill="#f1f3f4"/><text x="50%" y="48%" text-anchor="middle" font-family="Arial" font-size="18" font-weight="bold">PDF</text></svg>')}`;
  document.querySelector('#logo-preview img').src = state.logo.dataUrl || placeholder;
}

function readImageLogo(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onerror = reject;
    reader.onload = () => {
      const image = new Image();
      image.onerror = reject;
      image.onload = () => {
        const scale = Math.min(1, 600 / image.width, 220 / image.height);
        const canvas = document.createElement('canvas');
        canvas.width = Math.max(1, Math.round(image.width * scale));
        canvas.height = Math.max(1, Math.round(image.height * scale));
        canvas.getContext('2d').drawImage(image, 0, 0, canvas.width, canvas.height);
        resolve(canvas.toDataURL(file.type === 'image/jpeg' ? 'image/jpeg' : 'image/png', .9));
      };
      image.src = reader.result;
    };
    reader.readAsDataURL(file);
  });
}

async function processLogoFile(file) {
  if (!file || !/\.(pdf|png|jpe?g)$/i.test(file.name)) return;
  if (file.type === 'application/pdf' || /\.pdf$/i.test(file.name)) {
    state.logo = { name: file.name, type: 'application/pdf', dataUrl: null };
  } else {
    const dataUrl = await readImageLogo(file);
    state.logo = { name: file.name, type: file.type || 'image/png', dataUrl };
  }
  renderLogoSettings(); renderTitleBlock(); saveState();
}

async function processSignatureFile(kind, file) {
  if (!file || !/\.(pdf|png|jpe?g)$/i.test(file.name)) return;
  const signature = file.type === 'application/pdf' || /\.pdf$/i.test(file.name)
    ? { name: file.name, type: 'application/pdf', dataUrl: null }
    : { name: file.name, type: file.type || 'image/png', dataUrl: await readImageLogo(file) };
  state[kind].signature = signature;
  renderLogoSettings(); renderTitleBlock(); saveState();
}

function openCalibration(fileName, recalibration = false) {
  pendingFileName = fileName;
  const requiresTwoPoints = /\.(pdf|png|jpe?g)$/i.test(fileName);
  document.querySelector('#calibration-file').textContent = recalibration ? `Recalibrage de « ${state.baseName} ». Les PDF déjà exportés ne seront pas modifiés.` : requiresTwoPoints ? `« ${fileName} » est un document sans unité métrique exploitable : une calibration par deux points est obligatoire.` : `« ${fileName} » : confirmez l’unité déclarée ou calibrez le plan par deux points.`;
  const sourceUnit = document.querySelector('#source-unit');
  sourceUnit.value = recalibration ? state.calibration.sourceUnit : 'unknown';
  sourceUnit.disabled = requiresTwoPoints && !recalibration;
  updateCalibrationPreview();
  calibrationDialog.showModal();
}

function updateCalibrationPreview() {
  const unit = document.querySelector('#source-unit').value;
  const manual = document.querySelector('#manual-calibration');
  manual.hidden = unit !== 'unknown';
  let metersPerUnit = 1;
  if (unit === 'mm') metersPerUnit = 0.001;
  if (unit === 'unknown') metersPerUnit = (Number(document.querySelector('#real-distance').value) || 1) / (Number(document.querySelector('#native-distance').value) || 1);
  const nativePerMeter = 1 / metersPerUnit;
  document.querySelector('#calibration-result').textContent = `${nativePerMeter.toLocaleString('fr-FR', { maximumFractionDigits: 3 })} unité(s) = 1 m`;
  return metersPerUnit;
}

function confirmCalibration(event) {
  event.preventDefault();
  const unit = document.querySelector('#source-unit').value;
  state.calibration = { sourceUnit: unit, metersPerNativeUnit: updateCalibrationPreview(), method: unit === 'unknown' ? 'two-points' : 'file' };
  if (pendingFileName && pendingFileName !== state.baseName) {
    state = { ...freshState(`Plan de balisage — ${pendingFileName.replace(/\.(pdf|png|jpe?g)$/i, '')}`), baseName: pendingFileName, calibration: state.calibration };
    state.location = pendingFileName.replace(/\.(pdf|png|jpe?g)$/i, '');
    state.planFile = pendingPlanImport;
  }
  calibrationDialog.close();
  openEditor();
  saveState();
}

document.querySelectorAll('[data-open-base]').forEach((button) => button.addEventListener('click', () => {
  state = freshState(`Plan de balisage — ${button.dataset.openBase}`);
  state.baseName = button.dataset.openBase;
  state.location = button.dataset.openBase;
  openEditor();
  saveState();
}));
document.querySelector('#back-home').addEventListener('click', openHome);
document.querySelector('#orientation-select').addEventListener('change', (event) => { setOrientation(event.target.value); saveState(); });
document.querySelector('#plan-zoom').addEventListener('input', (event) => { state.planZoom = Number(event.target.value); updateMapTransform(); renderZones(); renderTitleBlock(); saveState(); });
document.querySelectorAll('.tool[data-tool]').forEach((button) => button.addEventListener('click', () => setTool(button.dataset.tool)));
document.querySelector('#settings-button').addEventListener('click', openSettings);
document.querySelector('#settings-close').addEventListener('click', () => settingsDialog.close());
document.querySelector('#settings-theme').addEventListener('change', (event) => { state.theme = event.target.value; applyTheme(state.theme); saveState(); });
document.querySelector('#settings-orientation').addEventListener('change', (event) => { document.querySelector('#orientation-select').value = event.target.value; setOrientation(event.target.value); saveState(); });
document.querySelector('#settings-margin').addEventListener('change', (event) => { state.sheetMargin = Math.max(5, Math.min(20, Number(event.target.value) || 5)); setOrientation(state.orientation); saveState(); });
document.querySelector('#settings-zoom').addEventListener('input', (event) => { state.planZoom = Number(event.target.value); document.querySelector('#plan-zoom').value = state.planZoom; updateMapTransform(); renderZones(); renderTitleBlock(); saveState(); });
document.querySelector('#settings-opacity').addEventListener('change', (event) => { state.zoneOpacity = Number(event.target.value); renderZones(); saveState(); });
document.querySelector('#settings-labels').addEventListener('change', (event) => { state.showImpactLabels = event.target.checked; renderZones(); saveState(); });
document.querySelector('#settings-recenter').addEventListener('click', () => { state.panX = 0; state.panY = 0; updateMapTransform(); renderTitleBlock(); saveState(); });
document.querySelector('#settings-recalibrate').addEventListener('click', () => openCalibration(state.baseName, true));
document.querySelector('#author-name').addEventListener('change', (event) => { state.author.name = event.target.value; renderTitleBlock(); saveState(); });
document.querySelector('#author-role').addEventListener('change', (event) => { state.author.role = event.target.value; renderTitleBlock(); saveState(); });
document.querySelector('#validator-enabled').addEventListener('change', (event) => { state.validatorEnabled = event.target.checked; document.querySelector('#validator-settings').hidden = !state.validatorEnabled; renderTitleBlock(); saveState(); });
document.querySelector('#validator-name').addEventListener('change', (event) => { state.validator.name = event.target.value; renderTitleBlock(); saveState(); });
document.querySelector('#validator-role').addEventListener('change', (event) => { state.validator.role = event.target.value; renderTitleBlock(); saveState(); });
['author', 'validator'].forEach((kind) => {
  const input = document.querySelector(`#${kind}-signature-file`);
  input.addEventListener('change', () => { if (input.files[0]) processSignatureFile(kind, input.files[0]); });
  const drop = document.querySelector(`#${kind}-signature-drop`);
  ['dragenter', 'dragover'].forEach((name) => drop.addEventListener(name, (event) => { event.preventDefault(); drop.classList.add('dragging'); }));
  ['dragleave', 'drop'].forEach((name) => drop.addEventListener(name, (event) => { event.preventDefault(); drop.classList.remove('dragging'); }));
  drop.addEventListener('drop', (event) => processSignatureFile(kind, event.dataTransfer.files[0]));
});
document.querySelectorAll('[data-remove-signature]').forEach((button) => button.addEventListener('click', () => { state[button.dataset.removeSignature].signature = null; renderLogoSettings(); renderTitleBlock(); saveState(); }));
sheet.addEventListener('click', handleSheetClick);
sheet.addEventListener('wheel', (event) => {
  event.preventDefault();
  const box = sheet.getBoundingClientRect();
  const viewBox = sheet.viewBox.baseVal;
  const paperX = ((event.clientX - box.left) / box.width) * viewBox.width;
  const paperY = ((event.clientY - box.top) / box.height) * viewBox.height;
  const oldScale = mapScale();
  const mapX = 150 + (paperX - 150 - state.panX) / oldScale;
  const mapY = 135 + (paperY - 135 - state.panY) / oldScale;
  const zoomStep = state.planZoom < 200 ? 25 : 50;
  state.planZoom = Math.max(25, Math.min(800, state.planZoom + (event.deltaY < 0 ? zoomStep : -zoomStep)));
  const newScale = mapScale();
  state.panX = paperX - 150 - newScale * (mapX - 150);
  state.panY = paperY - 135 - newScale * (mapY - 135);
  document.querySelector('#plan-zoom').value = state.planZoom;
  updateMapTransform(); renderZones(); renderTitleBlock(); saveState();
}, { passive: false });
sheet.addEventListener('pointerdown', (event) => {
  if (activeTool !== 'select' || event.button !== 0 || event.target.closest('.zone-circle,.merged-zone,.overzone-circle,.signal-item,.measurement-item,.impact-marker,#title-block')) return;
  const box = sheet.getBoundingClientRect();
  const viewBox = sheet.viewBox.baseVal;
  panSession = { x: event.clientX, y: event.clientY, panX: state.panX, panY: state.panY, ratioX: viewBox.width / box.width, ratioY: viewBox.height / box.height };
  sheet.setPointerCapture(event.pointerId);
  document.querySelector('.canvas-area').classList.add('panning');
});
sheet.addEventListener('pointermove', (event) => {
  if (!panSession) return;
  state.panX = panSession.panX + (event.clientX - panSession.x) * panSession.ratioX;
  state.panY = panSession.panY + (event.clientY - panSession.y) * panSession.ratioY;
  updateMapTransform();
  renderTitleBlock();
});
sheet.addEventListener('pointerup', () => {
  if (!panSession) return;
  panSession = null;
  document.querySelector('.canvas-area').classList.remove('panning');
  saveState();
});

new ResizeObserver(() => {
  if (state.planFile?.previewType === 'application/pdf') queuePdfRender(80);
}).observe(sheetFrame);
document.querySelector('#circle-panel').addEventListener('change', updateComputedRadius);
document.querySelector('#manual-radius').addEventListener('input', updateComputedRadius);
document.querySelector('#signal-picker').addEventListener('click', (event) => {
  const button = event.target.closest('[data-signal]');
  if (!button) return;
  selectedSignalType = button.dataset.signal;
  document.querySelectorAll('#signal-picker button').forEach((item) => item.classList.toggle('active', item === button));
});
function deleteSelection() {
  const mergedCircleIds = new Set(state.merges.filter((merge) => selectedMergeIds.has(merge.id)).flatMap((merge) => merge.circleIds));
  state.circles = state.circles.filter((circle) => !selectedCircleIds.has(circle.id) && !mergedCircleIds.has(circle.id));
  state.merges = state.merges.filter((merge) => !selectedMergeIds.has(merge.id) && !merge.circleIds.some((id) => selectedCircleIds.has(id)));
  state.signals = state.signals.filter((signal) => !selectedSignalIds.has(signal.id));
  state.measurements = (state.measurements || []).filter((measurement) => !selectedMeasurementIds.has(measurement.id));
  selectedOverzoneKeys.forEach((key) => {
    if (!state.suppressedOverzones.includes(key)) state.suppressedOverzones.push(key);
  });
  selectedCircleIds.clear(); selectedMergeIds.clear(); selectedSignalIds.clear(); selectedOverzoneKeys.clear(); selectedMeasurementIds.clear();
  renderZones(); renderTitleBlock(); saveState();
}
document.querySelector('#delete-selection').addEventListener('click', deleteSelection);
document.addEventListener('keydown', (event) => {
  if (!['Backspace', 'Delete'].includes(event.key) || ['INPUT', 'TEXTAREA', 'SELECT'].includes(document.activeElement?.tagName)) return;
  if (selectedCircleIds.size + selectedMergeIds.size + selectedSignalIds.size + selectedOverzoneKeys.size + selectedMeasurementIds.size === 0) return;
  event.preventDefault();
  deleteSelection();
});
document.querySelector('#plan-date').addEventListener('change', (event) => { state.planDate = event.target.value; renderTitleBlock(); saveState(); });
document.querySelector('#plan-location').addEventListener('change', (event) => { state.location = event.target.value.trim(); renderTitleBlock(); saveState(); });
const logoInput = document.querySelector('#logo-file');
logoInput.addEventListener('change', () => { if (logoInput.files[0]) processLogoFile(logoInput.files[0]); });
const logoDrop = document.querySelector('#logo-drop');
['dragenter', 'dragover'].forEach((name) => logoDrop.addEventListener(name, (event) => { event.preventDefault(); logoDrop.classList.add('dragging'); }));
['dragleave', 'drop'].forEach((name) => logoDrop.addEventListener(name, (event) => { event.preventDefault(); logoDrop.classList.remove('dragging'); }));
logoDrop.addEventListener('drop', (event) => processLogoFile(event.dataTransfer.files[0]));
document.querySelector('#remove-logo').addEventListener('click', () => { state.logo = null; renderLogoSettings(); renderTitleBlock(); saveState(); });
document.querySelector('#client-name').addEventListener('change', (event) => { state.client = event.target.value.trim(); renderTitleBlock(); saveState(); });
document.querySelector('#reassign-intervention').addEventListener('change', (event) => {
  const intervention = state.interventions.find((item) => item.id === event.target.value);
  if (!intervention) return;
  const selectedIds = new Set([...selectedCircleIds]);
  state.merges.filter((merge) => selectedMergeIds.has(merge.id)).forEach((merge) => {
    merge.circleIds.forEach((id) => selectedIds.add(id));
    merge.interventionId = intervention.id;
    merge.color = intervention.color;
  });
  [...selectedIds].map(circleById).filter(Boolean).forEach((circle) => {
    circle.interventionId = intervention.id;
    circle.color = intervention.color;
    if (circle.threshold !== 'manual') circle.radius = radiusMeters(intervention, circle.threshold, circle.attenuated);
  });
  renderZones(); renderTitleBlock(); saveState();
});
document.querySelector('#merge-button').addEventListener('click', () => {
  const circles = [...selectedCircleIds].map(circleById).filter(Boolean);
  if (!circlesConnected(circles)) { updateSelectionPanel('Les zones doivent se toucher pour être fusionnées.'); return; }
  const intervention = state.interventions.find((item) => item.id === circles[0].interventionId);
  state.merges.push({ id: uid('merge'), circleIds: circles.map((circle) => circle.id), interventionId: intervention.id, color: intervention.color });
  selectedCircleIds.clear(); renderZones(); saveState();
});
document.querySelector('#split-button').addEventListener('click', () => {
  state.merges = state.merges.filter((merge) => !selectedMergeIds.has(merge.id));
  selectedMergeIds.clear(); renderZones(); saveState();
});
function setInterventionCount(requestedCount) {
  const count = Math.max(1, Math.min(10, Math.round(Number(requestedCount) || 1)));
  const removedIds = new Set(state.interventions.slice(count).map((item) => item.id));
  if (state.circles.some((circle) => removedIds.has(circle.interventionId))) {
    document.querySelector('#save-status').textContent = 'Impossible : cette équipe possède encore des zones';
    renderCountPicker();
    return;
  }
  while (state.interventions.length < count) state.interventions.push(defaultIntervention(state.interventions.length));
  state.interventions = state.interventions.slice(0, count);
  renderAll(); saveState();
}
document.querySelector('#count-picker').addEventListener('click', (event) => {
  const delta = Number(event.target.dataset.countDelta);
  if (!delta) return;
  setInterventionCount(state.interventions.length + delta);
});
document.querySelector('#count-picker').addEventListener('change', (event) => {
  if (event.target.id === 'intervention-count') setInterventionCount(event.target.value);
});
document.querySelector('#intervention-forms').addEventListener('change', (event) => {
  const card = event.target.closest('[data-intervention-id]');
  if (!card) return;
  const intervention = state.interventions.find((item) => item.id === card.dataset.interventionId);
  const field = event.target.dataset.field;
  if (!intervention || !field) return;
  intervention[field] = event.target.type === 'checkbox' ? event.target.checked : event.target.type === 'number' ? Number(event.target.value) : event.target.value;
  if (field === 'overEnabled' && intervention.overEnabled) {
    state.suppressedOverzones = state.suppressedOverzones.filter((key) => !key.startsWith(`${intervention.id}:`));
  }
  if (field === 'color') {
    state.circles.filter((circle) => circle.interventionId === intervention.id).forEach((circle) => { circle.color = intervention.color; });
    state.merges.filter((merge) => merge.interventionId === intervention.id).forEach((merge) => { merge.color = intervention.color; });
  }
  state.circles.filter((circle) => circle.interventionId === intervention.id && circle.threshold !== 'manual').forEach((circle) => { circle.radius = radiusMeters(intervention, circle.threshold, circle.attenuated); });
  renderInterventionForms(); renderTitleBlock(); renderZones(); saveState();
});
function exportFileName() {
  const date = (state.planDate || new Date().toISOString().slice(0, 10)).replaceAll('-', '.');
  const client = (state.client || 'CLIENT').trim();
  const location = (state.location || 'localisation').trim();
  return `${date} plan radio ${client} ${location}`.replace(/[\\/:*?"<>|]+/g, '-').replace(/\s+/g, ' ').trim();
}

function archiveCurrentExport(exportName) {
  const archives = loadArchives();
  archives.unshift({ id: uid('archive'), exportName, exportedAt: new Date().toISOString(), state: JSON.parse(JSON.stringify(state)) });
  try {
    localStorage.setItem(ARCHIVE_KEY, JSON.stringify(archives.slice(0, 12)));
    document.querySelector('#save-status').textContent = 'Export archivé';
  } catch (error) {
    document.querySelector('#save-status').textContent = 'Archive locale saturée';
  }
  renderArchives();
  if (serverAvailable()) {
    apiRequest('archives', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ id: uid('archive'), projectId: state.projectId, exportName, state }),
    }).catch(() => { document.querySelector('#save-status').textContent = 'PDF archivé localement uniquement'; });
  }
}

document.querySelector('#export-button').addEventListener('click', () => {
  saveState();
  const exportName = exportFileName();
  archiveCurrentExport(exportName);
  const previousTitle = document.title;
  document.title = exportName;
  window.addEventListener('afterprint', () => { document.title = previousTitle; }, { once: true });
  window.print();
});
document.querySelector('#recalibrate-button').addEventListener('click', () => openCalibration(state.baseName, true));
document.querySelector('#source-unit').addEventListener('change', updateCalibrationPreview);
document.querySelector('#manual-calibration').addEventListener('input', updateCalibrationPreview);
document.querySelector('#confirm-calibration').addEventListener('click', confirmCalibration);

const fileInput = document.querySelector('#plan-file');
function setImportStatus(message = '', stateName = '') {
  importStatus.textContent = message;
  if (stateName) importStatus.dataset.state = stateName;
  else delete importStatus.dataset.state;
}

function setImportProgress(phase = 'hidden', value = 0) {
  importProgressWrap.hidden = phase === 'hidden';
  if (phase === 'hidden') return;
  if (phase === 'conversion') importProgress.removeAttribute('value');
  else importProgress.value = value;
  importProgressLabel.textContent = phase === 'upload'
    ? `Envoi du fichier — ${Math.round(value)} %`
    : phase === 'conversion'
      ? 'Analyse du PDF et conversion SVG…'
      : 'Import terminé';
}

function uploadPlanFile(file) {
  return new Promise((resolve, reject) => {
    const request = new XMLHttpRequest();
    request.open('POST', apiUrl('imports'));
    request.responseType = 'json';
    request.setRequestHeader('Content-Type', 'application/octet-stream');
    request.setRequestHeader('X-Filename', encodeURIComponent(file.name));
    request.upload.addEventListener('progress', (event) => {
      if (event.lengthComputable) setImportProgress('upload', (event.loaded / event.total) * 100);
    });
    request.upload.addEventListener('load', () => setImportProgress('conversion'));
    request.addEventListener('load', () => {
      const payload = request.response || {};
      if (request.status >= 200 && request.status < 300) resolve(payload);
      else reject(new Error(payload.error || `Erreur serveur ${request.status}`));
    });
    request.addEventListener('error', () => reject(new Error('Connexion au serveur interrompue.')));
    request.addEventListener('abort', () => reject(new Error('Import annulé.')));
    request.send(file);
  });
}

async function handlePlanFile(file) {
  if (!file) return;
  const allowedType = /\.(pdf|png|jpe?g)$/i.test(file.name) && (!file.type || ['application/pdf', 'image/png', 'image/jpeg'].includes(file.type));
  if (!allowedType) {
    setImportStatus('Format refusé. Utilisez un fichier PDF, PNG ou JPEG.', 'error');
    return;
  }
  if (file.size > 100 * 1024 * 1024) {
    setImportStatus('Fichier trop volumineux : la limite est de 100 Mo.', 'error');
    return;
  }
  pendingPlanImport = null;
  setImportProgress('upload', 0);
  setImportStatus(`Import de « ${file.name} » en cours…`, 'busy');
  if (serverAvailable()) {
    document.querySelector('#save-status').textContent = 'Import du plan…';
    try {
      pendingPlanImport = await uploadPlanFile(file);
      if (!pendingPlanImport.previewUrl) throw new Error('Le serveur utilise encore une ancienne version du moteur d’import. Mettez ARCenal DRAW à jour dans YunoHost.');
      document.querySelector('#save-status').textContent = `Plan converti avec ${pendingPlanImport.conversion}`;
      setImportProgress('complete', 100);
      setImportStatus('Plan converti. Vérifiez maintenant son échelle.', 'success');
    } catch (error) {
      document.querySelector('#save-status').textContent = error.message;
      setImportProgress('hidden');
      setImportStatus(`Échec de l’import : ${error.message}`, 'error');
      return;
    }
  }
  openCalibration(file.name);
}
fileInput.addEventListener('change', async () => {
  if (fileInput.files[0]) await handlePlanFile(fileInput.files[0]);
  fileInput.value = '';
});
const dropZone = document.querySelector('#drop-zone');
['dragenter', 'dragover'].forEach((name) => dropZone.addEventListener(name, (event) => { event.preventDefault(); dropZone.classList.add('dragging'); }));
['dragleave', 'drop'].forEach((name) => dropZone.addEventListener(name, (event) => { event.preventDefault(); dropZone.classList.remove('dragging'); }));
dropZone.addEventListener('drop', (event) => {
  const file = event.dataTransfer.files[0];
  if (file) handlePlanFile(file);
});
document.querySelector('#project-search').addEventListener('input', () => renderRecentProjects(serverProjects));
document.querySelector('#archive-search').addEventListener('input', () => renderArchives(serverArchives));

applyTheme(loadSavedState()?.theme || state.theme);
renderRecentProjects();
renderArchives();
refreshServerLibrary();
