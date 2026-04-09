// ─── CANVAS STATE ─────────────────────────────────────────────────────────────

var cvBlend = null;
var cvPls   = [];
var cvSelId = null;
var cvVp    = 'desktop';
var cvXml   = false;
var cvTimer = null;

// ─── OPEN / CLOSE ─────────────────────────────────────────────────────────────

function openCanvas(blendId) {
  for (var i = 0; i < blends.length; i++) {
    if (blends[i].id === blendId) {
      cvBlend = JSON.parse(JSON.stringify(blends[i]));
      break;
    }
  }
  if (!cvBlend) return;

  cvPls = (cvBlend.placements || []).map(function(p) {
    return { refId: p.refId, order: p.order, layout: p.layout,
             style: p.style ? JSON.parse(JSON.stringify(p.style)) : {} };
  });
  cvSelId = null;
  cvXml   = false;
  cvTimer = null;

  var pages = document.querySelectorAll('.page');
  for (var j = 0; j < pages.length; j++) pages[j].classList.remove('active');
  document.getElementById('canvas-page').classList.add('active');
  document.getElementById('stitle').value      = cvBlend.title || '';
  document.getElementById('cvurl').textContent = 'blend/' + cvBlend.id;
  document.getElementById('exp-link').href     = API + '/blends/' + cvBlend.id + '/export/html';
  document.getElementById('xdrawer').style.display = 'none';

  cvSetTarget(cvBlend.target, true);
  cvSetVp('desktop');
  cvRender();
  cvRenderLayers();
  cvRenderProps();
}

function closeCanvas() {
  document.getElementById('canvas-page').classList.remove('active');
  var pages = document.querySelectorAll('.page');
  for (var i = 0; i < pages.length; i++) pages[i].classList.remove('active');
  document.getElementById('page-blend').classList.add('active');
  document.getElementById('nav-bank').classList.remove('active');
  document.getElementById('nav-blend').classList.add('active');
  loadBlends();
  cvBlend = null; cvPls = []; cvSelId = null;
}

// ─── TOOLBAR CONTROLS ─────────────────────────────────────────────────────────

function cvTitleChange() {
  if (cvBlend) cvBlend.title = document.getElementById('stitle').value;
  cvSched();
}

function cvSetTarget(t, noSave) {
  if (cvBlend) cvBlend.target = t;
  var wb = document.getElementById('sbtn-web');
  var pb = document.getElementById('sbtn-pdf');
  if (!wb || !pb) return;
  wb.classList.remove('web');
  pb.classList.remove('pdf');
  if (t === 'Web') wb.classList.add('web');
  else             pb.classList.add('pdf');
  if (!noSave) cvSched();
}

function cvSetVp(vp) {
  cvVp = vp;
  var frame = document.getElementById('cframe');
  if (vp === 'desktop')    frame.style.width = '100%';
  else if (vp === 'tablet') frame.style.width = '768px';
  else                      frame.style.width = '390px';

  var map = { 'vp-d': 'desktop', 'vp-t': 'tablet', 'vp-m': 'mobile' };
  for (var k in map) {
    var b = document.getElementById(k);
    if (b) b.classList.toggle('active', map[k] === vp);
  }
}

// ─── RENDER ───────────────────────────────────────────────────────────────────

function getItem(id) {
  for (var i = 0; i < bankItems.length; i++) {
    if (bankItems[i].id === id) return bankItems[i];
  }
  return null;
}

