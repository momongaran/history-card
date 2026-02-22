#!/usr/bin/env python3
"""
convert_v22_to_v30.py — v2.2 (C/F/P/R) → v3.0 (B/F/E) 全面移行スクリプト

変換ルール:
  - C → B  (elementId はそのまま、subCategory の C- → B- プレフィックス変更)
  - F → F  (そのまま)
  - P → 削除 (各FWの notes.legacyPath に保存)
  - R → E  (subCategory の R- → E- プレフィックス変更)

出力:
  - data/framework_output_v3_0_bfe.json
  - data/taxonomy_v3_0_bfe.json
  - data/inheritance_links_v3_0_bfe.json
  - data/default_correspondences_v3_0_bfe.json
"""

import json
import sys
import os
from copy import deepcopy

BASE_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')


def convert_prefix(s, old, new):
    """Replace prefix in a string: 'C-PWR-01' → 'B-PWR-01'"""
    if s and s.startswith(old + '-'):
        return new + s[len(old):]
    return s


def convert_framework_output():
    src = os.path.join(BASE_DIR, 'framework_output_v2_2.json')
    with open(src, encoding='utf-8') as f:
        data = json.load(f)

    data['version'] = '3.0'
    data['meta'] = {
        'note': 'v3.0 BFE移行。C→B, P削除(legacyPath保存), R→E。',
        'baseVersion': '2.2',
        'migrationScript': 'convert_v22_to_v30.py'
    }

    for fv in data['frameworkViews']:
        legacy_paths = []
        new_elements = []

        for el in fv['elements']:
            layer = el['layer']

            if layer == 'P':
                # Save P info as legacy, then skip
                legacy_paths.append({
                    'elementId': el['elementId'],
                    'category': el.get('category'),
                    'subCategory': el.get('subCategory'),
                    'label': el.get('label'),
                })
                continue

            if layer == 'C':
                el['layer'] = 'B'
                el['category'] = convert_prefix(el.get('category'), 'C', 'B')
                el['subCategory'] = convert_prefix(el.get('subCategory'), 'C', 'B')

            elif layer == 'R':
                el['layer'] = 'E'
                el['category'] = convert_prefix(el.get('category'), 'R', 'E')
                el['subCategory'] = convert_prefix(el.get('subCategory'), 'R', 'E')

            # F stays as-is
            new_elements.append(el)

        fv['elements'] = new_elements

        # Store legacy path info in notes
        if legacy_paths:
            if not fv.get('notes'):
                fv['notes'] = {}
            fv['notes']['legacyPath'] = legacy_paths

    dst = os.path.join(BASE_DIR, 'framework_output_v3_0_bfe.json')
    with open(dst, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    return data


def convert_taxonomy():
    src = os.path.join(BASE_DIR, 'taxonomy_v2_2.json')
    with open(src, encoding='utf-8') as f:
        data = json.load(f)

    data['version'] = '3.0'
    data['notes'] = [
        'v3.0 BFE移行: C→B, P削除, R→E。',
        'taxonomy.json はカテゴリ/サブカテゴリ表示名称の唯一の正本。',
    ]

    layers = data['layers']

    # C → B
    if 'C' in layers:
        b_layer = deepcopy(layers['C'])
        b_layer['displayName'] = 'Background'
        # Rename category keys and subCategory keys
        new_cats = {}
        for cat_key, cat_val in b_layer['categories'].items():
            new_key = convert_prefix(cat_key, 'C', 'B')
            new_val = deepcopy(cat_val)
            if 'subCategories' in new_val:
                new_subs = {}
                for sub_key, sub_name in new_val['subCategories'].items():
                    new_subs[convert_prefix(sub_key, 'C', 'B')] = sub_name
                new_val['subCategories'] = new_subs
            new_cats[new_key] = new_val
        b_layer['categories'] = new_cats
        layers['B'] = b_layer
        del layers['C']

    # R → E
    if 'R' in layers:
        e_layer = deepcopy(layers['R'])
        e_layer['displayName'] = 'Emancipation'
        new_cats = {}
        for cat_key, cat_val in e_layer['categories'].items():
            new_key = convert_prefix(cat_key, 'R', 'E')
            new_val = deepcopy(cat_val)
            if 'subCategories' in new_val:
                new_subs = {}
                for sub_key, sub_name in new_val['subCategories'].items():
                    new_subs[convert_prefix(sub_key, 'R', 'E')] = sub_name
                new_val['subCategories'] = new_subs
            new_cats[new_key] = new_val
        e_layer['categories'] = new_cats
        layers['E'] = e_layer
        del layers['R']

    # Delete P
    if 'P' in layers:
        del layers['P']

    # Reorder: B, F, E, L
    ordered = {}
    for key in ['B', 'F', 'E', 'L']:
        if key in layers:
            ordered[key] = layers[key]
    data['layers'] = ordered

    dst = os.path.join(BASE_DIR, 'taxonomy_v3_0_bfe.json')
    with open(dst, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    return data


def convert_inheritance_links():
    dst = os.path.join(BASE_DIR, 'inheritance_links_v3_0_bfe.json')
    data = {
        'version': '3.0',
        'inheritanceLinks': []
    }
    with open(dst, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return data


def convert_correspondences(fw_data):
    """Convert correspondences: remove P-layer element refs, keep others as-is.
    Element IDs (EL_EV_...) don't have layer prefixes, so we need to check
    which elements were P-layer by looking at the framework data."""
    src = os.path.join(BASE_DIR, 'default_correspondences.json')
    with open(src, encoding='utf-8') as f:
        corrs = json.load(f)

    # Build set of P-layer element IDs from original data
    src_fw = os.path.join(BASE_DIR, 'framework_output_v2_2.json')
    with open(src_fw, encoding='utf-8') as f:
        orig = json.load(f)

    p_element_ids = set()
    for fv in orig['frameworkViews']:
        for el in fv['elements']:
            if el['layer'] == 'P':
                p_element_ids.add(el['elementId'])

    # Filter out P-layer element correspondences
    new_corrs = {}
    removed = 0
    for fw_id, el_corrs in corrs.items():
        new_el_corrs = {}
        for el_id, corr in el_corrs.items():
            if el_id in p_element_ids:
                removed += 1
                continue
            new_el_corrs[el_id] = corr
        if new_el_corrs:
            new_corrs[fw_id] = new_el_corrs

    print(f'  Correspondences: removed {removed} P-layer refs')

    dst = os.path.join(BASE_DIR, 'default_correspondences_v3_0_bfe.json')
    with open(dst, 'w', encoding='utf-8') as f:
        json.dump(new_corrs, f, ensure_ascii=False, indent=2)

    return new_corrs


def validate(fw_data):
    """Validate the converted framework output."""
    events = fw_data['events']
    fws = fw_data['frameworkViews']
    errors = []

    # Event count
    if len(events) != 221:
        errors.append(f'Event count: {len(events)} (expected 221)')

    for fv in fws:
        layers = [el['layer'] for el in fv['elements']]

        # No P or R elements
        for l in layers:
            if l in ('P', 'R', 'C'):
                errors.append(f'{fv["frameworkViewId"]}: found layer {l}')

        # Exactly 1 F
        f_count = layers.count('F')
        if f_count != 1:
            errors.append(f'{fv["frameworkViewId"]}: F count = {f_count}')

        # Exactly 1 E
        e_count = layers.count('E')
        if e_count != 1:
            errors.append(f'{fv["frameworkViewId"]}: E count = {e_count}')

        # At least 1 B (warn only — some v2.2 events lack C elements)
        b_count = layers.count('B')
        if b_count < 1:
            print(f'  ⚠ Warning: {fv["frameworkViewId"]}: B count = 0 (no C in source)')

        # Check subCategory prefixes
        for el in fv['elements']:
            sc = el.get('subCategory', '')
            if sc:
                if el['layer'] == 'B' and not sc.startswith('B-'):
                    errors.append(f'{el["elementId"]}: B layer but subCat={sc}')
                elif el['layer'] == 'E' and not sc.startswith('E-'):
                    errors.append(f'{el["elementId"]}: E layer but subCat={sc}')
                elif el['layer'] == 'F' and not sc.startswith('F-'):
                    errors.append(f'{el["elementId"]}: F layer but subCat={sc}')

    if errors:
        print(f'\n❌ Validation FAILED ({len(errors)} errors):')
        for e in errors[:20]:
            print(f'  - {e}')
        return False
    else:
        # Summary
        layer_counts = {}
        for fv in fws:
            for el in fv['elements']:
                layer_counts[el['layer']] = layer_counts.get(el['layer'], 0) + 1
        print(f'\n✅ Validation PASSED')
        print(f'  Events: {len(events)}')
        print(f'  FWs: {len(fws)}')
        print(f'  Layer counts: {layer_counts}')
        return True


def main():
    print('=== v2.2 → v3.0 BFE Migration ===\n')

    print('1. Converting framework_output...')
    fw_data = convert_framework_output()

    print('2. Converting taxonomy...')
    convert_taxonomy()

    print('3. Converting inheritance_links...')
    convert_inheritance_links()

    print('4. Converting correspondences...')
    convert_correspondences(fw_data)

    print('\n5. Validating...')
    ok = validate(fw_data)

    if ok:
        print('\n🎉 Migration complete!')
    else:
        print('\n⚠️  Migration completed with errors.')
        sys.exit(1)


if __name__ == '__main__':
    main()
