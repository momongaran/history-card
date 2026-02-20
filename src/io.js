// io.js — JSON save/load + validation

import { getState } from './state.js';

/**
 * exportState() — Download full correspondences as JSON
 */
export function exportState() {
  const state = getState();
  const snapshot = {
    version: '1.0',
    exportedAt: new Date().toISOString(),
    correspondences: state.correspondences,
  };
  const blob = new Blob([JSON.stringify(snapshot, null, 2)], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `myhistory_save_${Date.now()}.json`;
  a.click();
  URL.revokeObjectURL(url);
}

/**
 * importState(file) → Promise<correspondences>
 * Parses, validates, and returns the correspondences object.
 */
export function importState(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => {
      try {
        const data = JSON.parse(reader.result);
        if (!data.correspondences || typeof data.correspondences !== 'object') {
          reject(new Error('Invalid save file: missing correspondences'));
          return;
        }
        resolve(data.correspondences);
      } catch (e) {
        reject(new Error('Failed to parse JSON: ' + e.message));
      }
    };
    reader.onerror = () => reject(new Error('Failed to read file'));
    reader.readAsText(file);
  });
}
