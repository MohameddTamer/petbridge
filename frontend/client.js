// Client portal wires the home, directory, bookings and community sections.
'use strict';

var token = localStorage.getItem('petbridge_token');
var user = null;
try { user = JSON.parse(localStorage.getItem('petbridge_user') || 'null'); } catch (e) {}
if (!token || !user) window.location.href = './login.html';

var state = { pets: [], taxonomy: [] };

function $(id) { return document.getElementById(id); }
function el(tag, cls, text) {
  var n = document.createElement(tag);
  if (cls) n.className = cls;
  if (text != null) n.textContent = text;
  return n;
}
function show(id, text, kind) {
  var n = $(id); if (!n) return;
  n.textContent = text; n.className = 'msg show ' + kind;
}
function hide(id) { var n = $(id); if (n) n.className = 'msg'; }
function money(v) { if (v == null || v === '') return 'Not set'; return Number(v).toLocaleString('en-US') + ' EGP'; }
function fmtDate(v) { if (!v) return 'Not set'; try { return new Date(v).toLocaleString('en-GB'); } catch (e) { return String(v); } }
var STATUS_LABELS = { active: 'Active', approved: 'Approved', completed: 'Completed', accepted: 'Accepted', available: 'Available', pending: 'Pending', proposed: 'New time proposed', open: 'Open', lost: 'Lost', overdue: 'Overdue', due_soon: 'Due soon', cancelled: 'Cancelled', rejected: 'Rejected', hidden: 'Hidden', suspended: 'Suspended', found: 'Found', paid: 'Paid', simulated: 'Simulated', placed: 'Placed' };
function statusChip(status) {
  var map = { active: 'ok', approved: 'ok', completed: 'ok', accepted: 'ok', available: 'ok', pending: 'warn', proposed: 'warn', open: 'warn', due_soon: 'warn', lost: 'bad', overdue: 'bad', cancelled: 'bad', rejected: 'bad', hidden: 'bad', suspended: 'bad', found: 'teal', paid: 'teal', simulated: 'ochre' };
  var c = el('span', 'chip ' + (map[status] || ''), STATUS_LABELS[status] || status || '');
  return c;
}
var KIND_LABELS = { clinic: 'Veterinary clinic', grooming: 'Grooming salon', training: 'Training academy', boarding: 'Boarding house', shop: 'Supplies shop', transport: 'Pet transport', shelter: 'Shelter', other: 'Provider' };
var MODE_LABELS = { onsite: 'At their place', home: 'At your home', online: 'Online', delivery: 'Delivery' };
function emptyBox(title, text) {
  var d = el('div', 'empty');
  d.appendChild(el('h3', '', title));
  d.appendChild(el('p', '', text));
  return d;
}

async function api(path, options) {
  options = options || {};
  options.headers = Object.assign({ 'Authorization': 'Bearer ' + token }, options.headers || {});
  var res;
  try { res = await fetch(path, options); }
  catch (e) { throw new Error('Could not reach the server. Make sure the service is running, then reload the page.'); }
  var data = {};
  try { data = await res.json(); } catch (e) {}
  if (res.status === 401) { localStorage.clear(); window.location.href = './login.html'; throw new Error('Session ended.'); }
  if (!res.ok) throw new Error(data.error || data.message || 'The server returned an error.');
  return data;
}
function postJson(path, body) {
  return api(path, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body || {}) });
}

$('logout-btn').addEventListener('click', function () {
  localStorage.removeItem('petbridge_token'); localStorage.removeItem('petbridge_user'); localStorage.removeItem('petbridge_provider');
  window.location.href = './login.html';
});

function petOptions() {
  var sels = [$('health-pet'), $('booking-pet')];
  sels.forEach(function (sel) {
    if (!sel) return;
    sel.innerHTML = '';
    if (!state.pets.length) { sel.appendChild(el('option', '', 'No pets yet')); sel.disabled = true; return; }
    sel.disabled = false;
    state.pets.forEach(function (p) { var o = el('option', '', p.name); o.value = p.id; sel.appendChild(o); });
  });
}

