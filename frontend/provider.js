// Provider portal handles bookings, services, availability, documents, shop and earnings.
'use strict';

var token = localStorage.getItem('petbridge_token');
var user = null;
try { user = JSON.parse(localStorage.getItem('petbridge_user') || 'null'); } catch (e) {}
if (!token || !user) window.location.href = './login.html';
if (user && user.role !== 'provider' && user.role !== 'admin') window.location.href = './index.html';

function $(id) { return document.getElementById(id); }
function el(tag, cls, text) { var n = document.createElement(tag); if (cls) n.className = cls; if (text != null) n.textContent = text; return n; }
function show(id, text, kind) { var n = $(id); if (!n) return; n.textContent = text; n.className = 'msg show ' + kind; }
function money(v) { if (v == null || v === '') return '-'; return Number(v).toLocaleString('en-US') + ' EGP'; }
function fmtDate(v) { if (!v) return '-'; try { return new Date(v).toLocaleString('en-GB'); } catch (e) { return String(v); } }
function chip(status) {
  var map = { approved: 'ok', active: 'ok', completed: 'ok', accepted: 'ok', pending: 'warn', proposed: 'warn', rejected: 'bad', cancelled: 'bad', suspended: 'bad' };
  var labels = { approved: 'Approved', active: 'Active', completed: 'Completed', accepted: 'Accepted', pending: 'Pending', proposed: 'Proposed', rejected: 'Rejected', cancelled: 'Cancelled', suspended: 'Suspended', placed: 'Placed', simulated: 'Simulated' };
  return el('span', 'chip ' + (map[status] || ''), labels[status] || status || '');
}
var MODE_LABELS = { onsite: 'At our place', home: "Client's home", online: 'Online', delivery: 'Delivery' };
function emptyRow(tbody, cols, title, text) {
  var tr = el('tr'); var td = el('td'); td.colSpan = cols;
  td.appendChild(el('strong', '', title)); td.appendChild(el('div', 'small', text));
  tr.appendChild(td); tbody.appendChild(tr);
}
async function api(path, options) {
  options = options || {};
  options.headers = Object.assign({ 'Authorization': 'Bearer ' + token }, options.headers || {});
  var res;
  try { res = await fetch(path, options); } catch (e) { throw new Error('Could not reach the server. Make sure the service is running, then reload the page.'); }
  var data = {}; try { data = await res.json(); } catch (e) {}
  if (res.status === 401) { localStorage.clear(); window.location.href = './login.html'; throw new Error('Session ended.'); }
  if (res.status === 403) throw new Error('Your account is not approved yet, or it does not have provider portal access.');
  if (!res.ok) throw new Error(data.error || data.message || 'The server returned an error.');
  return data;
}
function postJson(path, body) { return api(path, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body || {}) }); }

$('logout-btn').addEventListener('click', function () { localStorage.clear(); window.location.href = './login.html'; });
document.querySelectorAll('[data-scroll]').forEach(function (btn) {
  btn.addEventListener('click', function () {
    document.querySelectorAll('.side-link').forEach(function (b) { b.classList.remove('active'); });
    var nav = document.querySelector('.side-link[data-scroll="' + btn.getAttribute('data-scroll') + '"]');
    if (nav) nav.classList.add('active');
    var t = $(btn.getAttribute('data-scroll')); if (t) window.scrollTo({ top: t.offsetTop - 12, behavior: 'smooth' });
  });
});

var dash = null;

