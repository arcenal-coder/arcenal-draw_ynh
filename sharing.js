const shareDialog = document.querySelector('#share-dialog');
const shareStatus = document.querySelector('#share-status');
const shareCode = document.querySelector('#share-code');
let shareProjectId = null;

function showShareInfo(info) {
  document.querySelector('#share-result').hidden = !info;
  document.querySelector('#revoke-share').hidden = !info?.enabled;
  document.querySelector('#share-expiry').value = info?.expires_at ? new Date(info.expires_at * 1000).toISOString().slice(0, 10) : '';
  if (!info) return;
  const url = new URL('consultation/', window.location.href);
  url.hash = info.id;
  document.querySelector('#share-link').value = url.href;
  document.querySelector('#share-generated-row').hidden = !info.accessCode;
  document.querySelector('#share-generated-code').value = info.accessCode || '';
  shareStatus.textContent = info.enabled ? `Dernière publication : ${new Date(info.publishedAt * 1000).toLocaleString('fr-FR')}. Le lien reste identique après chaque publication.` : 'Ce lien est révoqué. Publiez à nouveau pour le réactiver.';
  document.querySelector('#publish-share').textContent = info.enabled ? 'Mettre à jour la consultation' : 'Publier la consultation';
}

function capturePublishedOverlay() {
  const selected = [...mapLayer.querySelectorAll('.selected')];
  selected.forEach((node) => node.classList.remove('selected'));
  const root = document.createElementNS(NS, 'svg');
  const definitions = document.createElementNS(NS, 'defs');
  definitions.innerHTML = '<clipPath id="impact-image-clip"><circle r="2"/></clipPath>';
  root.append(definitions);
  const allowed = new Set(['x', 'y', 'x1', 'y1', 'x2', 'y2', 'cx', 'cy', 'r', 'rx', 'ry', 'width', 'height', 'd', 'transform', 'fill', 'stroke', 'stroke-width', 'fill-opacity', 'opacity', 'stroke-dasharray', 'font-size', 'font-family', 'font-weight', 'text-anchor', 'dominant-baseline', 'preserveAspectRatio', 'clip-path', 'vector-effect']);
  const numeric = new Set(['stroke-width', 'font-size', 'fill-opacity', 'opacity']);
  const styleNames = ['fill', 'stroke', 'stroke-width', 'fill-opacity', 'opacity', 'stroke-dasharray', 'font-size', 'font-family', 'font-weight', 'text-anchor', 'dominant-baseline', 'vector-effect'];
  function copy(source) {
    if (source.matches('#plan-preview,#scale-layer,.selection-ring,.measurement-hit,.measurement-anchor,.measurement-preview')) return null;
    const target = document.createElementNS(NS, source.localName);
    for (const attribute of source.attributes) {
      const name = attribute.localName;
      if (allowed.has(name)) target.setAttribute(name, attribute.value);
      if (name === 'href') target.setAttribute('href', attribute.value);
    }
    if (source.matches('circle,line,path,rect,text,tspan')) {
      const style = getComputedStyle(source);
      for (const name of styleNames) {
        let value = style.getPropertyValue(name).trim();
        if (!value) continue;
        if (numeric.has(name)) value = String(parseFloat(value));
        if (name === 'stroke-dasharray') value = value.replaceAll('px', '');
        target.setAttribute(name, value);
      }
    }
    let point = source.hasAttribute('data-x') ? { x: source.dataset.x, y: source.dataset.y } : null;
    if (source.matches('.signal-item')) {
      const signal = state.signals.find((item) => item.id === source.dataset.signalId);
      if (signal) point = { x: signal.x, y: signal.y };
    }
    if (point) {
      target.setAttribute('data-fixed', '1'); target.setAttribute('data-x', point.x); target.setAttribute('data-y', point.y);
      target.setAttribute('transform', `translate(${point.x} ${point.y}) scale(1)`);
    }
    for (const child of source.childNodes) {
      if (child.nodeType === Node.TEXT_NODE) target.append(document.createTextNode(child.textContent));
      if (child.nodeType === Node.ELEMENT_NODE) { const copied = copy(child); if (copied) target.append(copied); }
    }
    return target;
  }
  try {
    for (const layer of [overzoneLayer, zoneLayer, impactLayer, signalLayer, measurementLayer]) root.append(copy(layer));
    return new XMLSerializer().serializeToString(root);
  } finally { selected.forEach((node) => node.classList.add('selected')); }
}