function renderHome(home) {
  state.pets = home.pets || [];
  var list = $('pets-list'); list.innerHTML = '';
  if (!state.pets.length) {
    list.appendChild(emptyBox('No pets registered yet', 'Add your first pet from the form below this section, and its health records, vaccination dates and bookings will live here on its own page.'));
  }
  state.pets.forEach(function (pet) {
    var row = el('div', 'pet-page');
    var face = el('div', 'pet-face');
    face.innerHTML = '<svg viewBox="0 0 24 24" fill="currentColor"><ellipse cx="12" cy="15.5" rx="4.4" ry="3.6"/><ellipse cx="5.8" cy="10.5" rx="1.9" ry="2.5" transform="rotate(-18 5.8 10.5)"/><ellipse cx="9.2" cy="8" rx="1.9" ry="2.6"/><ellipse cx="14.8" cy="8" rx="1.9" ry="2.6"/><ellipse cx="18.2" cy="10.5" rx="1.9" ry="2.5" transform="rotate(18 18.2 10.5)"/></svg>';
    row.appendChild(face);
    var nameCell = el('div');
    nameCell.appendChild(el('strong', '', pet.name));
    nameCell.appendChild(el('div', 'small', [pet.species, pet.breed].filter(Boolean).join(', ')));
    row.appendChild(nameCell);
    row.appendChild(el('div', 'small', pet.age_label ? 'Age: ' + pet.age_label : (pet.birth_date ? 'Born: ' + pet.birth_date : 'Age not recorded')));
    var health = el('div', 'stitch');
    var recs = pet.health_records || [];
    if (!recs.length) health.appendChild(el('span', 'small', 'No health records yet. Add the first vaccination from the form.'));
    recs.slice(0, 3).forEach(function (r) {
      var line = el('div', 'health-line' + (r.status === 'overdue' ? ' overdue' : r.status === 'due_soon' ? ' due-soon' : ''), (r.name || r.kind) + (r.next_due ? ', next: ' + r.next_due : ''));
      health.appendChild(line);
    });
    row.appendChild(health);
    var count = el('div'); count.appendChild(el('span', 'chip teal', recs.length + ' health records')); row.appendChild(count);
    list.appendChild(row);
  });

  var due = $('due-list'); due.innerHTML = '';
  var dueItems = home.due || [];
  if (!dueItems.length) due.appendChild(el('p', 'small', 'No vaccination or appointment is due soon. Everything is in order so far.'));
  dueItems.forEach(function (d) {
    due.appendChild(el('div', 'due-line', (d.pet_name ? d.pet_name + ': ' : '') + (d.name || '') + (d.next_due ? ', due ' + d.next_due : '')));
  });
  var notif = $('notif-list'); notif.innerHTML = '';
  (home.notifications || []).slice(0, 4).forEach(function (n) {
    notif.appendChild(el('span', 'notif-dot', n.title || n.message || n.body || ''));
  });
  petOptions();
}