function fillBento(d, prov, s) {
  var bookings = d.bookings || [];
  var waiting = bookings.filter(function (b) { return b.status === 'pending' || b.status === 'proposed'; });

  // Large tile: the next request, with its accept action inside the tile.
  var next = waiting[0];
  var nextLine = $('next-pending');
  var quick = $('quick-accept');
  if (next) {
    nextLine.textContent = 'Next: ' + (next.service_name || 'Service') + ' — ' + (next.customer_name || next.client_name || 'Client') + ', ' + fmtDate(next.start_at) + ', ' + money(next.total);
    quick.hidden = false;
    quick.onclick = function () { bookingAction(next.id, 'accept', ''); };
  } else {
    nextLine.textContent = 'No pending booking right now. New requests land here first.';
    quick.hidden = true;
  }

  // Medium tile: pending requests with decisions inside the tile.
  var pend = $('pend-list'); pend.innerHTML = '';
  if (!waiting.length) {
    pend.appendChild(el('p', 'small', 'Nothing waiting. New booking requests will appear here with their accept and reject actions inside this tile.'));
  }
  waiting.slice(0, 3).forEach(function (b) {
    var row = el('div'); row.style.cssText = 'display:flex;justify-content:space-between;gap:.6rem;align-items:center;padding:.45rem 0;border-bottom:1px solid var(--tile2)';
    var info = el('div');
    info.appendChild(el('strong', '', b.service_name || 'Service'));
    info.appendChild(el('div', 'small', (b.customer_name || b.client_name || '') + ' · ' + fmtDate(b.start_at) + ' · ' + money(b.total)));
    row.appendChild(info);
    var acts = el('div'); acts.style.display = 'flex'; acts.style.gap = '.4rem';
    var acc = el('button', 'btn small', 'Accept'); acc.type = 'button';
    acc.addEventListener('click', function () { bookingAction(b.id, 'accept', ''); });
    var rej = el('button', 'btn small danger', 'Reject'); rej.type = 'button';
    rej.addEventListener('click', function () { bookingAction(b.id, 'reject', ''); });
    acts.appendChild(acc); acts.appendChild(rej);
    row.appendChild(acts);
    pend.appendChild(row);
  });

  // Medium tile spark bars: one bar per completed booking net, oldest to newest.
  var spark = $('earn-spark'); spark.innerHTML = '';
  var nets = bookings.filter(function (b) { return b.status === 'completed'; }).map(function (b) { return Number(b.provider_net != null ? b.provider_net : b.total) || 0; });
  if (!nets.length) {
    var flat = document.createElement('i'); flat.style.height = '12%'; flat.style.opacity = '.3'; spark.appendChild(flat);
  } else {
    var max = Math.max.apply(null, nets.concat([1]));
    nets.slice(-14).forEach(function (v) {
      var bar = document.createElement('i');
      bar.style.height = Math.max(6, Math.round((v / max) * 100)) + '%';
      spark.appendChild(bar);
    });
  }

  // Small tiles.
  $('st-orders').textContent = (d.orders || []).length;
  var checks = [
    ['approval', prov.status === 'approved' || prov.status === 'active'],
    ['services', (d.services || []).length > 0],
    ['open slots', (d.availability || []).length > 0],
    ['documents', (d.documents || []).length > 0]
  ];
  var done = checks.filter(function (c) { return c[1]; }).length;
  $('st-complete').textContent = done + ' / 4';
  var missing = checks.filter(function (c) { return !c[1]; }).map(function (c) { return c[0]; });
  $('st-complete-note').textContent = missing.length ? 'Still missing: ' + missing.join(', ') : 'Profile complete: approval, services, slots, documents';
}

