// app.js — Entry point: data load → init → render

import { initState, getState, setInheritanceLinks } from './state.js';
import { initTaxonomy } from './taxonomy.js';
import { computeLayout } from './layout.js';
import { render } from './render.js';
import { initInteractions } from './interact.js';
import { exportState, importState } from './io.js';
import { showStats } from './stats.js';

(async function main() {
  // ── Data loading ──
  const cacheBust = `?t=${Date.now()}`;
  const [fwData, taxonomy, defaultCorrs, inheritData] = await Promise.all([
    fetch(`../data/framework_output_v2_2.json${cacheBust}`).then(r => r.json()),
    fetch(`../data/taxonomy_v2_2.json${cacheBust}`).then(r => r.json()),
    fetch(`../data/default_correspondences.json${cacheBust}`).then(r => r.json()).catch(() => ({})),
    fetch(`../data/inheritance_links_v2_2.json${cacheBust}`).then(r => r.json()).catch(() => ({ inheritanceLinks: [] })),
  ]);

  const events = fwData.events;
  const frameworkViews = fwData.frameworkViews;

  // ── Initialize state ──
  initState(events, frameworkViews, taxonomy);
  initTaxonomy(taxonomy);

  // Load default correspondences
  const state = getState();
  Object.assign(state.correspondences, defaultCorrs);

  // v2.2: Store inheritance links (internal hold, no UI)
  setInheritanceLinks(inheritData.inheritanceLinks || []);
  validateInheritanceLinks(events, frameworkViews);

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

  // ── v2.2: Inheritance link validation (console warnings only) ──
  function validateInheritanceLinks(events, frameworkViews) {
    const links = getState().inheritanceLinks;
    if (!links || links.length === 0) return;

    const eventMap = new Map();
    for (const ev of events) eventMap.set(ev.eventId, ev);

    const elementIds = new Set();
    for (const fv of frameworkViews) {
      for (const el of fv.elements) elementIds.add(el.elementId);
    }

    for (const link of links) {
      const from = eventMap.get(link.fromEventId);
      const to = eventMap.get(link.toEventId);

      // Time-order check
      if (from && to && from.sortKey > to.sortKey) {
        console.warn(`[v2.2 validate] 時系列逆転: ${link.fromEventId}(${from.sortKey}) → ${link.toEventId}(${to.sortKey})`);
      }

      // backgroundRefs existence check
      if (link.backgroundRefs) {
        for (const ref of link.backgroundRefs) {
          if (!elementIds.has(ref)) {
            console.warn(`[v2.2 validate] backgroundRef不在: ${ref} (link: ${link.fromEventId} → ${link.toEventId})`);
          }
        }
      }
    }
  }
})();