function renderBookings(bookings) {
  var wrap = $('bookings-list'); wrap.innerHTML = '';
  if (!bookings.length) { wrap.appendChild(emptyBox('No bookings yet', 'When you book your first service from the directory it will appear here with its status, time and amount, and you can cancel it or answer any alternative time the provider proposes.')); return; }
  bookings.forEach(function (b) {
    var line = el('div', 'booking-line' + (b.status === 'proposed' ? ' warn' : ''));
    var main = el('div');
    main.appendChild(el('strong', '', b.service_name || 'Service'));
    main.appendChild(el('div', 'small', [b.business_name, b.pet_name ? 'for pet: ' + b.pet_name : '', fmtDate(b.start_at)].filter(Boolean).join(', ')));
    if (b.proposed_start_at) main.appendChild(el('div', 'small', 'Proposed alternative: ' + fmtDate(b.proposed_start_at)));
    if (b.payment_label) main.appendChild(el('div', 'small', b.payment_label));
    line.appendChild(main);
    var side = el('div');
    side.appendChild(statusChip(b.status)); side.appendChild(document.createTextNode(' '));
    if (b.total != null) side.appendChild(el('span', 'price', money(b.total)));
    if (b.commission != null || b.provider_net != null) side.appendChild(el('div', 'small', 'Platform commission: ' + money(b.commission) + ' · Provider net: ' + money(b.provider_net)));
    var acts = el('div'); acts.style.marginTop = '.4rem';
    if (b.status === 'proposed') {
      var acc = el('button', 'btn small', 'Accept the new time'); acc.type = 'button';
      acc.addEventListener('click', function () { respondProposal(b.id, true); });
      var rej = el('button', 'btn ghost small', 'Reject proposal'); rej.type = 'button';
      rej.addEventListener('click', function () { respondProposal(b.id, false); });
      acts.appendChild(acc); acts.appendChild(document.createTextNode(' ')); acts.appendChild(rej);
    }
    if (['pending', 'accepted', 'proposed'].indexOf(b.status) !== -1) {
      var can = el('button', 'btn danger small', 'Cancel booking'); can.type = 'button';
      can.addEventListener('click', function () { cancelBooking(b.id); });
      acts.appendChild(document.createTextNode(' ')); acts.appendChild(can);
    }
    side.appendChild(acts);
    line.appendChild(side);
    wrap.appendChild(line);
  });
}

async function loadBookings() {
  try { var d = await api('/api/client/bookings'); renderBookings(d.bookings || []); }
  catch (e) { $('bookings-list').appendChild(emptyBox('Bookings could not be loaded', e.message)); }
}
async function cancelBooking(id) {
  try { await postJson('/api/bookings/' + id + '/cancel'); show('booking-msg', 'The booking was cancelled.', 'success'); loadBookings(); }
  catch (e) { show('booking-msg', e.message, 'error'); }
}
async function respondProposal(id, accept) {
  try { await postJson('/api/bookings/' + id + '/respond-proposal', { accept: accept }); show('booking-msg', accept ? 'The alternative time was accepted.' : 'The proposal was rejected.', 'success'); loadBookings(); }
  catch (e) { show('booking-msg', e.message, 'error'); }
}

function renderDirectory(providers) {
  var wrap = $('dir-list'); wrap.innerHTML = '';
  if (!providers.length) { wrap.appendChild(emptyBox('No matching results', 'Try another city, a different category, or a broader search word. Only approved providers appear in the directory.')); return; }
  providers.forEach(function (prov) {
    var row = el('div', 'dir-row');
    var side = el('div');
    side.appendChild(el('span', 'chip teal', KIND_LABELS[prov.kind] || prov.kind || 'Provider'));
    side.appendChild(el('h3', '', prov.business_name));
    side.appendChild(el('div', 'small', [prov.city, prov.area].filter(Boolean).join(', ')));
    if (prov.rating != null) side.appendChild(el('div', 'stars', 'Rating: ' + prov.rating + ' of 5 (' + (prov.reviews_count || 0) + ' reviews)'));
    side.appendChild(el('p', 'small', prov.description || ''));
    row.appendChild(side);
    var services = el('div');
    var svcs = prov.services || [];
    if (!svcs.length) services.appendChild(el('p', 'small', 'This provider has not published bookable services yet.'));
    svcs.forEach(function (s) {
      var box = el('div', 'svc');
      var head = el('div');
      head.appendChild(el('strong', '', s.name)); head.appendChild(document.createTextNode('  '));
      head.appendChild(el('span', 'price', money(s.price)));
      if (s.duration_min) head.appendChild(el('span', 'small', ' · ' + s.duration_min + ' min'));
      if (s.mode) head.appendChild(el('span', 'small', ' · ' + (MODE_LABELS[s.mode] || s.mode)));
      box.appendChild(head);
      var slots = s.slots || [];
      if (!slots.length) box.appendChild(el('div', 'small', 'No open slots for this service right now.'));
      slots.forEach(function (slot) {
        var left = (slot.capacity || 0) - (slot.booked || 0);
        var btn = el('button', 'slot-btn' + (left <= 0 ? ' full' : ''), (slot.date || '') + ' ' + (slot.start_time || '') + (left > 0 ? ' · ' + left + ' left' : ' · Full'));
        btn.type = 'button'; btn.disabled = left <= 0;
        btn.addEventListener('click', function () { bookSlot(s, slot, prov); });
        box.appendChild(btn);
      });
      services.appendChild(box);
    });
    row.appendChild(services);
    wrap.appendChild(row);
  });
}