function renderDashboard(d) {
  dash = d;
  var prov = d.provider || {};
  $('biz-name').textContent = prov.business_name || user.name || 'My business';
  $('biz-meta').textContent = [prov.kind, prov.city, prov.area, prov.status ? 'Approval status: ' + prov.status : ''].filter(Boolean).join(', ');
  if (prov.status && prov.status !== 'approved' && prov.status !== 'active') {
    show('status-note', 'Your business status is currently: ' + prov.status + '. Some studio actions stay limited until the admins approve the account and its documents.', 'info');
  }
  var s = d.stats || {};
  $('st-pending').textContent = s.pending_bookings != null ? s.pending_bookings : '-';
  $('st-accepted').textContent = s.accepted_bookings != null ? s.accepted_bookings : '-';
  $('st-completed').textContent = s.completed_bookings != null ? s.completed_bookings : '-';
  $('st-rating').textContent = s.rating != null ? s.rating : 'No reviews yet';
  $('st-gross').textContent = money(s.gross); $('st-commission').textContent = money(s.commission); $('st-net').textContent = money(s.net);
  $('st-services').textContent = (d.services || []).length;
  fillBento(d, prov, s);

  var earn = d.earnings || s;
  $('earn-gross').textContent = money(earn.gross); $('earn-comm').textContent = money(earn.commission); $('earn-net').textContent = money(earn.net);

  var bb = $('bookings-body'); bb.innerHTML = '';
  var bookings = d.bookings || [];
  if (!bookings.length) emptyRow(bb, 6, 'No incoming bookings yet', 'When a client books any of your published services it will appear here for you to accept, reject, or answer with an alternative time.');
  bookings.forEach(function (b) {
    var tr = el('tr');
    tr.appendChild(el('td', '', b.service_name || 'Service'));
    var who = el('td'); who.appendChild(el('div', '', b.customer_name || b.client_name || '')); who.appendChild(el('div', 'small', b.pet_name ? 'Pet: ' + b.pet_name : '')); tr.appendChild(who);
    var when = el('td'); when.appendChild(el('div', 'mono', fmtDate(b.start_at))); if (b.proposed_start_at) when.appendChild(el('div', 'small', 'Proposed: ' + fmtDate(b.proposed_start_at))); tr.appendChild(when);
    var st = el('td'); st.appendChild(chip(b.status)); tr.appendChild(st);
    tr.appendChild(el('td', 'money', money(b.total) + (b.provider_net != null ? ' · net ' + money(b.provider_net) : '')));
    var acts = el('td');
    if (b.status === 'pending' || b.status === 'proposed') {
      var prop = el('input'); prop.type = 'datetime-local'; prop.style.marginBottom = '.35rem'; prop.title = 'Proposed alternative time';
      acts.appendChild(prop);
      [['accept', 'Accept'], ['reject', 'Reject'], ['propose', 'Propose time']].forEach(function (pair) {
        var btn = el('button', 'btn small' + (pair[0] === 'reject' ? ' danger' : pair[0] === 'propose' ? ' ghost' : ''), pair[1]); btn.type = 'button';
        btn.addEventListener('click', function () { bookingAction(b.id, pair[0], prop.value); });
        acts.appendChild(btn); acts.appendChild(document.createTextNode(' '));
      });
    }
    if (b.status === 'accepted') {
      var done = el('button', 'btn small', 'Mark completed'); done.type = 'button';
      done.addEventListener('click', function () { bookingAction(b.id, 'complete', ''); });
      acts.appendChild(done);
    }
    if (!acts.childNodes.length) acts.appendChild(el('span', 'small', 'No action available'));
    tr.appendChild(acts);
    bb.appendChild(tr);
  });

  var sb = $('services-body'); sb.innerHTML = '';
  (d.services || []).forEach(function (s2) {
    var tr = el('tr');
    tr.appendChild(el('td', '', s2.name || '')); tr.appendChild(el('td', '', s2.category || s2.taxonomy_key || ''));
    tr.appendChild(el('td', 'money', money(s2.price))); tr.appendChild(el('td', '', (s2.duration_min || '-') + ' min, ' + (MODE_LABELS[s2.mode] || s2.mode || '')));
    sb.appendChild(tr);
  });
  if (!(d.services || []).length) emptyRow(sb, 4, 'No services published', 'Add your first service from the form and it will appear to clients in the directory with your availability.');

  var ab = $('avail-body'); ab.innerHTML = '';
  var avail = d.availability || [];
  avail.forEach(function (a) {
    var tr = el('tr');
    tr.appendChild(el('td', 'mono', a.date || '')); tr.appendChild(el('td', 'mono', (a.start_time || '') + ' to ' + (a.end_time || '')));
    tr.appendChild(el('td', 'mono', String(a.capacity != null ? a.capacity : '-'))); tr.appendChild(el('td', 'mono', String(a.booked != null ? a.booked : 0)));
    ab.appendChild(tr);
  });
  if (!avail.length) emptyRow(ab, 4, 'No open availability', 'Open your first slot with a date, time and capacity, and it becomes bookable inside your services.');

  var docs = $('docs-list'); docs.innerHTML = '';
  var docItems = d.documents || [];
  if (!docItems.length) { var e = el('div', 'empty'); e.appendChild(el('h3', '', 'No documents registered')); e.appendChild(el('p', '', 'Register the business licence, ID and any professional certificates. The admins review this list at approval and renewal.')); docs.appendChild(e); }
  docItems.forEach(function (doc) {
    var c = el('div', 'booking-line');
    var m = el('div'); m.appendChild(el('strong', '', doc.label || doc.doc_type || 'Document')); m.appendChild(el('div', 'small', doc.file_name || ''));
    c.appendChild(m); var side = el('div'); side.appendChild(chip(doc.status || 'pending')); c.appendChild(side); docs.appendChild(c);
  });

  var pb = $('products-body'); pb.innerHTML = '';
  (d.products || []).forEach(function (p) {
    var tr = el('tr'); tr.appendChild(el('td', '', p.name || '')); tr.appendChild(el('td', 'money', money(p.price))); tr.appendChild(el('td', 'mono', String(p.stock != null ? p.stock : '-')));
    var st = el('td'); st.appendChild(chip(p.status || 'active')); tr.appendChild(st); pb.appendChild(tr);
  });
  if (!(d.products || []).length) emptyRow(pb, 4, 'No products in the shop', 'If your business is a shop, add your products with prices and stock and they will be offered to clients in the platform shop.');

  var ob = $('orders-body'); ob.innerHTML = '';
  var orders = d.orders || [];
  if (!orders.length) emptyRow(ob, 5, 'No incoming shop orders', 'Client orders on your products will appear here with quantity, total and status.');
  orders.forEach(function (o) {
    var tr = el('tr');
    tr.appendChild(el('td', '', o.product_name || o.name || 'Product')); tr.appendChild(el('td', '', o.customer_name || ''));
    tr.appendChild(el('td', 'mono', String(o.qty || 1))); tr.appendChild(el('td', 'money', money(o.total)));
    var st = el('td'); st.appendChild(chip(o.status || 'simulated')); tr.appendChild(st); ob.appendChild(tr);
  });

  var rv = $('reviews-list'); rv.innerHTML = '';
  var reviews = d.reviews || [];
  if (!reviews.length) { var e2 = el('div', 'empty'); e2.appendChild(el('h3', '', 'No reviews yet')); e2.appendChild(el('p', '', 'Client reviews linked to completed bookings will appear here with your overall average.')); rv.appendChild(e2); }
  reviews.forEach(function (r) {
    var c = el('div', 'booking-line'); var m = el('div'); m.appendChild(el('strong', '', r.customer_name || 'Client')); m.appendChild(el('div', 'small', r.comment || r.body || '')); c.appendChild(m); c.appendChild(el('span', 'stars', 'Rating: ' + (r.rating || '') + ' of 5')); rv.appendChild(c);
  });
}