function cvRender() {
  var container = document.getElementById('cblocks');
  if (!container) return;
  var html = '';

  for (var i = 0; i < cvPls.length; i++) {
    var pl = cvPls[i];
    if (pl.style && pl.style.hidden === 'true') continue;
    var it = getItem(pl.refId);
    if (!it) continue;

    var st      = pl.style || {};
    var selCls  = (cvSelId === pl.refId) ? ' sel' : '';
    var w       = st.width || '100%';
    var mg      = st.margin       ? 'margin:'       + st.margin       + ';' : '';
    var br      = st.borderRadius ? 'border-radius:' + st.borderRadius + ';' : '';
    var blockStyle = 'width:' + w + ';' + mg + br;

    html += '<div class="cblock' + selCls + '" data-idx="' + i + '" draggable="true"' +
      ' onclick="cvSel(\'' + pl.refId + '\',event)"' +
      ' ondragstart="cbDragStart(event,' + i + ')" ondragend="cbDragEnd(event)"' +
      ' ondragover="cbDragOver(event)" ondragleave="cbDragLeave(event)"' +
      ' ondrop="cbDrop(event,' + i + ')">';
    html += '<div class="blabel">' + pl.refId + '</div>';

    if (it.mediaType && it.mediaType.indexOf('text') === 0) {
      if (pl.layout === 'hero') {
        var bg  = st.background  || '#1a1a2e';
        var pad = st.padding     || '48px 40px';
        var fs  = st.fontSize    || '32px';
        var fw  = st.fontWeight  || '800';
        var col = st.color       || '#ffffff';
        html += '<div style="background:' + bg + ';padding:' + pad + ';' + blockStyle + '">';
        html += '<h1 style="font-family:Syne,sans-serif;font-size:' + fs + ';font-weight:' + fw +
          ';color:' + col + ';margin:0 0 10px 0;">' + (it.title || '') + '</h1>';
        html += '<p style="color:' + col + ';opacity:.85;font-size:16px;margin:0 0 8px 0;">' + (it.body || '') + '</p>';
        html += '<div style="color:' + col + ';opacity:.4;font-size:12px;">' +
          ((it.meta && it.meta.author) ? it.meta.author : '') + '</div>';
        html += '</div>';
      } else {
        var bg2  = st.background || '#ffffff';
        var pad2 = st.padding    || '24px 32px';
        var fs2  = st.fontSize   || '20px';
        var fw2  = st.fontWeight || '700';
        var col2 = st.color      || '#0e0e16';
        var lh2  = st.lineHeight || '1.6';
        html += '<div style="background:' + bg2 + ';padding:' + pad2 + ';' + blockStyle + '">';
        html += '<h2 style="border-left:3px solid #7c5cfc;padding-left:12px;font-family:Syne,sans-serif;' +
          'font-size:' + fs2 + ';font-weight:' + fw2 + ';color:' + col2 + ';margin:0 0 10px 0;">' +
          (it.title || '') + '</h2>';
        html += '<p style="color:' + col2 + ';line-height:' + lh2 + ';margin:0;">' + (it.body || '') + '</p>';
        html += '</div>';
      }

    } else if (it.mediaType && it.mediaType.indexOf('image') === 0) {
      var isrc = (it.asset && it.asset.src) ? it.asset.src : '';
      var ialt = (it.asset && it.asset.alt) ? it.asset.alt : '';
      var ar   = st.aspectRatio || '16/9';
      var of   = st.objectFit  || 'cover';
      var ibr  = st.borderRadius || '0px';
      html += '<div style="padding:0;background:transparent;' + mg + '">';
      html += '<img src="' + isrc + '" alt="' + ialt +
        '" style="width:100%;aspect-ratio:' + ar + ';object-fit:' + of +
        ';border-radius:' + ibr + ';display:block;" onerror="this.style.opacity=0.3">';
      if (it.caption) html += '<div style="padding:6px 12px;font-size:12px;color:#666;background:#fff;">' + it.caption + '</div>';
      html += '</div>';

    } else if (it.mediaType && it.mediaType.indexOf('video') === 0) {
      var vsrc = (it.asset && it.asset.src) ? it.asset.src : '';
      var var2 = st.aspectRatio || '16/9';
      var vbr  = st.borderRadius || '0px';
      html += '<div style="padding:0;background:transparent;' + mg + '">';
      html += '<div style="background:#000;border-radius:' + vbr + ';overflow:hidden;">';
      html += '<div style="display:flex;align-items:center;gap:8px;padding:8px 12px;background:#111;">' +
        '<div style="width:8px;height:8px;border-radius:50%;background:#f43f5e;"></div>' +
        '<span style="color:#ccc;font-size:12px;">' + (it.title || '') + '</span></div>';
      html += '<iframe src="' + vsrc + '" style="width:100%;aspect-ratio:' + var2 +
        ';border:none;display:block;" allowfullscreen></iframe>';
      if (it.caption) html += '<div style="padding:6px 12px;font-size:12px;color:#ccc;">' + it.caption + '</div>';
      html += '</div></div>';
    }

    html += '</div>'; // close cblock
  }
  container.innerHTML = html;
}