async function bookSlot(service, slot, prov) {
  var petId = $('booking-pet').value;
  if (!state.pets.length || !petId) { show('dir-msg', 'Add a pet first from the My pets section, choose it in the booking list, then try again.', 'error'); window.scrollTo({ top: $('pets').offsetTop - 80, behavior: 'smooth' }); return; }
  try {
    await postJson('/api/bookings', { service_id: service.id, pet_id: petId, slot_id: slot.id, notes: '' });
    show('dir-msg', 'Your booking was sent to ' + (service.name || 'the service') + ' and is now waiting for the provider to accept. Follow its status under My bookings.', 'success');
    var petName = '';
    state.pets.forEach(function (p) { if (String(p.id) === String(petId)) petName = p.name; });
    $('booked-text').textContent = (service.name || 'Service') + (prov && prov.business_name ? ' at ' + prov.business_name : '') + (petName ? ' for ' + petName : '') + ' — ' + (slot.date || '') + ' ' + (slot.start_time || '') + '. It is waiting for the provider to accept.';
    $('booked-back').classList.add('show');
    loadBookings(); loadDirectory();
  } catch (e) { show('dir-msg', e.message, 'error'); }
}
$('booked-close').addEventListener('click', function () {
  $('booked-back').classList.remove('show');
  window.scrollTo({ top: $('bookings').offsetTop - 80, behavior: 'smooth' });
});

async function loadDirectory() {
  var q = new URLSearchParams();
  if ($('f-city').value.trim()) q.set('city', $('f-city').value.trim());
  if ($('f-category').value) q.set('category', $('f-category').value);
  if ($('f-q').value.trim()) q.set('q', $('f-q').value.trim());
  try { var d = await api('/api/directory?' + q.toString()); renderDirectory(d.providers || []); }
  catch (e) { show('dir-msg', e.message, 'error'); }
}

function renderSimpleList(wrapId, items, build) {
  var wrap = $(wrapId); wrap.innerHTML = '';
  if (!items.length) return false;
  items.forEach(function (it) { wrap.appendChild(build(it)); });
  return true;
}

