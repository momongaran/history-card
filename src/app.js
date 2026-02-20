// app.js — Entry point: data load → init → render

import { initState, getState } from './state.js';
import { initTaxonomy } from './taxonomy.js';
import { computeLayout } from './layout.js';
import { render } from './render.js';
import { initInteractions } from './interact.js';
import { exportState, importState } from './io.js';
import { showStats } from './stats.js';

(async function main() {
  // ── Data loading ──
  const cacheBust = `?t=${Date.now()}`;
  const [fwData, taxonomy, defaultCorrs] = await Promise.all([
    fetch(`../data/framework_output_v2_0_freeze.json${cacheBust}`).then(r => r.json()),
    fetch(`../data/taxonomy.json${cacheBust}`).then(r => r.json()),
    fetch(`../data/default_correspondences.json${cacheBust}`).then(r => r.json()).catch(() => ({})),
  ]);

  const events = fwData.events;
  const frameworkViews = fwData.frameworkViews;

  // ── Initialize state ──
  initState(events, frameworkViews, taxonomy);
  initTaxonomy(taxonomy);

  // Load default correspondences
  const state = getState();
  Object.assign(state.correspondences, defaultCorrs);

  // ── Compute layout + render ──
  function fullRerender() {
    const state = getState();
    const layout = computeLayout(state.events, state.frameworkViews, state.correspondences);
    state.layout = layout;
    render(layout);
    updateStatus();
  }

  fullRerender();

  // ── Interactions ──
  initInteractions(fullRerender);

  // ── Scroll sync ──
  const eventScroll = document.getElementById('eventScroll');
  const lanesScroll = document.getElementById('lanesScroll');
  let ticking = false;

  eventScroll.addEventListener('scroll', () => {
    if (!ticking) {
      requestAnimationFrame(() => {
        lanesScroll.scrollTop = eventScroll.scrollTop;
        ticking = false;
      });
      ticking = true;
    }
  });

  let ticking2 = false;
  lanesScroll.addEventListener('scroll', () => {
    if (!ticking2) {
      requestAnimationFrame(() => {
        eventScroll.scrollTop = lanesScroll.scrollTop;
        ticking2 = false;
      });
      ticking2 = true;
    }
  });

  // ── IO buttons ──
  document.getElementById('btnSave').addEventListener('click', () => {
    exportState();
  });

  const fileInput = document.getElementById('fileInput');
  document.getElementById('btnLoad').addEventListener('click', () => {
    fileInput.click();
  });

  fileInput.addEventListener('change', async () => {
    const file = fileInput.files[0];
    if (!file) return;
    try {
      const correspondences = await importState(file);
      const state = getState();
      state.correspondences = correspondences;
      fullRerender();
    } catch (e) {
      alert('読込エラー: ' + e.message);
    }
    fileInput.value = '';
  });

  // ── Stats button ──
  document.getElementById('btnStats').addEventListener('click', () => {
    showStats();
  });

  // ── Status ──
  function updateStatus() {
    const state = getState();
    const corrCount = Object.values(state.correspondences)
      .reduce((sum, fwCorrs) => sum + Object.keys(fwCorrs).length, 0);
    document.getElementById('statusText').textContent =
      `イベント ${events.length}件｜FW ${frameworkViews.length}件｜対応リンク ${corrCount}件`;
  }
})();
