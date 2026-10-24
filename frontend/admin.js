// Admin portal covers approvals, users, moderation, operations, audit and settings.
'use strict';

var token = localStorage.getItem('petbridge_token');
var user = null;
try { user = JSON.parse(localStorage.getItem('petbridge_user') || 'null'); } catch (e) {}
if (!token || !user) window.location.href = './login.html';
if (user && user.role !== 'admin') window.location.href = './index.html';

function $(id) { return document.getElementById(id); }
function el(tag, cls, text) { var n = document.createElement(tag); if (cls) n.className = cls; if (text != null) n.textContent = text; return n; }
function show(id, text, kind) { var n = $(id); if (!n) return; n.textContent = text; n.className = 'msg show ' + kind; }
function money(v) { if (v == null || v === '') return '-'; return Number(v).toLocaleString('en-US') + ' EGP'; }
function fmtDate(v) { if (!v) return '-'; try { return new Date(v).toLocaleString('en-GB'); } catch (e) { return String(v); } }
var STATUS_LABELS = { approved: 'Approved', active: 'Active', completed: 'Completed', accepted: 'Accepted', pending: 'Pending', open: 'Open', proposed: 'Proposed', rejected: 'Rejected', hidden: 'Hidden', suspended: 'Suspended', cancelled: 'Cancelled', placed: 'Placed', simulated: 'Simulated' };
function chip(status) {
  return el('span', 'chip', STATUS_LABELS[status] || status || '');
}
function emptyRow(tbody, cols, title, text) {
  var tr = el('tr'); var td = el('td'); td.colSpan = cols;
  td.appendChild(el('strong', '', title)); td.appendChild(el('div', 'small', text)); tr.appendChild(td); tbody.appendChild(tr);
}
async function api(path, options) {
  options = options || {};
  options.headers = Object.assign({ 'Authorization': 'Bearer ' + token }, options.headers || {});
  var res;
  try { res = await fetch(path, options); } catch (e) { throw new Error('Could not reach the server. Make sure the service is running, then reload the page.'); }
  var data = {}; try { data = await res.json(); } catch (e) {}
  if (res.status === 401) { localStorage.clear(); window.location.href = './login.html'; throw new Error('Session ended.'); }
  if (res.status === 403) throw new Error('This account does not have platform admin access.');
  if (!res.ok) throw new Error(data.error || data.message || 'The server returned an error.');
  return data;
}
function postJson(path, body) { return api(path, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body || {}) }); }

$('logout-btn').addEventListener('click', function () { localStorage.clear(); window.location.href = './login.html'; });
document.querySelectorAll('[data-scroll]').forEach(function (btn) {
  btn.addEventListener('click', function () {
    document.querySelectorAll('[data-scroll]').forEach(function (b) { b.classList.remove('active'); });
    btn.classList.add('active');
    var t = $(btn.getAttribute('data-scroll')); if (t) window.scrollTo({ top: t.offsetTop - 12, behavior: 'smooth' });
  });
});

function decisionButtons(entity, id, refreshMsgId) {
  var cell = el('td');
  [['approved', 'Approve'], ['rejected', 'Reject']].forEach(function (pair) {
    var btn = el('button', 'btn small ' + (pair[0] === 'approved' ? 'approve' : 'danger'), pair[1]); btn.type = 'button';
    btn.setAttribute('data-decision', pair[0]);
    btn.addEventListener('click', async function () {
      var reason = '';
      if (pair[0] === 'rejected') { reason = window.prompt('Reason for rejection, saved with the decision:') || ''; }
      try {
        await postJson('/api/admin/approve', { entity: entity, id: id, decision: pair[0], reason: reason });
        show(refreshMsgId, 'Decision saved: ' + pair[1] + '. It is written in the audit rail.', 'success'); load();
      } catch (e) { show(refreshMsgId, e.message, 'error'); }
    });
    cell.appendChild(btn); cell.appendChild(document.createTextNode(' '));
  });
  return cell;
}