async function loadLost() {
  try {
    var d = await api('/api/lost-found'); var items = d.items || [];
    if (!renderSimpleList('lost-list', items, function (it) {
      var c = el('div', 'post');
      c.appendChild(statusChip(it.kind === 'found' ? 'found' : 'lost'));
      c.appendChild(el('h3', '', it.title || 'Report'));
      c.appendChild(el('p', 'small', [it.pet_name, it.species, it.city, it.area].filter(Boolean).join(', ')));
      c.appendChild(el('p', '', it.description || ''));
      if (it.contact_phone) c.appendChild(el('div', 'small', 'Contact: ' + it.contact_phone));
      return c;
    })) $('lost-list').appendChild(emptyBox('No reports right now', 'If you lost your pet or found a stray, post the first report from the form next to this list and it will appear here at once for people in your area.'));
  } catch (e) { show('page-error', e.message, 'error'); }
}
async function loadAdoptions() {
  try {
    var d = await api('/api/adoptions'); var items = d.items || [];
    if (!renderSimpleList('adopt-list', items, function (it) {
      var c = el('div', 'post');
      c.appendChild(el('h3', '', it.title || 'Pet for adoption'));
      c.appendChild(el('p', 'small', [it.animal_name, it.species, it.breed, it.age_label, it.city].filter(Boolean).join(', ')));
      c.appendChild(el('p', '', it.description || ''));
      if (it.contact_phone) c.appendChild(el('div', 'small', 'Contact: ' + it.contact_phone));
      return c;
    })) $('adopt-list').appendChild(emptyBox('No adoption listings right now', 'When the first adoption listing is posted it will appear here with contact details, a description of the pet and the adoption conditions.'));
  } catch (e) { show('page-error', e.message, 'error'); }
}
async function loadPosts() {
  try {
    var d = await api('/api/posts'); var posts = d.posts || [];
    var wrap = $('posts-list'); wrap.innerHTML = '';
    if (!posts.length) { wrap.appendChild(emptyBox('The community is quiet', 'Be the first to post a question or an experience about your pet, and members\' posts will appear here with their comments.')); return; }
    posts.forEach(function (p) {
      var c = el('div', 'post');
      c.appendChild(el('h3', '', p.title || 'Post'));
      c.appendChild(el('div', 'small', (p.author_name || '') + (p.created_at ? ', ' + fmtDate(p.created_at) : '')));
      c.appendChild(el('p', '', p.body || ''));
      (p.comments || []).forEach(function (cm) {
        var cc = el('div', 'comment');
        cc.appendChild(el('strong', '', cm.author_name || 'Member')); cc.appendChild(document.createTextNode(': ' + (cm.body || '')));
        c.appendChild(cc);
      });
      var form = el('form'); form.style.marginTop = '.6rem';
      var input = el('input'); input.placeholder = 'Write a comment…'; input.required = true;
      var btn = el('button', 'btn ghost small', 'Comment'); btn.type = 'submit';
      form.appendChild(input); form.appendChild(btn);
      form.addEventListener('submit', async function (ev) {
        ev.preventDefault();
        try { await postJson('/api/posts/' + p.id + '/comments', { body: input.value }); loadPosts(); }
        catch (e) { show('post-msg', e.message, 'error'); }
      });
      c.appendChild(form);
      var rep = el('button', 'btn ghost small', 'Report this post to the admins'); rep.type = 'button'; rep.style.marginTop = '.5rem';
      rep.addEventListener('click', async function () {
        var reason = window.prompt('Brief reason for the report:');
        if (!reason) return;
        try { await postJson('/api/posts/' + p.id + '/report', { reason: reason }); show('post-msg', 'Your report reached the admins and the post will be reviewed.', 'success'); }
        catch (e) { show('post-msg', e.message, 'error'); }
      });
      c.appendChild(rep);
      wrap.appendChild(c);
    });
  } catch (e) { show('page-error', e.message, 'error'); }
}
async function loadArticles() {
  try {
    var d = await api('/api/articles'); var items = d.articles || [];
    var wrap = $('articles-list'); wrap.innerHTML = '';
    if (!items.length) { wrap.appendChild(emptyBox('No articles published yet', 'The platform team will publish nutrition, training and health articles here over time.')); return; }
    items.forEach(function (a) {
      var c = el('div', 'article');
      if (a.category) c.appendChild(el('span', 'chip ochre', a.category));
      c.appendChild(el('h3', '', a.title || 'Article'));
      c.appendChild(el('p', '', a.excerpt || a.body || ''));
      if (a.body && a.excerpt) { var det = el('details'); det.appendChild(el('summary', '', 'Read the full article')); det.appendChild(el('p', '', a.body)); c.appendChild(det); }
      if (a.author) c.appendChild(el('div', 'small', 'By: ' + a.author));
      wrap.appendChild(c);
    });
  } catch (e) { show('page-error', e.message, 'error'); }
}
async function loadProducts() {
  try {
    var d = await api('/api/products'); var items = d.products || [];
    var wrap = $('products-list'); wrap.innerHTML = '';
    if (!items.length) { wrap.appendChild(emptyBox('The shop is empty right now', 'When providers and shops publish their products they will appear here with prices and stock, ready to order from the same place.')); return; }
    items.forEach(function (p) {
      var row = el('div', 'shop-row');
      var info = el('div');
      info.appendChild(el('strong', '', p.name)); info.appendChild(el('div', 'small', [p.provider_name, p.city, p.stock != null ? 'Stock: ' + p.stock : ''].filter(Boolean).join(', ')));
      info.appendChild(el('div', 'small', p.description || ''));
      row.appendChild(info);
      var side = el('div'); side.style.display = 'flex'; side.style.gap = '.5rem'; side.style.alignItems = 'center';
      side.appendChild(el('span', 'price', money(p.price)));
      var qty = el('input'); qty.type = 'number'; qty.min = '1'; qty.value = '1'; qty.style.width = '70px';
      var btn = el('button', 'btn small', 'Demo order, simulated payment'); btn.type = 'button';
      btn.addEventListener('click', async function () {
        try {
          var r = await postJson('/api/orders', { product_id: p.id, qty: Number(qty.value) || 1 });
          show('shop-msg', (r.label || r.message || 'The demo order was created.') + ' This is a simulated order inside the demo — there is no real payment or delivery.', 'success');
        } catch (e) { show('shop-msg', e.message, 'error'); }
      });
      side.appendChild(qty); side.appendChild(btn);
      row.appendChild(side);
      wrap.appendChild(row);
    });
  } catch (e) { show('shop-msg', e.message, 'error'); }
}

