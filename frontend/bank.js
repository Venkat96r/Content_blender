// ─── BANK STATE ───────────────────────────────────────────────────────────────

var bankFilter = 'all';
var pickedFile = null;
var curTab = 'text';

// ─── LOAD / RENDER ────────────────────────────────────────────────────────────

function loadBank() {
  apic('GET', '/bank').then(function(d) {
    bankItems = d.items;
    document.getElementById('badge-bank').textContent = bankItems.length;
    document.getElementById('bank-sub').textContent =
      bankItems.length + ' item' + (bankItems.length !== 1 ? 's' : '') + ' in bank';
    renderBank();
  }).catch(function(e) { toast('Failed to load bank: ' + e.message, 'error'); });
}

function setFilter(btn, f) {
  bankFilter = f;
  var chips = document.querySelectorAll('.chip');
  for (var i = 0; i < chips.length; i++) chips[i].classList.remove('active');
  btn.classList.add('active');
  renderBank();
}

function renderBank() {
  var q = (document.getElementById('search-input').value || '').toLowerCase();
  var filtered = bankItems.filter(function(it) {
    if (bankFilter !== 'all') {
      if (bankFilter === 'text'  && it.mediaType.indexOf('text')  !== 0) return false;
      if (bankFilter === 'image' && it.mediaType.indexOf('image') !== 0) return false;
      if (bankFilter === 'video' && it.mediaType.indexOf('video') !== 0) return false;
    }
    if (q) {
      return (it.title && it.title.toLowerCase().indexOf(q) !== -1) ||
             (it.id    && it.id.toLowerCase().indexOf(q) !== -1);
    }
    return true;
  });

  var grid = document.getElementById('bank-grid');
  if (filtered.length === 0) {
    grid.innerHTML =
      '<div class="empty-state"><div class="es-icon">' +
      (bankItems.length === 0 ? '&#128196;' : '&#128269;') +
      '</div><p>' +
      (bankItems.length === 0
        ? 'No items yet. Click &quot;+ Add Content&quot; to get started.'
        : 'No items match your search.') +
      '</p></div>';
    return;
  }

  var html = '';
  for (var i = 0; i < filtered.length; i++) {
    var it    = filtered[i];
    var badge = typeBadge(it.mediaType);
    var thumb = '';

    if (it.mediaType && it.mediaType.indexOf('image') === 0) {
      var src = (it.asset && it.asset.src) ? it.asset.src : '';
      thumb = '<img src="' + src + '" alt="' +
        (it.asset && it.asset.alt ? it.asset.alt : '') +
        '" onerror="this.style.display=\'none\'">';

    } else if (it.mediaType && it.mediaType.indexOf('video') === 0) {
      var tsrc = (it.fallback && it.fallback.thumbnail) ? it.fallback.thumbnail : '';
      thumb = '<div class="tthumb"><img src="' + tsrc +
        '" alt="" onerror="this.style.opacity=0"></div>' +
        '<div class="tplay"><div class="tplay-icon">&#9654;</div></div>';

    } else {
      var prev = (it.body || '').substring(0, 110);
      thumb = '<div class="tprev">' + prev + '</div>';
    }

    var created = (it.meta && it.meta.created) ? it.meta.created : '';
    html += '<div class="mc">';
    html += '<div class="mc-thumb"><span class="tbadge ' + badge + '">' +
      badge.toUpperCase() + '</span>' + thumb + '</div>';
    html += '<div class="mc-body">';
    html += '<div class="mc-title">' + (it.title || '') + '</div>';
    html += '<div class="mc-meta"><span class="id-chip">' + it.id +
      '</span><span class="mc-date">' + created + '</span></div>';
    html += '<div class="mc-actions">' +
      '<button class="btn-teal" onclick="addToBlend(\'' + it.id + '\')">+ Blend</button>' +
      '<button class="btn-danger" onclick="deleteItem(\'' + it.id + '\')">Delete</button>' +
      '</div>';
    html += '</div></div>';
  }
  grid.innerHTML = html;
}

// ─── BANK ACTIONS ─────────────────────────────────────────────────────────────

function deleteItem(id) {
  if (!confirm('Delete ' + id + '? This cannot be undone.')) return;
  apic('DELETE', '/bank/' + id).then(function() {
    toast(id + ' deleted.', 'success');
    loadBank();
  }).catch(function(e) { toast(e.message, 'error'); });
}

function addToBlend(id) {
  showPage('blend');
  var initPl = [{ refId: id, order: 1, layout: 'body', style: {} }];
  openEditor(null, initPl);
}

// ─── ADD MODAL ────────────────────────────────────────────────────────────────

function openAddModal() {
  resetAdd();
  document.getElementById('add-modal').classList.add('open');
}

function closeAddModal() {
  document.getElementById('add-modal').classList.remove('open');
}

function switchTab(t) {
  curTab = t;
  var tabs = ['text', 'img-url', 'vid-url', 'upload'];
  for (var i = 0; i < tabs.length; i++) {
    var id  = tabs[i];
    document.getElementById('tab-' + id).classList.toggle('active', id === t);
    document.getElementById('tab-' + id + '-btn').classList.toggle('active', id === t);
  }
}

