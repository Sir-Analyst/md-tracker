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

function onBrowseFile(event) {
  var file = event.target.files[0];
  if (!file) return;
  var input = document.getElementById('add-file-input');
  var path = file.name;
  if (file.webkitRelativePath) {
    path = file.webkitRelativePath;
  } else if (file.path) {
    path = file.path;
  }
  input.value = path;
  event.target.value = '';
}