// Form wiring
$('dir-filters').addEventListener('submit', function (ev) { ev.preventDefault(); hide('dir-msg'); loadDirectory(); });
$('pet-form').addEventListener('submit', async function (ev) {
  ev.preventDefault();
  try {
    await postJson('/api/pets', { name: $('pet-name').value.trim(), species: $('pet-species').value.trim(), breed: $('pet-breed').value.trim(), birth_date: $('pet-birth').value || null });
    show('pet-msg', 'The pet was saved and appears in your notebook above.', 'success'); ev.target.reset(); initHome();
  } catch (e) { show('pet-msg', e.message, 'error'); }
});
$('health-form').addEventListener('submit', async function (ev) {
  ev.preventDefault();
  var petId = $('health-pet').value;
  if (!petId) { show('health-msg', 'Add a pet before recording a health record.', 'error'); return; }
  try {
    await postJson('/api/pets/' + petId + '/health', { kind: $('health-kind').value, name: $('health-name').value.trim(), given_date: $('health-given').value || null, next_due: $('health-due').value || null });
    show('health-msg', 'The health record was saved and appears in the pet\'s follow-up.', 'success'); ev.target.reset(); initHome();
  } catch (e) { show('health-msg', e.message, 'error'); }
});
$('lost-form').addEventListener('submit', async function (ev) {
  ev.preventDefault();
  try {
    await postJson('/api/lost-found', { kind: $('lost-kind').value, title: $('lost-title').value.trim(), description: $('lost-desc').value.trim(), city: $('lost-city').value.trim(), area: $('lost-area').value.trim(), pet_name: $('lost-pet').value.trim(), species: $('lost-species').value.trim(), contact_phone: $('lost-phone').value.trim() });
    show('lost-msg', 'The report was posted.', 'success'); ev.target.reset(); loadLost();
  } catch (e) { show('lost-msg', e.message, 'error'); }
});
$('adopt-form').addEventListener('submit', async function (ev) {
  ev.preventDefault();
  try {
    await postJson('/api/adoptions', { title: $('ad-title').value.trim(), animal_name: $('ad-name').value.trim(), species: $('ad-species').value.trim(), breed: $('ad-breed').value.trim(), age_label: $('ad-age').value.trim(), city: $('ad-city').value.trim(), description: $('ad-desc').value.trim(), contact_phone: $('ad-phone').value.trim() });
    show('adopt-msg', 'The adoption listing was posted.', 'success'); ev.target.reset(); loadAdoptions();
  } catch (e) { show('adopt-msg', e.message, 'error'); }
});
$('post-form').addEventListener('submit', async function (ev) {
  ev.preventDefault();
  try { await postJson('/api/posts', { title: $('post-title').value.trim(), body: $('post-body').value.trim() }); show('post-msg', 'Your post is live in the community.', 'success'); ev.target.reset(); loadPosts(); }
  catch (e) { show('post-msg', e.message, 'error'); }
});
$('breed-form').addEventListener('submit', async function (ev) {
  ev.preventDefault();
  var file = $('breed-file').files[0];
  if (!file) { show('breed-msg', 'Choose an image file first. In this version only the file name is sent to the demo analysis.', 'error'); return; }
  try {
    var r = await postJson('/api/breed/analyze', { file_name: file.name, declared_species: $('breed-species').value.trim() });
    hide('breed-msg');
    var box = $('breed-result'); box.innerHTML = '';
    box.appendChild(el('span', 'chip ochre', 'Beta demo analysis'));
    box.appendChild(el('h3', '', r.label || 'Analysis result'));
    box.appendChild(el('p', '', [r.species ? 'Likely species: ' + r.species : '', r.breed ? 'Likely breed: ' + r.breed : ''].filter(Boolean).join(', ')));
    if (r.summary) box.appendChild(el('p', '', r.summary));
    if (r.care && r.care.length) { var ul = el('ul'); r.care.forEach(function (c) { ul.appendChild(el('li', '', c)); }); box.appendChild(ul); }
    box.appendChild(el('p', 'small', r.note || 'A demo result, not a final confirmation. See a vet for an exact diagnosis.'));
  } catch (e) { show('breed-msg', e.message, 'error'); }
});

