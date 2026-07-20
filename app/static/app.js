function showToast(msg, isError) {
  var t = document.getElementById('toast');
  t.textContent = msg;
  t.className = 'toast show' + (isError ? ' error' : '');
  setTimeout(function() { t.className = 'toast'; }, 3000);
}

async function addFile() {
  var input = document.getElementById('add-file-input');
  var path = input.value.trim();
  if (!path) { showToast('Enter a file path', true); return; }
  try {
    var resp = await fetch('/api/files', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ path: path })
    });
    var data = await resp.json();
    if (!resp.ok) { showToast(data.detail || 'Failed to add file', true); return; }
    input.value = '';
    showToast('Added: ' + data.name);
    setTimeout(function() { location.reload(); }, 500);
  } catch (e) { showToast('Error: ' + e.message, true); }
}

async function deleteFile(id, name) {
  if (!confirm('Remove "' + name + '" from tracking?')) return;
  try {
    var resp = await fetch('/api/files/' + id, { method: 'DELETE' });
    if (!resp.ok) { showToast('Failed to remove', true); return; }
    showToast('Removed: ' + name);
    setTimeout(function() { location.reload(); }, 500);
  } catch (e) { showToast('Error: ' + e.message, true); }
}

async function rescanFile(id) {
  try {
    var resp = await fetch('/api/files/' + id + '/rescan', { method: 'POST' });
    if (!resp.ok) { showToast('Rescan failed', true); return; }
    showToast('File rescanned');
    setTimeout(function() { location.reload(); }, 500);
  } catch (e) { showToast('Error: ' + e.message, true); }
}

async function toggleStep(stepId, checkbox) {
  try {
    var resp = await fetch('/api/steps/' + stepId, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ completed: checkbox.checked })
    });
    if (!resp.ok) { showToast('Toggle failed', true); return; }
    var data = await resp.json();
    checkbox.checked = data.completed === 1;
    updateViewerProgress();
  } catch (e) { showToast('Error: ' + e.message, true); }
}

function updateViewerProgress() {
  var checks = document.querySelectorAll('.step-check');
  var total = checks.length;
  var done = 0;
  checks.forEach(function(c) { if (c.checked) done++; });
  var pct = total > 0 ? Math.round(done / total * 100) : 0;
  var bar = document.getElementById('viewer-progress-fill');
  var label = document.getElementById('viewer-progress-label');
  if (bar) bar.style.width = pct + '%';
  if (label) label.textContent = done + '/' + total + ' (' + pct + '%)';
  if (bar) {
    bar.className = 'viewer-bar-fill';
    if (pct === 100) bar.className += ' done';
  }
}

document.addEventListener('DOMContentLoaded', function() {
  var input = document.getElementById('add-file-input');
  if (input) {
    input.addEventListener('keydown', function(e) {
      if (e.key === 'Enter') addFile();
    });
  }
});

var browserCurrentPath = '';

function openFileBrowser(startPath) {
  var modal = document.getElementById('file-browser-modal');
  modal.style.display = 'flex';
  loadBrowserDir(startPath || '');
}

function closeFileBrowser(e) {
  if (e && e.target !== e.currentTarget) return;
  document.getElementById('file-browser-modal').style.display = 'none';
}

async function loadBrowserDir(path) {
  var list = document.getElementById('browser-file-list');
  var pathEl = document.getElementById('browser-current-path');
  list.innerHTML = '<div style="padding:12px 18px;color:#999;font-size:12px;">Loading...</div>';

  try {
    var url = '/api/browse' + (path ? '?path=' + encodeURIComponent(path) : '');
    var resp = await fetch(url);
    var data = await resp.json();
    if (!resp.ok) { list.innerHTML = '<div style="padding:12px 18px;color:#e74c3c;font-size:12px;">' + data.detail + '</div>'; return; }

    browserCurrentPath = data.current;
    pathEl.textContent = data.current;
    list.innerHTML = '';

    if (data.parent) {
      var back = document.createElement('div');
      back.className = 'browser-item back';
      back.innerHTML = '<span class="bi-icon">&#8593;</span><span class="bi-name">..</span>';
      back.onclick = function() { loadBrowserDir(data.parent); };
      list.appendChild(back);
    }

    var dirs = data.items.filter(function(i) { return i.is_dir; });
    var files = data.items.filter(function(i) { return !i.is_dir; });

    dirs.forEach(function(item) {
      var el = document.createElement('div');
      el.className = 'browser-item dir';
      el.innerHTML = '<span class="bi-icon">&#128193;</span><span class="bi-name">' + item.name + '</span>';
      el.onclick = function() { loadBrowserDir(item.path); };
      list.appendChild(el);
    });

    files.forEach(function(item) {
      if (!/\.(md|markdown|txt)$/i.test(item.name)) return;
      var el = document.createElement('div');
      el.className = 'browser-item file';
      el.innerHTML = '<span class="bi-icon">&#128196;</span><span class="bi-name">' + item.name + '</span>';
      el.onclick = function() {
        list.querySelectorAll('.browser-item.file').forEach(function(f) { f.classList.remove('selected'); });
        el.classList.add('selected');
        document.getElementById('add-file-input').value = item.path;
        closeFileBrowser();
        addFile();
      };
      list.appendChild(el);
    });

    if (dirs.length === 0 && files.filter(function(f) { return /\.(md|markdown|txt)$/i.test(f.name); }).length === 0) {
      list.innerHTML += '<div style="padding:12px 18px;color:#999;font-size:12px;">No markdown files here</div>';
    }
  } catch (e) {
    list.innerHTML = '<div style="padding:12px 18px;color:#e74c3c;font-size:12px;">Failed to load: ' + e.message + '</div>';
  }
}