function render(d) {
  var k = d.kpis || {};
  var strip = $('kpi-strip'); strip.innerHTML = '';
  [['Users', k.users], ['Clients', k.customers], ['Providers', k.providers], ['Providers awaiting approval', k.pending_providers], ['Open reports', k.open_reports]].forEach(function (p) {
    var c = el('div', 'kpi'); c.appendChild(el('b', '', String(p[1] != null ? p[1] : '-'))); c.appendChild(el('span', '', p[0])); strip.appendChild(c);
  });
  var strip2 = $('kpi-strip-2'); strip2.innerHTML = '';
  [['All bookings', k.bookings], ['Completed bookings', k.completed_bookings], ['Store orders', k.orders], ['Platform gross movement', money(k.gross_total)], ['Platform commissions', money(k.commission_total)]].forEach(function (p) {
    var c = el('div', 'kpi'); c.appendChild(el('b', '', String(p[1] != null ? p[1] : '-'))); c.appendChild(el('span', '', p[0])); strip2.appendChild(c);
  });

  var q = d.queues || {};
  var qp = $('q-providers'); qp.innerHTML = '';
  var provs = q.providers || [];
  if (!provs.length) { emptyRow(qp, 4, 'Provider queue is empty', 'No approval requests are pending. New registrations appear here at once, with their documents.'); $('q-providers-empty').innerHTML = ''; }
  provs.forEach(function (p) {
    var tr = el('tr');
    tr.appendChild(el('td', '', p.business_name || p.name || ''));
    tr.appendChild(el('td', '', [p.kind, p.city, p.area].filter(Boolean).join(', ')));
    var st = el('td'); st.appendChild(chip(p.status || 'pending')); tr.appendChild(st);
    tr.appendChild(decisionButtons('provider', p.id, 'queue-msg'));
    qp.appendChild(tr);
  });
  var qs = $('q-services'); qs.innerHTML = '';
  var svcs = q.services || [];
  if (!svcs.length) emptyRow(qs, 4, 'No services pending', 'New or edited services that need review appear here before approval.');
  svcs.forEach(function (s) {
    var tr = el('tr'); tr.appendChild(el('td', '', s.name || '')); tr.appendChild(el('td', '', s.business_name || s.provider_name || '')); tr.appendChild(el('td', 'mono', money(s.price))); tr.appendChild(decisionButtons('service', s.id, 'queue-msg')); qs.appendChild(tr);
  });
  var qpr = $('q-products'); qpr.innerHTML = '';
  var prods = q.products || [];
  if (!prods.length) emptyRow(qpr, 4, 'No products pending', 'New shop products that need review appear here.');
  prods.forEach(function (p) {
    var tr = el('tr'); tr.appendChild(el('td', '', p.name || '')); tr.appendChild(el('td', '', p.provider_name || p.business_name || '')); tr.appendChild(el('td', 'mono', money(p.price) + ', stock ' + (p.stock != null ? p.stock : '-'))); tr.appendChild(decisionButtons('product', p.id, 'queue-msg')); qpr.appendChild(tr);
  });

  var ub = $('users-body'); ub.innerHTML = '';
  var users = d.users || [];
  if (!users.length) emptyRow(ub, 5, 'No users', 'Client, provider and admin accounts appear here with their status and suspend or reactivate actions.');
  users.forEach(function (u) {
    var tr = el('tr');
    tr.appendChild(el('td', '', u.name || ''));
    var contact = el('td'); contact.appendChild(el('div', '', u.email || '')); contact.appendChild(el('div', 'small mono', u.phone || '')); tr.appendChild(contact);
    tr.appendChild(el('td', '', (u.role || '') + (u.admin_level ? ', ' + u.admin_level : '')));
    var st = el('td'); st.appendChild(chip(u.status || 'active')); tr.appendChild(st);
    var acts = el('td');
    var targetStatus = u.status === 'suspended' ? 'active' : 'suspended';
    var btn = el('button', 'btn small' + (targetStatus === 'suspended' ? ' danger' : ''), targetStatus === 'suspended' ? 'Suspend account' : 'Reactivate'); btn.type = 'button';
    btn.addEventListener('click', async function () {
      try { await postJson('/api/admin/users/' + u.id + '/status', { status: targetStatus }); show('user-msg', 'Account status updated.', 'success'); load(); }
      catch (e) { show('user-msg', e.message, 'error'); }
    });
    acts.appendChild(btn); tr.appendChild(acts); ub.appendChild(tr);
  });

  var pb2 = $('posts-body'); pb2.innerHTML = '';
  var posts = d.posts || [];
  if (!posts.length) emptyRow(pb2, 4, 'No community posts', 'Community posts appear here so you can hide rule-breaking ones or warn their authors.');
  posts.forEach(function (p) {
    var tr = el('tr');
    var title = el('td'); title.appendChild(el('strong', '', p.title || '')); title.appendChild(el('div', 'small', p.body || '')); if (p.status) { title.appendChild(document.createTextNode(' ')); title.appendChild(chip(p.status)); } tr.appendChild(title);
    tr.appendChild(el('td', '', p.author_name || '')); tr.appendChild(el('td', 'mono', fmtDate(p.created_at)));
    var acts = el('td');
    [['hide', 'Hide'], ['warn', 'Warn author']].forEach(function (pair) {
      var btn = el('button', 'btn small ghost', pair[1]); btn.type = 'button';
      btn.addEventListener('click', async function () {
        try { await postJson('/api/admin/posts/' + p.id + '/moderate', { action: pair[0] }); show('mod-msg', 'Moderation action applied.', 'success'); load(); }
        catch (e) { show('mod-msg', e.message, 'error'); }
      });
      acts.appendChild(btn); acts.appendChild(document.createTextNode(' '));
    });
    tr.appendChild(acts); pb2.appendChild(tr);
  });

  var rep = $('reports-list'); rep.innerHTML = '';
  var reports = d.reports || [];
  if (!reports.length) { var e = el('div', 'empty'); e.appendChild(el('h3', '', 'No open reports')); e.appendChild(el('p', '', 'User reports about posts or rule-breaking content appear here with the report reason.')); rep.appendChild(e); }
  reports.forEach(function (r) {
    var c = el('div', 'booking-line warn'); var m = el('div'); m.appendChild(el('strong', '', r.reason || r.title || 'Report')); m.appendChild(el('div', 'small', [r.reporter_name || '', r.post_title || '', fmtDate(r.created_at)].filter(Boolean).join(', '))); c.appendChild(m); var s = el('div'); s.appendChild(chip(r.status || 'open')); c.appendChild(s); rep.appendChild(c);
  });

  var bk = $('bookings-body'); bk.innerHTML = '';
  var bookings = d.bookings || [];
  if (!bookings.length) emptyRow(bk, 5, 'No bookings on the platform yet', 'All client bookings appear here with their total, platform commission and provider net, for oversight and settlement.');
  bookings.forEach(function (b) {
    var tr = el('tr'); tr.appendChild(el('td', '', b.service_name || ''));
    tr.appendChild(el('td', '', [b.customer_name || '', b.business_name || ''].filter(Boolean).join(', ')));
    tr.appendChild(el('td', 'mono', fmtDate(b.start_at)));
    var st = el('td'); st.appendChild(chip(b.status || '')); tr.appendChild(st);
    tr.appendChild(el('td', 'mono', money(b.total) + ' · commission ' + money(b.commission) + ' · net ' + money(b.provider_net)));
    bk.appendChild(tr);
  });

  var au = $('audit-body'); au.innerHTML = '';
  var audit = d.audit || [];
  if (!audit.length) emptyRow(au, 4, 'Audit log is empty', 'Important admin and user actions are recorded here automatically and cannot be edited from the interface.');
  audit.forEach(function (a) {
    var tr = el('tr');
    tr.appendChild(el('td', '', fmtDate(a.created_at || a.at)));
    tr.appendChild(el('td', '', a.actor_name || a.actor || a.user_name || ''));
    tr.appendChild(el('td', '', a.action || a.event || ''));
    tr.appendChild(el('td', '', a.details || a.detail || a.entity || ''));
    au.appendChild(tr);
  });
}

async function load() {
  try { var d = await api('/api/admin/dashboard'); render(d); }
  catch (e) { show('page-error', e.message, 'error'); }
}
async function loadSettings() {
  try {
    var s = await api('/api/admin/settings');
    var rate = s.commission_rate != null ? s.commission_rate : (s.settings && s.settings.commission_rate);
    if (rate != null) $('commission-rate').value = rate;
    var extra = [];
    Object.keys(s).forEach(function (key) { if (key !== 'commission_rate') extra.push(key + ': ' + (typeof s[key] === 'object' ? JSON.stringify(s[key]) : s[key])); });
    $('settings-extra').textContent = extra.join(', ');
  } catch (e) { show('settings-msg', e.message, 'error'); }
}
$('settings-form').addEventListener('submit', async function (ev) {
  ev.preventDefault();
  try { await postJson('/api/admin/settings', { commission_rate: Number($('commission-rate').value) }); show('settings-msg', 'Commission rate saved. It applies to new bookings from now on.', 'success'); }
  catch (e) { show('settings-msg', e.message, 'error'); }
});

if (user) $('admin-meta').textContent = (user.name || user.email || '') + (user.admin_level ? ' · admin level: ' + user.admin_level : '');
load(); loadSettings();
