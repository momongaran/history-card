// interact.js — UI interactions for horizontal badge layout
// Link creation/edit/delete, category selection, keyboard

import { getState, pushUndo, undo, redo, setCorrespondence, removeCorrespondence, getCorrespondence } from './state.js';
import { getLinkCategories } from './taxonomy.js';

let onRerender = null;

export function initInteractions(rerenderFn) {
  onRerender = rerenderFn;

  // Event delegation on causal body (badges)
  document.getElementById('lanes').addEventListener('click', handleBadgeClick);

  // Event lane click (for link target selection)
  document.getElementById('eventRows').addEventListener('click', handleEventClick);

  // Right-click for link delete
  document.addEventListener('contextmenu', handleContextMenu);

  // Keyboard shortcuts
  document.addEventListener('keydown', handleKeydown);

  // Click elsewhere to cancel linking
  document.addEventListener('click', handleDocumentClick);
}

function rerender() {
  if (onRerender) onRerender();
}

// ── Badge click ──
function handleBadgeClick(e) {
  const badge = e.target.closest('.el-badge');
  if (!badge) return;

  e.stopPropagation();

  const fwViewId = badge.dataset.fwViewId;
  const elementId = badge.dataset.elementId;

  if (badge.classList.contains('no-link')) {
    // No link → start linking (select event)
    startLinking(badge, fwViewId, elementId);
  } else if (badge.classList.contains('has-link')) {
    // Has link → show L-code dropdown
    showCategoryDropdown(badge, fwViewId, elementId);
  }
}

// ── Context menu (right-click) on badge ──
function handleContextMenu(e) {
  const badge = e.target.closest('.el-badge.has-link');
  if (badge) {
    e.preventDefault();
    const fwViewId = badge.dataset.fwViewId;
    const elementId = badge.dataset.elementId;
    if (confirm('対応リンクを削除しますか？')) {
      pushUndo();
      removeCorrespondence(fwViewId, elementId);
      rerender();
    }
  }
}

// ── Link creation ──
function startLinking(badgeEl, fwViewId, elementId) {
  const state = getState();
  cancelLinking();

  state.ui.linking = { fwViewId, elementId };
  state.ui.selectedDot = badgeEl;

  badgeEl.classList.add('is-linking');
  document.getElementById('eventRows').classList.add('is-target-mode');
  updateStatus('イベントを選択してください（Escでキャンセル）');
}

function cancelLinking() {
  const state = getState();
  if (state.ui.selectedDot) {
    state.ui.selectedDot.classList.remove('is-linking');
  }
  state.ui.linking = null;
  state.ui.selectedDot = null;
  document.getElementById('eventRows').classList.remove('is-target-mode');
  closeDropdown();
  updateStatus('');
}

// ── Event selection (link target) ──
function handleEventClick(e) {
  const state = getState();
  if (!state.ui.linking) return;

  const eventRow = e.target.closest('.event-row');
  if (!eventRow) return;

  e.stopPropagation();

  const eventId = eventRow.dataset.eventId;
  if (!eventId) return;

  const { fwViewId, elementId } = state.ui.linking;

  pushUndo();
  setCorrespondence(fwViewId, elementId, eventId, null, null);
  cancelLinking();
  rerender();
}

// ── Category dropdown ──
let activeDropdown = null;

function showCategoryDropdown(triggerEl, fwViewId, elementId) {
  closeDropdown();

  const linkCategories = getLinkCategories();

  const dropdown = document.createElement('div');
  dropdown.className = 'cat-dropdown';

  const header = document.createElement('div');
  header.className = 'cat-dropdown-header';
  header.textContent = 'リンクカテゴリ（Lコード）';
  dropdown.appendChild(header);

  // Re-link option
  const relinkItem = document.createElement('div');
  relinkItem.className = 'cat-dropdown-item cat-dropdown-relink';
  relinkItem.textContent = '↻ イベント再選択';
  relinkItem.addEventListener('click', (e) => {
    e.stopPropagation();
    closeDropdown();
    startLinking(triggerEl, fwViewId, elementId);
  });
  dropdown.appendChild(relinkItem);

  const sep = document.createElement('div');
  sep.className = 'cat-dropdown-sep';
  dropdown.appendChild(sep);

  for (const lcat of linkCategories) {
    const item = document.createElement('div');
    item.className = 'cat-dropdown-item';
    item.textContent = `${lcat.code}: ${lcat.name}`;
    item.addEventListener('click', (e) => {
      e.stopPropagation();
      pushUndo();
      const corr = getCorrespondence(fwViewId, elementId);
      setCorrespondence(
        fwViewId, elementId,
        corr?.eventId || null,
        lcat.code,
        null
      );
      closeDropdown();
      rerender();
    });
    dropdown.appendChild(item);
  }

  // Position near the trigger
  const rect = triggerEl.getBoundingClientRect();
  dropdown.style.position = 'fixed';
  dropdown.style.left = `${rect.left}px`;
  dropdown.style.top = `${rect.bottom + 4}px`;
  dropdown.style.zIndex = '9999';

  document.body.appendChild(dropdown);
  activeDropdown = dropdown;
}

function closeDropdown() {
  if (activeDropdown) {
    activeDropdown.remove();
    activeDropdown = null;
  }
}

// ── Keyboard shortcuts ──
function handleKeydown(e) {
  if ((e.ctrlKey || e.metaKey) && !e.shiftKey && e.key.toLowerCase() === 'z') {
    e.preventDefault();
    if (undo()) rerender();
    return;
  }
  if ((e.ctrlKey || e.metaKey) && e.shiftKey && e.key.toLowerCase() === 'z') {
    e.preventDefault();
    if (redo()) rerender();
    return;
  }
  if (e.key === 'Escape') {
    cancelLinking();
  }
}

// ── Document click → cancel linking ──
function handleDocumentClick(e) {
  const state = getState();
  if (state.ui.linking) {
    if (!e.target.closest('#eventRows') && !e.target.closest('#lanes')) {
      cancelLinking();
    }
  }
  if (activeDropdown && !activeDropdown.contains(e.target)) {
    closeDropdown();
  }
}

function updateStatus(msg) {
  const statusEl = document.getElementById('statusText');
  if (msg) {
    statusEl.textContent = msg;
  } else {
    const state = getState();
    const corrCount = Object.values(state.correspondences)
      .reduce((sum, fwCorrs) => sum + Object.keys(fwCorrs).length, 0);
    statusEl.textContent = `イベント ${state.events.length}件｜FW ${state.frameworkViews.length}件｜対応リンク ${corrCount}件`;
  }
}