// Tour
var tourSteps = [
  { t: 'Your pets first', x: 'Add your pets and their health records, and the home page will warn you about any vaccination coming due.' },
  { t: 'Book from the directory', x: 'Search by city and category, choose your pet in the booking list, then tap any open slot and your request goes to the provider.' },
  { t: 'Follow up under My bookings', x: 'There you see acceptance, rejection and proposed alternative times, and you can accept, reject or cancel.' },
  { t: 'Community and lost & found', x: 'Post a lost report, an adoption listing or a community question, and browse articles and the shop from the same portal.' }
];
var tourIdx = 0;
function renderTour() {
  var s = tourSteps[tourIdx];
  $('tour-step-label').textContent = 'Step ' + (tourIdx + 1) + ' of ' + tourSteps.length;
  $('tour-title').textContent = s.t; $('tour-text').textContent = s.x;
  $('tour-next').textContent = tourIdx === tourSteps.length - 1 ? 'Finish' : 'Next';
}
function closeTour() { $('tour-back').classList.remove('show'); localStorage.setItem('petbridge_tour_done', '1'); }
$('tour-btn').addEventListener('click', function () { tourIdx = 0; renderTour(); $('tour-back').classList.add('show'); });
$('tour-close').addEventListener('click', closeTour);
$('tour-next').addEventListener('click', function () { if (tourIdx >= tourSteps.length - 1) closeTour(); else { tourIdx++; renderTour(); } });

async function initHome() {
  try { var home = await api('/api/client/home'); renderHome(home); }
  catch (e) { show('page-error', e.message, 'error'); $('pets-list').appendChild(emptyBox('Your data could not be loaded', 'The server is unavailable right now, or the session ended. Try again in a moment.')); }
}
async function initTaxonomy() {
  try {
    var d = await api('/api/taxonomy'); state.taxonomy = d.categories || [];
    var sel = $('f-category');
    state.taxonomy.forEach(function (c) { var o = el('option', '', c.label || c.key); o.value = c.key; sel.appendChild(o); });
  } catch (e) {}
}

(function init() {
  if (!user) return;
  $('user-name').textContent = user.name || user.email || '';
  if (user.role === 'provider') $('provider-link').hidden = false;
  if (user.role === 'admin') $('admin-link').hidden = false;
  initHome(); initTaxonomy().then(loadDirectory);
  loadBookings(); loadLost(); loadAdoptions(); loadPosts(); loadArticles(); loadProducts();
  if (!localStorage.getItem('petbridge_tour_done')) { renderTour(); $('tour-back').classList.add('show'); }
  if ('serviceWorker' in navigator) navigator.serviceWorker.register('./sw.js').catch(function () {});
})();

