// ─── BLEND STATE ──────────────────────────────────────────────────────────────

var edBlend = null;
var edPls   = [];
var edPickQ = '';
var activeSlotIndex = null;

// ─── LOAD / RENDER ────────────────────────────────────────────────────────────

function loadBlends() {
  apic('GET', '/blends').then(function(d) {
    blends = d.blends;
    document.getElementById('badge-blend').textContent = blends.length;
    renderStats();
    renderBlendGrid();
  }).catch(function(e) { toast('Failed to load blends: ' + e.message, 'error'); });
}

function renderStats() {
  var web = blends.filter(function(b) { return b.target === 'Web'; }).length;
  var pdf = blends.filter(function(b) { return b.target === 'PDF'; }).length;
  document.getElementById('blend-stats').innerHTML =
    '<div class="stat-card"><div class="sv" style="color:var(--accent-lt)">' + blends.length + '</div><div class="sl">Total Blends</div></div>' +
    '<div class="stat-card"><div class="sv" style="color:var(--teal)">'      + web           + '</div><div class="sl">Web Blends</div></div>'   +
    '<div class="stat-card"><div class="sv" style="color:var(--amber)">'     + pdf           + '</div><div class="sl">PDF Blends</div></div>'   +
    '<div class="stat-card"><div class="sv" style="color:var(--text2)">'     + bankItems.length + '</div><div class="sl">Bank Items</div></div>';
}

function renderBlendGrid() {
  var grid = document.getElementById('blend-grid');
  if (blends.length === 0) {
    grid.innerHTML = '<div class="empty-state"><div class="es-icon">&#9636;</div><p>No blends yet. Click &quot;+ New Blend&quot; to compose your first.</p></div>';
    return;
  }
  var html = '';
  for (var i = 0; i < blends.length; i++) {
    var b   = blends[i];
    var tgt = b.target === 'Web' ? 'web' : 'pdf';
    var refs = '';
    var pls  = b.placements || [];
    var shown = pls.slice(0, 6);
    for (var j = 0; j < shown.length; j++) {
      var rid = shown[j].refId;
      var cls = rid.indexOf('TXT') === 0 ? 'txt' : (rid.indexOf('IMG') === 0 ? 'img' : 'vid');
      refs += '<span class="ref-chip ' + cls + '">' + rid + '</span>';
    }
    if (pls.length > 6) refs += '<span class="ref-chip">+' + (pls.length - 6) + '</span>';

    html += '<div class="bc">';
    html += '<div class="bc-hdr"><div class="bc-title">' + (b.title || 'Untitled') +
      '</div><span class="bc-target ' + tgt + '">' + b.target + '</span></div>';
    html += '<div class="bc-id">' + b.id + '</div>';
    html += '<div class="bc-refs">' + refs + '</div>';
    html += '<div class="bc-actions">' +
      '<button class="btn-canvas" style="flex:2" onclick="openCanvas(\'' + b.id + '\')">&#9881; Open Canvas</button>' +
      '<button class="btn-ghost"  style="flex:1" onclick="openEditor(\'' + b.id + '\',null)">Edit</button>' +
      '<button class="btn-danger"               onclick="deleteBlend(\'' + b.id + '\')">Del</button>' +
      '</div></div>';
  }
  grid.innerHTML = html;
}

function deleteBlend(id) {
  if (!confirm('Delete blend ' + id + '?')) return;
  apic('DELETE', '/blends/' + id).then(function() {
    toast('Blend deleted.', 'success');
    loadBlends();
  }).catch(function(e) { toast(e.message, 'error'); });
}

// ─── TEMPLATES ────────────────────────────────────────────────────────────────

function useTemplate(type) {
  var tpl = [];
  if (type === 'grid') {
    tpl = [
      { refId: '', order: 1, layout: 'card',       style: {} },
      { refId: '', order: 2, layout: 'card',       style: {} },
      { refId: '', order: 3, layout: 'card',       style: {} }
    ];
  } else if (type === 'hero') {
    tpl = [
      { refId: '', order: 1, layout: 'hero',       style: {} },
      { refId: '', order: 2, layout: 'body',       style: {} },
      { refId: '', order: 3, layout: 'body',       style: {} }
    ];
  } else if (type === 'sidebar') {
    tpl = [
      { refId: '', order: 1, layout: 'body',       style: {} },
      { refId: '', order: 2, layout: 'sidebar',    style: {} }
    ];
  } else if (type === 'mixed') {
    tpl = [
      { refId: '', order: 1, layout: 'full-width', style: {} },
      { refId: '', order: 2, layout: 'media-embed',style: {} },
      { refId: '', order: 3, layout: 'card',       style: {} },
      { refId: '', order: 4, layout: 'card',       style: {} }
    ];
  }
  openEditor(null, tpl);
}

// ─── EDITOR ───────────────────────────────────────────────────────────────────