// ─── LAYERS PANEL ─────────────────────────────────────────────────────────────

function cvRenderLayers() {
  var list = document.getElementById('llist');
  if (!list) return;
  var vis  = 0;
  var html = '';

  for (var i = 0; i < cvPls.length; i++) {
    var pl     = cvPls[i];
    var it     = getItem(pl.refId);
    var hidden = pl.style && pl.style.hidden === 'true';
    if (!hidden) vis++;
    var selCls = cvSelId === pl.refId ? ' sel' : '';
    var hidCls = hidden ? ' hid' : '';
    var icon   = it ? mediaIcon(it.mediaType) : '?';
    var name   = it ? (it.title || pl.refId) : pl.refId;

    html += '<div class="litem' + selCls + hidCls + '" data-idx="' + i + '" draggable="true"' +
      ' onclick="cvSel(\'' + pl.refId + '\',event)"' +
      ' ondragstart="lDragStart(event,' + i + ')"' +
      ' ondragover="lDragOver(event,' + i + ')"' +
      ' ondragleave="lDragLeave(event,' + i + ')"' +
      ' ondrop="lDrop(event,' + i + ')">';
    html += '<div class="litem-icon">' + icon + '</div>';
    html += '<div class="litem-info"><div class="litem-name">' + name +
      '</div><div class="litem-id">' + pl.refId + '</div></div>';
    html += '</div>';
  }

  list.innerHTML = html;
  var hdr = document.getElementById('layers-hdr');
  if (hdr) hdr.textContent = 'Layers ' + vis + '/' + cvPls.length;
}

// ─── PROPERTIES PANEL ─────────────────────────────────────────────────────────