async function bookingAction(id, action, proposed) {
  if (action === 'propose' && !proposed) { show('booking-msg', 'Choose an alternative time in the date and time field inside the booking row before sending the proposal.', 'error'); return; }
  try {
    var body = { action: action };
    if (action === 'propose') body.proposed_start_at = proposed;
    await postJson('/api/provider/bookings/' + id + '/action', body);
    show('booking-msg', 'Done — the booking was updated.', 'success'); load();
  } catch (e) { show('booking-msg', e.message, 'error'); }
}

async function load() {
  try { var d = await api('/api/provider/dashboard'); renderDashboard(d); }
  catch (e) { show('page-error', e.message, 'error'); }
}
async function loadTaxonomy() {
  try {
    var d = await api('/api/taxonomy'); var sel = $('svc-tax'); sel.innerHTML = '';
    (d.categories || []).forEach(function (cat) {
      var group = document.createElement('optgroup'); group.label = cat.label || cat.key;
      (cat.services || []).forEach(function (s) { var o = el('option', '', s.label || s.key); o.value = s.key; group.appendChild(o); });
      sel.appendChild(group);
    });
  } catch (e) { show('page-error', 'The service taxonomy could not be loaded: ' + e.message, 'error'); }
}

$('service-form').addEventListener('submit', async function (ev) {
  ev.preventDefault();
  try {
    await postJson('/api/provider/services', { taxonomy_key: $('svc-tax').value, name: $('svc-name').value.trim(), price: Number($('svc-price').value), duration_min: Number($('svc-duration').value), mode: $('svc-mode').value });
    show('service-msg', 'The service was published and appears in your list, and in the directory according to its review status.', 'success'); ev.target.reset(); load();
  } catch (e) { show('service-msg', e.message, 'error'); }
});
$('avail-form').addEventListener('submit', async function (ev) {
  ev.preventDefault();
  try {
    await postJson('/api/provider/availability', { date: $('av-date').value, start_time: $('av-start').value, end_time: $('av-end').value, capacity: Number($('av-cap').value) });
    show('avail-msg', 'The slot was opened and is now bookable.', 'success'); ev.target.reset(); load();
  } catch (e) { show('avail-msg', e.message, 'error'); }
});
$('doc-form').addEventListener('submit', async function (ev) {
  ev.preventDefault();
  try {
    await postJson('/api/provider/documents', { doc_type: $('doc-type').value.trim(), label: $('doc-label').value.trim(), file_name: $('doc-file').value.trim() });
    show('doc-msg', 'The document was registered and is visible to the admins.', 'success'); ev.target.reset(); load();
  } catch (e) { show('doc-msg', e.message, 'error'); }
});
$('product-form').addEventListener('submit', async function (ev) {
  ev.preventDefault();
  try {
    await postJson('/api/provider/products', { name: $('prod-name').value.trim(), description: $('prod-desc').value.trim(), price: Number($('prod-price').value), stock: Number($('prod-stock').value) });
    show('product-msg', 'The product was published according to the admin review status.', 'success'); ev.target.reset(); load();
  } catch (e) { show('product-msg', e.message, 'error'); }
});

loadTaxonomy(); load();

