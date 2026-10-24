// Auth page handles login and both registration forms.
'use strict';

function $(id) { return document.getElementById(id); }

function showMsg(text, ok) {
  var el = $('auth-msg');
  el.textContent = text;
  el.className = 'msg show ' + (ok ? 'success' : 'error');
}

async function api(path, options) {
  var res;
  try {
    res = await fetch(path, options);
  } catch (e) {
    throw new Error('Could not reach the server. Make sure the PetBridge service is running, then try again.');
  }
  var data = {};
  try { data = await res.json(); } catch (e) { data = {}; }
  if (!res.ok) throw new Error(data.error || data.message || 'The server returned an unexpected error.');
  return data;
}

function postJson(path, body) {
  return api(path, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });
}

function saveSession(data) {
  localStorage.setItem('petbridge_token', data.token);
  localStorage.setItem('petbridge_user', JSON.stringify(data.user));
  if (data.provider) localStorage.setItem('petbridge_provider', JSON.stringify(data.provider));
  else localStorage.removeItem('petbridge_provider');
}

function routeFor(user, provider) {
  if (user.role === 'admin') return './admin.html';
  if (user.role === 'provider') {
    if (provider && (provider.status === 'approved' || provider.status === 'active')) return './provider.html';
    return null;
  }
  return './index.html';
}

document.querySelectorAll('.tab').forEach(function (tab) {
  tab.addEventListener('click', function () {
    document.querySelectorAll('.tab').forEach(function (t) { t.classList.remove('active'); });
    tab.classList.add('active');
    document.querySelectorAll('[data-pane]').forEach(function (pane) {
      pane.hidden = pane.getAttribute('data-pane') !== tab.getAttribute('data-tab');
    });
    $('auth-msg').className = 'msg';
  });
});

$('add-doc').addEventListener('click', function () {
  var row = document.createElement('div');
  row.className = 'doc-row';
  row.innerHTML = '<input data-doc="type" placeholder="Document type"><input data-doc="label" placeholder="Document description"><input data-doc="file" placeholder="File name">';
  $('doc-rows').appendChild(row);
});

$('login-form').addEventListener('submit', async function (ev) {
  ev.preventDefault();
  $('pending-note').className = 'msg';
  try {
    var data = await postJson('/api/auth/login', { email: $('login-email').value.trim(), password: $('login-password').value });
    saveSession(data);
    var target = routeFor(data.user, data.provider);
    if (!target) {
      var note = $('pending-note');
      note.textContent = 'This provider account is still under admin review. The studio will not open before approval; try again later or contact the platform administration.';
      note.className = 'msg show info';
      showMsg('You are signed in, but your business is not approved yet.', true);
      return;
    }
    window.location.href = target;
  } catch (e) { showMsg(e.message, false); }
});

$('customer-form').addEventListener('submit', async function (ev) {
  ev.preventDefault();
  try {
    await postJson('/api/auth/register-customer', {
      name: $('c-name').value.trim(), email: $('c-email').value.trim(),
      phone: $('c-phone').value.trim(), password: $('c-password').value
    });
    var data = await postJson('/api/auth/login', { email: $('c-email').value.trim(), password: $('c-password').value });
    saveSession(data);
    window.location.href = './index.html';
  } catch (e) { showMsg(e.message, false); }
});

$('provider-form').addEventListener('submit', async function (ev) {
  ev.preventDefault();
  var docs = [];
  document.querySelectorAll('#doc-rows .doc-row').forEach(function (row) {
    var type = row.querySelector('[data-doc="type"]').value.trim();
    var label = row.querySelector('[data-doc="label"]').value.trim();
    var file = row.querySelector('[data-doc="file"]').value.trim();
    if (type || label || file) docs.push({ doc_type: type, label: label, file_name: file });
  });
  try {
    await postJson('/api/auth/register-provider', {
      name: $('p-name').value.trim(), email: $('p-email').value.trim(),
      phone: $('p-phone').value.trim(), password: $('p-password').value,
      business_name: $('p-business').value.trim(), kind: $('p-kind').value,
      city: $('p-city').value.trim(), area: $('p-area').value.trim(),
      address: $('p-address').value.trim(), description: $('p-desc').value.trim(),
      documents: docs
    });
    showMsg('Your business registration was received and is now under admin review. You can enter the studio after approval.', true);
    ev.target.reset();
  } catch (e) { showMsg(e.message, false); }
});

// A visitor who is already signed in goes straight to the right portal.
(function () {
  var token = localStorage.getItem('petbridge_token');
  var raw = localStorage.getItem('petbridge_user');
  if (!token || !raw) return;
  try {
    var user = JSON.parse(raw);
    var provider = null;
    try { provider = JSON.parse(localStorage.getItem('petbridge_provider') || 'null'); } catch (e) {}
    var target = routeFor(user, provider);
    if (target) window.location.href = target;
  } catch (e) {}
})();

if ('serviceWorker' in navigator) {
  navigator.serviceWorker.register('./sw.js').catch(function () {});
}