function cvRenderProps() {
  var pbody = document.getElementById('pbody');
  if (!pbody) return;
  if (!cvSelId) {
    pbody.innerHTML = '<div class="empty-state"><div class="es-icon">[ ]</div><p>Select a block to edit its properties</p></div>';
    return;
  }

  var pl = null;
  for (var i = 0; i < cvPls.length; i++) {
    if (cvPls[i].refId === cvSelId) { pl = cvPls[i]; break; }
  }
  if (!pl) { pbody.innerHTML = ''; return; }

  var it     = getItem(pl.refId);
  var st     = pl.style || {};
  var isHidden = st.hidden === 'true';
  var isText = it && it.mediaType && it.mediaType.indexOf('text')  === 0;
  var isImg  = it && it.mediaType && it.mediaType.indexOf('image') === 0;
  var isVid  = it && it.mediaType && it.mediaType.indexOf('video') === 0;
  var name   = it ? (it.title || pl.refId) : pl.refId;

  var html = '<div class="prop-blk-hdr">';
  html += '<div><div class="prop-blk-id">' + pl.refId +
    '</div><div class="prop-blk-title">' + name + '</div></div>';
  html += '<div class="prop-blk-btns">';
  html += '<button class="phide-btn' + (isHidden ? ' hidden-on' : '') +
    '" onclick="cvPropHide()" title="' + (isHidden ? 'Show' : 'Hide') + '">' +
    (isHidden ? '&#128065;' : '&#9632;') + '</button>';
  html += '<button class="premove-btn" onclick="cvPropRemove()" title="Remove">&#10005;</button>';
  html += '</div></div>';

  // Layout
  html += '<div class="prop-section"><div class="prop-section-title">Layout</div>';
  html += '<div class="prop-row"><label>Layout</label><select onchange="cvPropSet(\'layout\',this.value,true)">';
  var lays = ['hero', 'full-width', 'body', 'sidebar', 'media-embed', 'card'];
  for (var li = 0; li < lays.length; li++) {
    html += '<option value="' + lays[li] + '"' + (pl.layout === lays[li] ? ' selected' : '') + '>' + lays[li] + '</option>';
  }
  html += '</select></div></div>';

  // Spacing
  html += '<div class="prop-section"><div class="prop-section-title">Spacing</div>';
  html += pslider('Padding',    'padding',      parsePx(st.padding, 24),        0, 80, 'px');
  html += pslider('Margin Bot', 'marginBottom', parsePxBottom(st.margin),       0, 64, 'px');
  html += '</div>';

  // Appearance
  html += '<div class="prop-section"><div class="prop-section-title">Appearance</div>';
  html += pcolor('Background', 'background', st.background || '#ffffff');
  html += pslider('Radius', 'borderRadius', parsePx(st.borderRadius, 0), 0, 48, 'px');
  html += '<div class="prop-row"><label>Width</label><select onchange="cvPropSet(\'width\',this.value)">';
  var widths = ['100%', '75%', '50%', '25%'];
  for (var wi = 0; wi < widths.length; wi++) {
    html += '<option value="' + widths[wi] + '"' + (st.width === widths[wi] ? ' selected' : '') + '>' + widths[wi] + '</option>';
  }
  html += '</select></div></div>';

  // Typography (text only)
  if (isText) {
    html += '<div class="prop-section"><div class="prop-section-title">Typography</div>';
    html += pslider('Font Size', 'fontSize', parsePx(st.fontSize, 20), 10, 48, 'px');
    html += '<div class="prop-row"><label>Weight</label><select onchange="cvPropSet(\'fontWeight\',this.value)">';
    var weights = [['300','Light'],['400','Regular'],['500','Medium'],['600','Semibold'],['700','Bold'],['800','Black']];
    for (var fw = 0; fw < weights.length; fw++) {
      html += '<option value="' + weights[fw][0] + '"' + (st.fontWeight === weights[fw][0] ? ' selected' : '') + '>' + weights[fw][1] + '</option>';
    }
    html += '</select></div>';
    html += pslider('Line Height', 'lineHeight', Math.round((parseFloat(st.lineHeight) || 1.6) * 10), 10, 30, '');
    html += pcolor('Text Color', 'color', st.color || '#000000');
    html += '</div>';
  }

  // Image options
  if (isImg) {
    html += '<div class="prop-section"><div class="prop-section-title">Image</div>';
    html += '<div class="prop-row"><label>Fit</label><select onchange="cvPropSet(\'objectFit\',this.value)">';
    var fits = ['cover', 'contain', 'fill', 'none'];
    for (var fi = 0; fi < fits.length; fi++) {
      html += '<option value="' + fits[fi] + '"' + (st.objectFit === fits[fi] ? ' selected' : '') + '>' + fits[fi] + '</option>';
    }
    html += '</select></div>';
    html += '<div class="prop-row"><label>Ratio</label><select onchange="cvPropSet(\'aspectRatio\',this.value)">';
    var ratios = ['16/9', '4/3', '1/1', '3/2', '21/9'];
    for (var ri = 0; ri < ratios.length; ri++) {
      html += '<option value="' + ratios[ri] + '"' + (st.aspectRatio === ratios[ri] ? ' selected' : '') + '>' + ratios[ri] + '</option>';
    }
    html += '</select></div></div>';
  }

  // Video options
  if (isVid) {
    html += '<div class="prop-section"><div class="prop-section-title">Video</div>';
    html += '<div class="prop-row"><label>Ratio</label><select onchange="cvPropSet(\'aspectRatio\',this.value)">';
    var vrs = ['16/9', '4/3', '1/1'];
    for (var vri = 0; vri < vrs.length; vri++) {
      html += '<option value="' + vrs[vri] + '"' + (st.aspectRatio === vrs[vri] ? ' selected' : '') + '>' + vrs[vri] + '</option>';
    }
    html += '</select></div></div>';
  }

  pbody.innerHTML = html;
}

// ─── PROP HELPERS ─────────────────────────────────────────────────────────────

function parsePx(val, def) {
  if (!val) return def || 0;
  return parseInt(val) || def || 0;
}

function parsePxBottom(val) {
  if (!val) return 0;
  var parts = val.split(' ');
  if (parts.length >= 3) return parseInt(parts[2]) || 0;
  return 0;
}

function pslider(lbl, key, val, min, max, unit) {
  var display = (unit === '' && key === 'lineHeight') ? ((val / 10).toFixed(1)) : (val + unit);
  return '<div class="prop-row"><label>' + lbl + '</label>' +
    '<input type="range" min="' + min + '" max="' + max + '" value="' + val +
    '" oninput="cvSlider(\'' + key + '\',this.value,\'' + unit + '\')"' +
    ' onchange="cvSlider(\'' + key + '\',this.value,\'' + unit + '\')">' +
    '<span class="pval" id="pv-' + key + '">' + display + '</span></div>';
}