function prevImg() {
  var url  = document.getElementById('iu-url').value;
  var prev = document.getElementById('iprev');
  var img  = document.getElementById('iprev-img');
  if (url) { img.src = url; prev.style.display = 'block'; }
  else       prev.style.display = 'none';
}

function checkYt() {
  var url  = document.getElementById('vu-url').value;
  var hint = document.getElementById('ythint');
  hint.style.display =
    (url && (url.indexOf('youtube.com') !== -1 || url.indexOf('youtu.be') !== -1))
      ? 'block' : 'none';
}

function setFile(f) {
  if (!f) return;
  pickedFile = f;
  document.getElementById('dz-icon').textContent =
    f.type.indexOf('image') === 0 ? '&#128444;' : '&#127916;';
  document.getElementById('dz-text').textContent = f.name;
  document.getElementById('dz-sub').textContent  = (f.size / 1024).toFixed(0) + ' KB';
  var titleEl = document.getElementById('up-title');
  if (!titleEl.value) titleEl.value = f.name.replace(/\.[^/.]+$/, '');
}

function dzOv(e) { e.preventDefault(); document.getElementById('dz').classList.add('over'); }
function dzLv()  { document.getElementById('dz').classList.remove('over'); }
function dzDp(e) {
  e.preventDefault(); dzLv();
  var files = e.dataTransfer.files;
  if (files && files.length > 0) setFile(files[0]);
}

function resetAdd() {
  document.getElementById('txt-title').value  = '';
  document.getElementById('txt-body').value   = '';
  document.getElementById('txt-author').value = '';
  document.getElementById('iu-title').value   = '';
  document.getElementById('iu-url').value     = '';
  document.getElementById('iu-alt').value     = '';
  document.getElementById('iu-cap').value     = '';
  document.getElementById('iprev').style.display = 'none';
  document.getElementById('vu-title').value   = '';
  document.getElementById('vu-url').value     = '';
  document.getElementById('vu-cap').value     = '';
  document.getElementById('ythint').style.display = 'none';
  document.getElementById('up-title').value   = '';
  document.getElementById('up-cap').value     = '';
  document.getElementById('dz-icon').innerHTML  = '&#128196;';
  document.getElementById('dz-text').textContent = 'Click or drag & drop a file';
  document.getElementById('dz-sub').textContent  = 'Images and videos accepted';
  document.getElementById('dz').classList.remove('over');
  pickedFile = null;
  switchTab('text');
}

function submitAdd() {
  var btn = document.getElementById('add-btn');
  btn.disabled = true;
  btn.textContent = 'Adding...';

  var fd = new FormData();
  var p;

  if (curTab === 'text') {
    var t = document.getElementById('txt-title').value.trim();
    var b = document.getElementById('txt-body').value.trim();
    if (!t || !b) {
      toast('Title and body are required.', 'error');
      btn.disabled = false; btn.textContent = 'Add to Bank'; return;
    }
    fd.append('title', t);
    fd.append('body', b);
    fd.append('author', document.getElementById('txt-author').value.trim() || 'Anonymous');
    p = '/bank/text';

  } else if (curTab === 'img-url') {
    var t2 = document.getElementById('iu-title').value.trim();
    var s2 = document.getElementById('iu-url').value.trim();
    if (!t2 || !s2) {
      toast('Title and URL are required.', 'error');
      btn.disabled = false; btn.textContent = 'Add to Bank'; return;
    }
    fd.append('title', t2);
    fd.append('src', s2);
    fd.append('alt', document.getElementById('iu-alt').value.trim() || t2);
    fd.append('caption', document.getElementById('iu-cap').value.trim());
    p = '/bank/image-url';

  } else if (curTab === 'vid-url') {
    var t3 = document.getElementById('vu-title').value.trim();
    var s3 = document.getElementById('vu-url').value.trim();
    if (!t3 || !s3) {
      toast('Title and URL are required.', 'error');
      btn.disabled = false; btn.textContent = 'Add to Bank'; return;
    }
    fd.append('title', t3);
    fd.append('src', s3);
    fd.append('caption', document.getElementById('vu-cap').value.trim());
    p = '/bank/video-url';

  } else {
    if (!pickedFile) {
      toast('Please select a file.', 'error');
      btn.disabled = false; btn.textContent = 'Add to Bank'; return;
    }
    var t4 = document.getElementById('up-title').value.trim();
    if (!t4) {
      toast('Title is required.', 'error');
      btn.disabled = false; btn.textContent = 'Add to Bank'; return;
    }
    fd.append('file', pickedFile);
    fd.append('title', t4);
    fd.append('caption', document.getElementById('up-cap').value.trim());
    p = '/bank/upload';
  }

  apic('POST', p, fd).then(function(d) {
    toast(d.id + ' added!', 'success');
    closeAddModal();
    loadBank();
  }).catch(function(e) {
    toast(e.message, 'error');
  }).finally(function() {
    btn.disabled = false;
    btn.textContent = 'Add to Bank';
  });
}