function openEditor(blendId, initPls) {
  if (blendId) {
    for (var i = 0; i < blends.length; i++) {
      if (blends[i].id === blendId) {
        edBlend = JSON.parse(JSON.stringify(blends[i]));
        edPls   = JSON.parse(JSON.stringify(edBlend.placements || []));
        break;
      }
    }
  } else {
    edBlend = null;
    edPls   = initPls ? JSON.parse(JSON.stringify(initPls)) : [];
  }
  edPickQ = '';
  renderEditor();
}

function getEdTarget() {
  var wb = document.getElementById('ed-web');
  return (wb && wb.classList.contains('web')) ? 'Web' : 'PDF';
}

function edSetTarget(t) {
  var wb = document.getElementById('ed-web');
  var pb = document.getElementById('ed-pdf');
  if (!wb || !pb) return;
  wb.classList.remove('web');
  pb.classList.remove('pdf');
  if (t === 'Web') wb.classList.add('web');
  else             pb.classList.add('pdf');
}

function renderEditor() {
  var isEdit  = (edBlend && edBlend.id);
  var title   = edBlend ? (edBlend.title  || '') : '';
  var target  = edBlend ? (edBlend.target || 'Web') : 'Web';
  var webCls  = target === 'Web' ? ' web' : '';
  var pdfCls  = target === 'PDF' ? ' pdf' : '';

  var html = '<div class="ebox">';
  html += '<div class="ehdr"><span>' + (isEdit ? 'Edit Blend' : 'New Blend') + '</span></div>';

  html += '<div class="frow" style="padding:16px 20px 0;">';
  html += '<input type="text" id="ed-title" placeholder="Blend title..." value="' + title + '">';
  html += '<button class="tbtn' + webCls + '" id="ed-web" onclick="edSetTarget(\'Web\')">Web</button>';
  html += '<button class="tbtn' + pdfCls + '" id="ed-pdf" onclick="edSetTarget(\'PDF\')">PDF</button>';
  html += '</div>';

  html += '<div class="ebody">';

  // Left: placement list + layout preview
  html += '<div class="eleft">';
  if (edPls.length === 0) {
    html += '<div class="empty-state"><div class="es-icon">&#43;</div><p>Add items from the bank panel on the right.</p></div>';
  } else {
    html += '<div class="layout-preview">' + buildLayoutPreview() + '</div>';

    for (var i = 0; i < edPls.length; i++) {
      var pl   = edPls[i];
      var it   = bankItems.find(function(x) { return x.id === pl.refId; });
      var icon = it ? mediaIcon(it.mediaType) : '?';
      var name = it ? (it.title || pl.refId) : '+ Add';

      html += '<div class="plitem">';
      html += '<div class="pord">' + (i + 1) + '</div>';
      html += '<div class="picon">' + icon + '</div>';
      html += '<div class="pinfo"><div class="pname">' + name +
        '</div><div class="pid">' + (pl.refId || '-') + '</div></div>';

      html += '<select onchange="edLayout(\'' + pl.refId + '\',this.value)">';
      var layouts = ['hero', 'full-width', 'body', 'sidebar', 'media-embed', 'card'];
      for (var li = 0; li < layouts.length; li++) {
        html += '<option value="' + layouts[li] + '"' +
          (pl.layout === layouts[li] ? ' selected' : '') + '>' + layouts[li] + '</option>';
      }
      html += '</select>';

      html += '<div class="pctrl">';
      html += '<button onclick="edMove(' + i + ',-1)"' + (i === 0 ? ' disabled' : '') + '>↑</button>';
      html += '<button onclick="edMove(' + i + ',1)"'  + (i === edPls.length - 1 ? ' disabled' : '') + '>↓</button>';
      html += '<button class="pdel" onclick="edRemove(\'' + pl.refId + '\')">✕</button>';
      html += '</div></div>';
    }
  }
  html += '</div>'; // close eleft

  // Right: bank item picker
  html += '<div class="eright">';
  html += '<div style="font-size:11px;font-weight:600;color:var(--text3);text-transform:uppercase;letter-spacing:.5px;margin-bottom:8px;">Bank Items</div>';
  html += '<input type="text" class="picker-search" placeholder="Search..." oninput="edPickQ=this.value;renderPickerList()">';
  html += '<div id="picker-list">' + buildPickerHtml() + '</div>';
  html += '</div>'; // close eright

  html += '</div>'; // close ebody

  html += '<div class="efooter">' +
    '<button class="btn-ghost"   onclick="closeEditor()">Cancel</button>' +
    '<button class="btn-primary" onclick="saveEditor()">Save Blend</button>' +
    '</div>';
  html += '</div>';

  document.getElementById('editor-wrap').innerHTML = html;
}

// ─── LAYOUT PREVIEW ───────────────────────────────────────────────────────────