function pcolor(lbl, key, val) {
  return '<div class="prop-row"><label>' + lbl + '</label>' +
    '<input type="color" value="' + (val || '#ffffff') +
    '" oninput="cvPropSet(\'' + key + '\',this.value)"' +
    ' onchange="cvPropSet(\'' + key + '\',this.value)"></div>';
}

function cvSlider(key, raw, unit) {
  var disp;
  if (key === 'lineHeight') {
    disp = (raw / 10).toFixed(1);
    cvPropSet('lineHeight', disp);
  } else if (key === 'marginBottom') {
    disp = raw + 'px';
    cvPropSet('margin', '0 0 ' + raw + 'px 0');
  } else {
    disp = raw + unit;
    cvPropSet(key, raw + unit);
  }
  var el = document.getElementById('pv-' + key);
  if (el) el.textContent = disp;
}

function cvPropSet(key, val, isLayout) {
  for (var i = 0; i < cvPls.length; i++) {
    if (cvPls[i].refId === cvSelId) {
      if (isLayout) {
        cvPls[i].layout = val;
      } else {
        if (!cvPls[i].style) cvPls[i].style = {};
        cvPls[i].style[key] = val;
      }
      break;
    }
  }
  cvRender();
  cvUpdateXml();
  cvSched();
}

function cvPropHide() {
  for (var i = 0; i < cvPls.length; i++) {
    if (cvPls[i].refId === cvSelId) {
      if (!cvPls[i].style) cvPls[i].style = {};
      cvPls[i].style.hidden = (cvPls[i].style.hidden === 'true') ? 'false' : 'true';
      break;
    }
  }
  cvRender(); cvRenderLayers(); cvRenderProps(); cvSched();
}

function cvPropRemove() {
  cvPls = cvPls.filter(function(p) { return p.refId !== cvSelId; });
  for (var i = 0; i < cvPls.length; i++) cvPls[i].order = i + 1;
  cvSelId = null;
  cvRender(); cvRenderLayers(); cvRenderProps(); cvSched();
}

function cvSel(id, e) {
  if (e) e.stopPropagation();
  cvSelId = (cvSelId === id) ? null : id;
  cvRender(); cvRenderLayers(); cvRenderProps();
}

function cvDesel() {
  cvSelId = null;
  cvRender(); cvRenderLayers(); cvRenderProps();
}

// ─── CANVAS DRAG/DROP ─────────────────────────────────────────────────────────

function cbDragStart(e, idx) {
  e.dataTransfer.setData('text/plain', String(idx));
  e.currentTarget.style.opacity = '0.35';
}
function cbDragEnd(e)      { e.currentTarget.style.opacity = '1'; }
function cbDragOver(e)     { e.preventDefault(); e.currentTarget.classList.add('cdrag-over'); }
function cbDragLeave(e)    { e.currentTarget.classList.remove('cdrag-over'); }
function cbDrop(e, toIdx) {
  e.preventDefault();
  e.currentTarget.classList.remove('cdrag-over');
  var fromIdx = parseInt(e.dataTransfer.getData('text/plain'));
  if (isNaN(fromIdx) || fromIdx === toIdx) return;
  var moved = cvPls.splice(fromIdx, 1)[0];
  cvPls.splice(toIdx, 0, moved);
  for (var i = 0; i < cvPls.length; i++) cvPls[i].order = i + 1;
  cvRender(); cvRenderLayers(); cvSched();
}

// ─── LAYERS DRAG/DROP ─────────────────────────────────────────────────────────

var lDragIdx = -1;
function lDragStart(e, idx) {
  lDragIdx = idx;
  e.dataTransfer.setData('text/plain', String(idx));
}
function lDragOver(e, idx) {
  e.preventDefault();
  var items = document.querySelectorAll('.litem');
  for (var i = 0; i < items.length; i++) items[i].classList.remove('dover');
  if (items[idx]) items[idx].classList.add('dover');
}
function lDragLeave(e, idx) {
  var items = document.querySelectorAll('.litem');
  if (items[idx]) items[idx].classList.remove('dover');
}
function lDrop(e, toIdx) {
  e.preventDefault();
  var items = document.querySelectorAll('.litem');
  for (var i = 0; i < items.length; i++) items[i].classList.remove('dover');
  var fromIdx = parseInt(e.dataTransfer.getData('text/plain'));
  if (isNaN(fromIdx) || fromIdx === toIdx) return;
  var moved = cvPls.splice(fromIdx, 1)[0];
  cvPls.splice(toIdx, 0, moved);
  for (var i = 0; i < cvPls.length; i++) cvPls[i].order = i + 1;
  cvRender(); cvRenderLayers(); cvSched();
}

