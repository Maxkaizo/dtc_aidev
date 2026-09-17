import { api } from './api.js';
import { calculate, categories } from './calculations.js';

const app = document.querySelector('#app');
let event, stage = 0, selected = '', modal = '', busy = false;
const steps = ['Grupos y asistentes', 'Gastos y aportaciones', 'Reparto de gastos', 'Quién paga a quién'];
const esc = value => String(value).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const money = cents => new Intl.NumberFormat('es-MX', { style: 'currency', currency: event?.currency || 'MXN' }).format(cents / 100);
const category = id => categories.find(c => c.id === id);
const groupName = id => esc(event.groups.find(g => g.id === id)?.name || '');
const badge = c => `<span class="badge ${c.color}">${c.icon} ${c.name}</span>`;
const empty = (title, detail) => `<div class="empty"><span>✧</span><h3>${title}</h3><p>${detail}</p></div>`;
function toast(message) { const node = document.querySelector('#toast'); node.textContent = message; node.classList.add('visible'); setTimeout(() => node.classList.remove('visible'), 4500); }
function header() { return `<header><a class="brand" href="/" aria-label="Chip In, inicio"><span class="logo">c<span>↗</span></span>chip in<span class="brand-dot">.</span></a><span class="header-note">Buenos momentos. Cuentas claras.</span><button class="quiet" data-action="new">＋ Nuevo evento</button></header>`; }
function render() {
  if (!event) {
    app.innerHTML = `${header()}<main class="landing"><div class="eyebrow">MENOS CUENTAS, MÁS MOMENTOS</div><h1>Compartir el plan.<br><em>También los gastos.</em></h1><p>Una comida, una escapada o una tarde entre amigos.<br>Junten los gastos y descubran cuánto le toca a cada quien.</p><div class="landing-actions"><button class="primary" data-action="new">Crear un evento <span>↗</span></button><button class="secondary" data-action="demo">Explorar un ejemplo</button></div><div class="illustration"><div class="paper"><span>EL PLAN DEL DOMINGO</span><h2>Todos ponen.<br>Todos disfrutan.</h2><div>◒ &nbsp; ♧ &nbsp; ✳</div><hr><small>La cuenta, en su justa medida. ✓</small></div><span class="sticker">¡Yo me<br>apunto!</span></div><p class="local-note">Comparte el enlace para organizar los gastos juntos.</p></main>`;
    showModal(); return;
  }
  const result = calculate(event);
  app.innerHTML = `${header()}<main><div class="event-heading"><div><div class="eyebrow"><span class="live-dot"></span> EL PLAN ESTÁ EN MARCHA</div><h1>${esc(event.name)}</h1><p>Disfruten juntos. Dividan justo.</p></div><button class="secondary" data-action="share">↗ Compartir evento</button></div><div class="event-meta"><span>◉ ${event.currency} · Moneda del evento</span><label>Estás participando como <select id="active-group" aria-label="Grupo actual"><option value="">Selecciona tu grupo</option>${event.groups.map(g => `<option value="${g.id}" ${selected === g.id ? 'selected' : ''}>${esc(g.name)}</option>`).join('')}</select></label></div><section class="stats"><div><span>Total del evento</span><strong>${money(result.total)} <small>${event.currency}</small></strong></div><div><span>Grupos en el plan</span><strong>${event.groups.length.toString().padStart(2, '0')} <small>grupos</small></strong></div><div><span>Personas que comparten</span><strong>${result.attendees.toString().padStart(2, '0')} <small>asistentes</small></strong></div><div class="stat-note"><span class="sun">✳</span><p>Cada quien aporta.<br><b>Las cuentas cuadran.</b></p></div></section><nav class="stages" aria-label="Etapas del evento">${steps.map((s, i) => `<button data-stage="${i}" class="${stage === i ? 'active' : ''}" ${stage === i ? 'aria-current="step"' : ''}><span>${i + 1}</span>${s}</button>`).join('')}</nav><section class="content">${[groupsView, expensesView, allocationView, settlementView][stage](result)}</section><footer><span class="mini-brand">chip in.</span><span>Hecho para compartir, sin complicaciones.</span><span>Evento compartido · Datos temporales</span></footer></main>`;
  showModal();
}
function title(kicker, heading, description, action = '') { return `<div class="section-title"><div><div class="eyebrow">${kicker}</div><h2>${heading}</h2><p>${description}</p></div>${action}</div>`; }
function groupsView(r) {
  return title('PASO 01 · LA BUENA COMPAÑÍA', '¿Quién se apunta?', 'Registra cada grupo y elige en qué participa cada persona.', '<button class="primary" data-action="group">＋ Agregar grupo</button>') + `<div class="two-col"><div class="group-grid">${r.groups.length ? r.groups.map((g, i) => `<article class="group-card"><div class="card-heading"><span class="avatar tone-${i % 3}">${esc(g.name.charAt(0).toUpperCase())}</span><div><h3>${esc(g.name)}</h3><p>Representante: ${esc(g.representative)}</p></div><span class="count">${g.attendees.length} pers.</span></div><div class="members">${g.attendees.map(a => `<div class="member"><strong>${esc(a.name)}</strong><div>${categories.filter(c => c.id === 'general' || a.categories.includes(c.id)).map(badge).join('')}</div></div>`).join('')}</div><button class="group-select ${g.id === selected ? 'chosen' : ''}" data-select="${g.id}">${g.id === selected ? '✓ Este es tu grupo' : 'Participar como este grupo →'}</button></article>`).join('') : empty('El plan empieza contigo', 'Agrega el primer grupo para empezar a compartir.')}<button class="add-card" data-action="group"><span>＋</span>Un lugar para tu grupo<small>Familia, pareja o solo tú</small></button></div><aside><h3>Cada quien elige su plan</h3><p>Los gastos se dividen entre quienes participan en cada categoría.</p>${r.allocation.map(c => `<div class="category-count"><span class="category-icon ${c.color}">${c.icon}</span><div><strong>${c.name}</strong><small>${c.id === 'general' ? 'Incluye a todos automáticamente' : 'Participación individual'}</small></div><b>${c.members.length}</b></div>`).join('')}<div class="tip">↳ ¿El representante también asiste?<br><span>Agrégalo una sola vez como asistente de su grupo.</span></div></aside></div>`;
}
function expensesView(r) {
  return title('PASO 02 · LO QUE PUSIMOS', 'Todo suma al plan', 'Registra cada compra en una sola categoría.', '<button class="primary" data-action="expense">＋ Agregar gasto</button>') + `<div class="category-totals">${r.allocation.map(c => `<div>${badge(c)}<strong>${money(c.total)}</strong></div>`).join('')}</div><div class="two-col"><div class="panel">${event.expenses.length ? `<div class="table-wrap"><table><thead><tr><th>Descripción</th><th>Categoría</th><th>Pagó</th><th class="numeric">Importe</th></tr></thead><tbody>${event.expenses.map(e => `<tr><td><strong>${esc(e.description)}</strong></td><td>${badge(category(e.category))}</td><td>${groupName(e.groupId)}</td><td class="numeric">${money(e.amount)}</td></tr>`).join('')}</tbody><tfoot><tr><td colspan="3">Total del evento</td><td class="numeric">${money(r.total)}</td></tr></tfoot></table></div>` : empty('Todavía no hay gastos', 'Registra la primera compra y haremos las cuentas.')}</div><aside><h3>Aportaciones por grupo</h3><p>Todo lo que cada grupo ha pagado.</p>${r.groups.map(g => `<div class="summary-row"><span>${esc(g.name)}</span><strong>${money(g.paid)}</strong></div>`).join('') || '<p>Primero registra un grupo.</p>'}<div class="tip">↳ ¿Una compra mezcla categorías?<br><span>Registra por separado el importe de cada una.</span></div></aside></div>`;
}
function allocationView(r) {
  return title('PASO 03 · A CADA QUIEN LO SUYO', 'Un reparto transparente', 'Partes iguales por persona, según las categorías en las que participa.') + `${r.blocked ? '<div class="warning" role="alert">Hay categorías con gastos y sin participantes. Registra asistentes en esas categorías para completar el reparto.</div>' : ''}<div class="two-col"><div class="allocation-list">${r.allocation.map(c => `<details class="panel" open><summary>${badge(c)}<span>${c.members.length} personas · <b>${money(c.total)}</b></span></summary><div class="allocation-body">${c.blocked ? '<p class="warning">No se puede repartir: no hay participantes en esta categoría.</p>' : `<p class="formula">${money(c.total)} ÷ ${c.members.length} personas = <strong>${money(c.base)}</strong> por persona${c.members.length ? '' : ' (sin gastos)'}</p>${c.remainder ? `<p class="rounding">Ajuste: +${money(1)} a las primeras ${c.remainder} personas en orden de registro, señaladas abajo.</p>` : ''}${r.groups.map(g => { const members = c.members.filter(m => m.groupId === g.id); return members.length ? `<div class="allocation-group"><div><strong>${esc(g.name)}</strong><b>${money(members.reduce((s, m) => s + m.charge, 0))}</b></div>${members.map(m => `<div class="allocation-member"><span>${esc(m.name)}${m.extra ? ' · +1 centavo' : ''}</span><span>${money(m.charge)}</span></div>`).join('')}</div>` : ''; }).join('')}`}</div></details>`).join('')}</div><aside><h3>${r.blocked ? 'Reparto parcial' : 'Total por grupo'}</h3><p>La suma de sus participaciones.</p>${r.groups.map(g => `<div class="summary-row"><span>${esc(g.name)}</span><strong>${money(g.share)}</strong></div>`).join('')}<div class="summary-row total"><span>Total asignado</span><strong>${money(r.groups.reduce((s, g) => s + g.share, 0))}</strong></div><div class="tip">✓ Cada centavo cuenta.<br><span>Los centavos sobrantes se asignan por orden de registro.</span></div></aside></div>`;
}
function settlementView(r) {
  return title('PASO 04 · CUENTAS CLARAS', 'Y ahora, ¿quién paga a quién?', 'Unos últimos movimientos y todos quedan a mano.') + (r.blocked ? '<div class="warning">Primero completa los participantes de las categorías pendientes en el reparto. Aún no se pueden calcular pagos.</div>' : `<div class="transfers">${r.transfers.length ? r.transfers.map((t, i) => `<article class="transfer"><span class="transfer-number">${i + 1}</span><div><small>TRANSFERENCIA SUGERIDA</small><h3>${groupName(t.from)} <span>→</span> ${groupName(t.to)}</h3><p>${esc(event.groups.find(g => g.id === t.from).representative)} paga a ${esc(event.groups.find(g => g.id === t.to).representative)}</p></div><strong>${money(t.amount)}</strong></article>`).join('') : empty(r.total ? '¡Todos están a mano!' : 'Las cuentas empiezan aquí', r.total ? 'No hacen falta transferencias entre los grupos.' : 'Agrega grupos y gastos para calcular los pagos.')}</div>`) + `<div class="panel table-wrap"><table><thead><tr><th>Grupo</th><th class="numeric">Pagó</th><th class="numeric">Le corresponde${r.blocked ? ' (parcial)' : ''}</th><th class="numeric">Balance</th></tr></thead><tbody>${r.groups.map(g => `<tr><td><strong>${esc(g.name)}</strong></td><td class="numeric">${money(g.paid)}</td><td class="numeric">${money(g.share)}</td><td class="numeric"><span class="balance ${g.balance > 0 ? 'receive' : ''}">${r.blocked ? 'Pendiente' : g.balance === 0 ? 'A mano' : `${g.balance > 0 ? 'Recibe' : 'Paga'} ${money(Math.abs(g.balance))}`}</span></td></tr>`).join('')}</tbody></table></div><p class="footnote">Estas son instrucciones sugeridas. Chip In no procesa pagos ni registra si se completaron.</p>`;
}
function attendeeRow() { return `<fieldset class="attendee-row"><legend>Asistente</legend><label>Nombre<input name="attendee" required maxlength="80" placeholder="Nombre de la persona"></label><div class="checkboxes">${categories.filter(c => c.id !== 'general').map(c => `<label><input type="checkbox" value="${c.id}" ${c.id === 'food' ? 'checked' : ''}>${c.name}</label>`).join('')}<span>✓ Gastos generales incluidos</span></div></fieldset>`; }
function showModal() {
  document.querySelector('dialog')?.remove();
  if (!modal) return;
  const dialog = document.createElement('dialog');
  const forms = {
    new: `<h2>Un nuevo plan</h2><p>Ponle nombre y elige la moneda que usarán todos.</p><label>Nombre del evento<input name="name" placeholder="Ej. Domingo entre amigos" required maxlength="100"></label><label>Moneda<select name="currency"><option value="MXN">MXN · Peso mexicano</option><option value="USD">USD · Dólar estadounidense</option><option value="EUR">EUR · Euro</option></select></label><p class="footnote">La moneda no se cambia después. Los datos se borran si se reinicia el servidor.</p>`,
    group: `<h2>Un grupo más al plan</h2><p>Una familia, una pareja o una persona sola.</p><label>Nombre del grupo<input name="name" required maxlength="80" placeholder="Ej. Familia de Ana"></label><label>Representante<input name="representative" required maxlength="80" placeholder="¿Quién representa al grupo?"></label><p class="form-hint">Si el representante asiste, inclúyelo una sola vez abajo. Todos los asistentes participan en gastos generales.</p><div id="attendees">${attendeeRow()}</div><button type="button" class="secondary" data-action="attendee">＋ Otro asistente</button>`,
    expense: `<h2>Agrega lo que pusieron</h2><p>Una compra, una categoría. Así de fácil.</p><label>Descripción<input name="description" required maxlength="120" placeholder="Ej. Comida para compartir"></label><label>Importe (${event?.currency})<input name="amount" type="text" inputmode="decimal" pattern="[0-9]+([.,][0-9]{1,2})?" required placeholder="0.00" title="Introduce un importe positivo con hasta dos decimales"></label><label>Categoría<select name="category">${categories.map(c => `<option value="${c.id}">${c.name}</option>`).join('')}</select></label><label>Grupo que pagó<select name="groupId" required><option value="">Selecciona un grupo</option>${event?.groups.map(g => `<option value="${g.id}" ${g.id === selected ? 'selected' : ''}>${esc(g.name)}</option>`).join('')}</select></label>`,
    share: `<h2>Un enlace para el plan</h2><p>Guarda este enlace para volver a tu evento.</p><label>Enlace del evento<input id="share-link" readonly value="${esc(location.href)}"></label><div class="warning">Cualquier persona con el enlace puede ver el evento y agregar grupos o gastos. Los datos se borran si se reinicia el servidor.</div><button class="primary" type="button" data-action="copy">Copiar enlace</button>`,
  };
  dialog.innerHTML = `<form id="modal-form"><button type="button" class="close" aria-label="Cerrar" data-action="close">×</button>${forms[modal]}<p id="form-error" role="alert"></p>${modal !== 'share' ? '<div class="form-actions"><button class="quiet" type="button" data-action="close">Cancelar</button><button class="primary" type="submit">Guardar →</button></div>' : ''}</form>`;
  document.body.append(dialog); dialog.showModal();
  dialog.addEventListener('close', () => { modal = ''; dialog.remove(); });
  dialog.querySelector('form').addEventListener('submit', submit);
}
async function submit(e) {
  e.preventDefault(); if (busy) return;
  busy = true; const submitButton = e.target.querySelector('[type="submit"]'); submitButton.disabled = true;
  const data = new FormData(e.target);
  try {
    if (modal === 'new') { event = await api.createEvent(data.get('name'), data.get('currency')); selected = ''; stage = 0; setUrl(); }
    if (modal === 'group') {
      const attendees = [...e.target.querySelectorAll('.attendee-row')].map(row => ({ name: row.querySelector('[name="attendee"]').value.trim(), categories: [...row.querySelectorAll('input:checked')].map(c => c.value) }));
      event = await api.addGroup(event.id, { name: data.get('name').trim(), representative: data.get('representative').trim(), attendees });
      selected = event.groups.at(-1).id; stage = 0;
    }
    if (modal === 'expense') {
      const [whole, fraction = ''] = data.get('amount').replace(',', '.').split('.');
      const amount = Number(whole) * 100 + Number(fraction.padEnd(2, '0'));
      event = await api.addExpense(event.id, { description: data.get('description').trim(), amount, category: data.get('category'), groupId: data.get('groupId') }); stage = 1;
    }
    modal = ''; render(); toast('Guardado. Las cuentas están actualizadas.');
  } catch (error) { e.target.querySelector('#form-error').textContent = error.message; }
  finally { busy = false; submitButton.disabled = false; }
}
function setUrl() { history.replaceState(null, '', `?event=${encodeURIComponent(event.id)}`); }
document.addEventListener('click', async e => {
  const button = e.target.closest('button'); if (!button) return;
  if (button.dataset.stage !== undefined) { stage = Number(button.dataset.stage); render(); return; }
  if (button.dataset.select) { selected = button.dataset.select; render(); return; }
  const action = button.dataset.action;
  if (action === 'close') { document.querySelector('dialog')?.close(); return; }
  if (action === 'attendee') { document.querySelector('#attendees').insertAdjacentHTML('beforeend', attendeeRow()); document.querySelector('#attendees').lastElementChild.querySelector('input').focus(); return; }
  if (action === 'copy') {
    try { await navigator.clipboard.writeText(location.href); toast('Enlace copiado'); }
    catch { document.querySelector('#share-link').select(); toast('Selecciona y copia el enlace manualmente.'); } return;
  }
  if (action === 'demo') {
    button.disabled = true;
    try { event = await api.createDemo(); selected = 'ana'; stage = 0; setUrl(); render(); } catch (error) { toast(error.message); button.disabled = false; } return;
  }
  if (['new', 'group', 'expense', 'share'].includes(action)) {
    if (action === 'expense' && !event.groups.length) { toast('Primero agrega un grupo para registrar sus gastos.'); return; }
    modal = action; showModal();
  }
});
document.addEventListener('change', e => { if (e.target.id === 'active-group') selected = e.target.value; });
// Refresh shared changes when returning to the page, without interrupting an open form.
window.addEventListener('focus', async () => {
  if (!event || modal || busy) return;
  const id = event.id;
  try {
    const latest = await api.getEvent(id);
    if (event?.id === id && !modal && !busy) { event = latest; render(); }
  } catch (error) { toast(error.message); }
});
const eventId = new URLSearchParams(location.search).get('event');
if (eventId) { app.innerHTML = '<main><p role="status">Cargando evento…</p></main>'; try { event = await api.getEvent(eventId); } catch (error) { toast(error.message); } }
render();