document.querySelector('#share-button').addEventListener('click', async () => {
  shareCode.value = '';
  document.querySelector('#share-generated-code').value = '';
  document.querySelector('#share-generated-row').hidden = true;
  showShareInfo(null);
  shareStatus.textContent = 'Chargement du partage…';
  shareDialog.showModal();
  if (!serverAvailable()) { shareStatus.textContent = 'La publication est disponible depuis votre installation YunoHost.'; document.querySelector('#publish-share').disabled = true; return; }
  shareProjectId = state.projectId;
  document.querySelector('#publish-share').disabled = false;
  try {
    await apiRequest(`projects/${encodeURIComponent(shareProjectId)}`, { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(state) });
    const result = await apiRequest(`projects/${encodeURIComponent(shareProjectId)}/consultation`);
    showShareInfo(result.share);
    if (!result.share) shareStatus.textContent = 'Aucune consultation publiée pour ce projet.';
  } catch (error) { shareStatus.textContent = error.message; document.querySelector('#publish-share').disabled = true; }
});

document.querySelector('#share-form').addEventListener('submit', async (event) => {
  event.preventDefault();
  if (shareProjectId !== state.projectId) { shareStatus.textContent = 'Le projet a changé. Fermez puis rouvrez ce dialogue.'; return; }
  const submit = document.querySelector('#publish-share');
  submit.disabled = true;
  document.querySelector('#revoke-share').disabled = true;
  shareStatus.textContent = 'Publication en cours…';
  try {
    const snapshot = JSON.parse(JSON.stringify(state));
    const overlaySvg = capturePublishedOverlay();
    const result = await apiRequest(`projects/${encodeURIComponent(shareProjectId)}/consultation`, { method: 'POST', headers: { 'Content-Type': 'application/json', 'X-Crobard-Publish': '1' }, body: JSON.stringify({ snapshot, overlaySvg, accessCode: shareCode.value, expiresOn: document.querySelector('#share-expiry').value || null }) });
    shareCode.value = '';
    showShareInfo(result.share);
  } catch (error) { shareStatus.textContent = `Publication impossible : ${error.message}`; }
  finally { submit.disabled = false; document.querySelector('#revoke-share').disabled = false; }
});
document.querySelector('#revoke-share').addEventListener('click', async () => {
  if (!window.confirm('Révoquer ce lien et fermer les accès à la consultation client ?')) return;
  try {
    await apiRequest(`projects/${encodeURIComponent(shareProjectId)}/consultation`, { method: 'DELETE', headers: { 'X-Crobard-Publish': '1' } });
    const result = await apiRequest(`projects/${encodeURIComponent(shareProjectId)}/consultation`);
    showShareInfo(result.share);
  } catch (error) { shareStatus.textContent = error.message; }
});
document.querySelector('#copy-share-link').addEventListener('click', async () => {
  try { await navigator.clipboard.writeText(document.querySelector('#share-link').value); shareStatus.textContent = 'Lien copié. Transmettez le code séparément.'; }
  catch { shareStatus.textContent = 'Sélectionnez le lien puis utilisez Copier sur votre appareil.'; document.querySelector('#share-link').select(); }
});
document.querySelector('#close-share').onclick = () => shareDialog.close();
shareDialog.addEventListener('close', () => { shareCode.value = ''; document.querySelector('#share-generated-code').value = ''; });