// ─── AUTO SAVE ────────────────────────────────────────────────────────────────

function cvSched() {
  if (!cvBlend || !cvBlend.id) return;
  var ss = document.getElementById('sstatus');
  if (ss) ss.textContent = '...';
  clearTimeout(cvTimer);
  cvTimer = setTimeout(function() {
    apic('PUT', '/blends/' + cvBlend.id, buildCvBody()).then(function() {
      var ss2 = document.getElementById('sstatus');
      if (ss2) { ss2.textContent = 'Saved'; setTimeout(function() { if (ss2) ss2.textContent = ''; }, 2000); }
    }).catch(function() {});
  }, 900);
}

function buildCvBody() {
  var pls = [];
  for (var i = 0; i < cvPls.length; i++) {
    var pl = cvPls[i];
    var st = {};
    if (pl.style) {
      for (var k in pl.style) {
        if (pl.style[k] !== null && pl.style[k] !== undefined) st[k] = pl.style[k];
      }
    }
    var entry = { refId: pl.refId, order: pl.order, layout: pl.layout };
    if (Object.keys(st).length > 0) entry.style = st;
    pls.push(entry);
  }
  return { title: cvBlend.title, target: cvBlend.target, placements: pls };
}

function cvSave() {
  if (!cvBlend) return;
  var btn = document.querySelector('.ssavebtn');
  if (btn) { btn.disabled = true; btn.textContent = '...'; }
  var method = cvBlend.id ? 'PUT'  : 'POST';
  var path   = cvBlend.id ? ('/blends/' + cvBlend.id) : '/blends';
  apic(method, path, buildCvBody()).then(function(d) {
    toast('Saved!', 'success');
    if (d.blend) cvBlend = d.blend;
  }).catch(function(e) {
    toast(e.message, 'error');
  }).finally(function() {
    if (btn) { btn.disabled = false; btn.textContent = 'Save'; }
  });
}

// ─── XML DRAWER ───────────────────────────────────────────────────────────────

function cvToggleXml() {
  cvXml = !cvXml;
  var drawer = document.getElementById('xdrawer');
  var btn    = document.getElementById('xmlbtn');
  if (drawer) drawer.style.display = cvXml ? 'block' : 'none';
  if (btn)    btn.classList.toggle('on', cvXml);
  if (cvXml)  cvUpdateXml();
}

function cvUpdateXml() {
  if (!cvXml) return;
  var el = document.getElementById('xprev');
  if (!el) return;

  var btitle = cvBlend ? (cvBlend.title  || '') : '';
  var btgt   = cvBlend ? (cvBlend.target || 'Web') : 'Web';
  var bid    = cvBlend ? (cvBlend.id     || '') : '';
  var lines  = ['<CBlend BlendID="' + bid + '" Title="' + btitle + '" Target="' + btgt + '">'];

  for (var i = 0; i < cvPls.length; i++) {
    var pl = cvPls[i];
    var st = pl.style || {};
    var hasStyle = false;
    for (var k in st) { if (st[k] !== null && st[k] !== undefined) { hasStyle = true; break; } }

    if (hasStyle) {
      lines.push('  <Placement Order="' + pl.order + '" RefID="' + pl.refId + '" Layout="' + pl.layout + '">');
      var stAttrs = '';
      for (var k2 in st) {
        if (st[k2] !== null && st[k2] !== undefined) stAttrs += ' ' + k2 + '="' + st[k2] + '"';
      }
      lines.push('    <Style' + stAttrs + '/>');
      lines.push('  </Placement>');
    } else {
      lines.push('  <Placement Order="' + pl.order + '" RefID="' + pl.refId + '" Layout="' + pl.layout + '"/>');
    }
  }
  lines.push('</CBlend>');
  el.textContent = lines.join('\n');
}