function buildLayoutPreview() {
  if (!edPls || edPls.length === 0) return '';
  var first = edPls[0].layout;

  if (first === 'card') {
    var h = '<div class="grid-3">';
    edPls.forEach(function(pl, i) { h += renderSlot(pl, i); });
    return h + '</div>';
  }
  if (first === 'hero') {
    return '<div class="hero-layout">' +
      renderSlot(edPls[0], 0, 'hero') +
      '<div class="row">' +
        renderSlot(edPls[1], 1) +
        renderSlot(edPls[2], 2) +
      '</div></div>';
  }
  if (first === 'body' && edPls.length === 2) {
    return '<div class="sidebar-layout">' +
      renderSlot(edPls[0], 0) + renderSlot(edPls[1], 1) +
      '</div>';
  }
  return '<div class="mixed-layout"><div class="full">' +
    renderSlot(edPls[0], 0) + '</div>' +
    renderSlot(edPls[1], 1) + renderSlot(edPls[2], 2) +
    '</div>';
}

function renderSlot(pl, index, extraClass) {
  extraClass = extraClass || '';
  var hasContent = !!pl.refId;
  var item       = bankItems.find(function(x) { return x.id === pl.refId; });
  var label      = item ? (item.title || item.id) : '+';
  var isActive   = activeSlotIndex === index ? ' active' : '';

  return '<div class="slot ' + extraClass + isActive + '" onclick="openPickerForSlot(' + index + ')">' +
    (hasContent
      ? '<span class="label">' + label + '</span>'
      : '<span class="plus">+</span>') +
    '</div>';
}

function openPickerForSlot(idx) {
  activeSlotIndex = idx;
  renderEditor();
}

// ─── PICKER ───────────────────────────────────────────────────────────────────

function buildPickerHtml() {
  var q        = (edPickQ || '').toLowerCase();
  var addedIds = {};
  for (var j = 0; j < edPls.length; j++) addedIds[edPls[j].refId] = true;

  var items = bankItems.filter(function(it) {
    if (!q) return true;
    return (it.title && it.title.toLowerCase().indexOf(q) !== -1) ||
           (it.id    && it.id.toLowerCase().indexOf(q) !== -1);
  });

  if (items.length === 0) return '<div style="color:var(--text3);font-size:12px;padding:8px;">No items found.</div>';

  var html = '';
  for (var i = 0; i < items.length; i++) {
    var it    = items[i];
    var added = addedIds[it.id];
    html += '<div class="pitem-row' + (added ? ' added' : '') + '" onclick="' +
      (added ? '' : 'edAdd(\'' + it.id + '\')') + '">';
    html += '<div class="pi-icon">' + mediaIcon(it.mediaType) + '</div>';
    html += '<div class="pi-info"><div class="pi-name">' + (it.title || it.id) +
      '</div><div class="pi-id">' + it.id + '</div></div>';
    html += '<div class="pi-add">' + (added ? '&#10003;' : '+') + '</div>';
    html += '</div>';
  }
  return html;
}

function renderPickerList() {
  var el = document.getElementById('picker-list');
  if (el) el.innerHTML = buildPickerHtml();
}

// ─── EDITOR MUTATIONS ─────────────────────────────────────────────────────────

function edAdd(id) {
  if (activeSlotIndex !== null) {
    edPls[activeSlotIndex].refId = id;
    activeSlotIndex = null;
  } else {
    edPls.push({ refId: id, order: edPls.length + 1, layout: 'body', style: {} });
  }
  renderEditor();
}

function edRemove(rid) {
  edPls = edPls.filter(function(p) { return p.refId !== rid; });
  for (var i = 0; i < edPls.length; i++) edPls[i].order = i + 1;
  renderEditor();
}

function edMove(idx, dir) {
  var ni = idx + dir;
  if (ni < 0 || ni >= edPls.length) return;
  var tmp    = edPls[idx];
  edPls[idx] = edPls[ni];
  edPls[ni]  = tmp;
  for (var i = 0; i < edPls.length; i++) edPls[i].order = i + 1;
  renderEditor();
}

function edLayout(rid, lay) {
  for (var i = 0; i < edPls.length; i++) {
    if (edPls[i].refId === rid) { edPls[i].layout = lay; break; }
  }
}

function saveEditor() {
  var titleEl = document.getElementById('ed-title');
  var t = titleEl ? titleEl.value.trim() : '';
  if (!t)             { toast('Please enter a title.', 'error'); return; }
  if (edPls.length === 0) { toast('Add at least one item.', 'error'); return; }

  var body   = { title: t, target: getEdTarget(), placements: edPls };
  var isEdit = (edBlend && edBlend.id);
  var method = isEdit ? 'PUT'  : 'POST';
  var path   = isEdit ? ('/blends/' + edBlend.id) : '/blends';

  apic(method, path, body).then(function() {
    toast('Blend saved!', 'success');
    closeEditor();
    loadBlends();
  }).catch(function(e) { toast(e.message, 'error'); });
}

function closeEditor() {
  document.getElementById('editor-wrap').innerHTML = '';
  edBlend = null;
  edPls   = [];
}