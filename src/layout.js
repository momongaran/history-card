// layout.js — Horizontal badge layout
// Each event row contains its FW's elements as horizontal badges.
// No lane assignment needed (1 event = 1 FW).

// Display order: C → F → P → R
const LAYER_ORDER = { C: 0, F: 1, P: 2, R: 3 };

/**
 * computeLayout(events, frameworkViews, correspondences)
 *
 * Returns: {
 *   totalRows: number,
 *   rows: [
 *     {
 *       event,                    // event object
 *       elements: [               // sorted: C → F → P → R
 *         { element, fwView, seqNo, corr, linkedEventIdx }
 *       ]
 *     }
 *   ],
 *   eventIndex: Map<eventId, rowIndex>
 * }
 */
export function computeLayout(events, frameworkViews, correspondences) {
  const eventIndex = new Map();
  for (let i = 0; i < events.length; i++) {
    eventIndex.set(events[i].eventId, i);
  }

  const rows = events.map(ev => ({
    event: ev,
    elements: [],
  }));

  for (const fwView of frameworkViews) {
    const evIdx = eventIndex.get(fwView.eventId);
    if (evIdx === undefined) continue;

    // Collect all elements, sorted by C → F → P → R
    const sorted = [...fwView.elements].sort((a, b) => {
      const oa = LAYER_ORDER[a.layer] ?? 99;
      const ob = LAYER_ORDER[b.layer] ?? 99;
      return oa - ob;
    });

    let seqNo = 0;
    for (const el of sorted) {
      seqNo++;
      const corr = correspondences?.[fwView.frameworkViewId]?.[el.elementId] || null;
      const linkedEventIdx = corr?.eventId ? (eventIndex.get(corr.eventId) ?? null) : null;

      rows[evIdx].elements.push({
        element: el,
        fwView,
        seqNo,
        corr,
        linkedEventIdx,
      });
    }
  }

  return {
    totalRows: events.length,
    rows,
    eventIndex,
  };
}
