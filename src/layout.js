// layout.js — Horizontal badge layout
// Each event row contains its FW's elements as horizontal badges.
// No lane assignment needed (1 event = 1 FW).

/**
 * computeLayout(events, frameworkViews, correspondences)
 *
 * Returns: {
 *   totalRows: number,
 *   rows: [
 *     {
 *       event,                    // event object
 *       elements: [               // sorted: C → P → R
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

    // Get lane elements in order
    const laneElements = [];
    if (fwView.lanes && fwView.lanes[0]) {
      const elementMap = new Map();
      for (const el of fwView.elements) {
        elementMap.set(el.elementId, el);
      }
      for (const elId of fwView.lanes[0].elements) {
        const el = elementMap.get(elId);
        if (el) laneElements.push(el);
      }
    }

    let seqNo = 0;
    for (const el of laneElements) {
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
