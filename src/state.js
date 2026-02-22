// state.js — Central state + Undo/Redo
// correspondences are the only user-editable data; layout is derived.

const state = {
  events: [],
  frameworkViews: [],
  taxonomy: null,
  // correspondences: { [fwViewId]: { [elementId]: { eventId, category, subCategory } } }
  correspondences: {},
  // v2.2: inheritance links (internal hold only, not rendered)
  inheritanceLinks: [],
  layout: null,
  ui: {
    linking: null,       // { fwViewId, elementId } when in link-creation mode
    selectedDot: null,   // DOM element of the active dot
  },
};

// Undo/Redo stacks — store JSON snapshots of correspondences only
const undoStack = [];
const redoStack = [];
const MAX_UNDO = 50;

export function getState() {
  return state;
}

export function initState(events, frameworkViews, taxonomy) {
  state.events = events;
  state.frameworkViews = frameworkViews;
  state.taxonomy = taxonomy;
  state.correspondences = {};
  state.inheritanceLinks = [];
  undoStack.length = 0;
  redoStack.length = 0;
}

// v2.2: Store inheritance links (internal only)
export function setInheritanceLinks(links) {
  state.inheritanceLinks = links || [];
}

export function pushUndo() {
  undoStack.push(JSON.stringify(state.correspondences));
  if (undoStack.length > MAX_UNDO) undoStack.shift();
  redoStack.length = 0;  // new action clears redo
}

export function undo() {
  if (undoStack.length === 0) return false;
  redoStack.push(JSON.stringify(state.correspondences));
  state.correspondences = JSON.parse(undoStack.pop());
  return true;
}

export function redo() {
  if (redoStack.length === 0) return false;
  undoStack.push(JSON.stringify(state.correspondences));
  state.correspondences = JSON.parse(redoStack.pop());
  return true;
}

export function canUndo() { return undoStack.length > 0; }
export function canRedo() { return redoStack.length > 0; }

// Set a correspondence for an element
export function setCorrespondence(fwViewId, elementId, eventId, category, subCategory) {
  if (!state.correspondences[fwViewId]) {
    state.correspondences[fwViewId] = {};
  }
  state.correspondences[fwViewId][elementId] = { eventId, category, subCategory };
}

// Remove a correspondence
export function removeCorrespondence(fwViewId, elementId) {
  if (state.correspondences[fwViewId]) {
    delete state.correspondences[fwViewId][elementId];
    if (Object.keys(state.correspondences[fwViewId]).length === 0) {
      delete state.correspondences[fwViewId];
    }
  }
}

// Get correspondence for an element
export function getCorrespondence(fwViewId, elementId) {
  return state.correspondences[fwViewId]?.[elementId] || null;
}
