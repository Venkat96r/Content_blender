// ─── SHARED STATE ────────────────────────────────────────────────────────────

var API = 'http://localhost:8000/api';
var bankItems = [];
var blends = [];

// ─── API HELPER ───────────────────────────────────────────────────────────────

function apic(method, path, body) {
  var opts = { method: method, headers: {} };
  if (body) {
    if (body instanceof FormData) {
      opts.body = body;
    } else {
      opts.body = JSON.stringify(body);
      opts.headers['Content-Type'] = 'application/json';
    }
  }
  return fetch(API + path, opts).then(function(r) {
    return r.json().then(function(d) {
      if (!r.ok) {
        throw new Error((d && d.detail) ? d.detail : 'Request failed');
      }
      return d;
    });
  });
}

// ─── TOAST ────────────────────────────────────────────────────────────────────

function toast(msg, type) {
  var el = document.createElement('div');
  el.className = 'toast' + (type ? ' ' + type : '');
  el.textContent = msg;
  document.getElementById('tc').appendChild(el);
  setTimeout(function() { if (el.parentNode) el.parentNode.removeChild(el); }, 3200);
}

// ─── MEDIA HELPERS ────────────────────────────────────────────────────────────

function mediaIcon(mt) {
  if (!mt) return '?';
  if (mt.indexOf('text') === 0) return '&#9997;';
  if (mt.indexOf('image') === 0) return '&#128444;';
  if (mt.indexOf('video') === 0) return '&#9654;';
  return '&#128196;';
}

function typeBadge(mt) {
  if (!mt) return '';
  if (mt.indexOf('text') === 0) return 'txt';
  if (mt.indexOf('image') === 0) return 'img';
  if (mt.indexOf('video') === 0) return 'vid';
  return '';
}

// ─── NAV / PAGE ───────────────────────────────────────────────────────────────

function showPage(name) {
  var pages = document.querySelectorAll('.page');
  for (var i = 0; i < pages.length; i++) pages[i].classList.remove('active');
  var navBtns = document.querySelectorAll('.nbtn');
  for (var j = 0; j < navBtns.length; j++) navBtns[j].classList.remove('active');
  document.getElementById('page-' + name).classList.add('active');
  document.getElementById('nav-' + name).classList.add('active');
  if (name === 'blend') {
    loadBank();
    loadBlends();
  } else if (name === 'bank') {
    loadBank();
  }
}

// ─── HEALTH CHECK ─────────────────────────────────────────────────────────────

function checkApi() {
  fetch(API + '/health').then(function(r) {
    document.getElementById('api-dot').style.background = r.ok ? '#2dd4bf' : '#f43f5e';
  }).catch(function() {
    document.getElementById('api-dot').style.background = '#f43f5e';
  });
}

// ─── GLOBAL DRAG/DROP ─────────────────────────────────────────────────────────

var gdoTimer = null;
window.addEventListener('dragover', function(e) {
  e.preventDefault();
  document.getElementById('gdo').classList.add('show');
  clearTimeout(gdoTimer);
});
window.addEventListener('dragleave', function(e) {
  if (e.clientX === 0 && e.clientY === 0) {
    document.getElementById('gdo').classList.remove('show');
  }
});
window.addEventListener('drop', function(e) {
  e.preventDefault();
  document.getElementById('gdo').classList.remove('show');
  var files = e.dataTransfer.files;
  if (files && files.length > 0) {
    openAddModal();
    switchTab('upload');
    setFile(files[0]);
  }
});

// ─── INIT ─────────────────────────────────────────────────────────────────────

checkApi();
loadBank();