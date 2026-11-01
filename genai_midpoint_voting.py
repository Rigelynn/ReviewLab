"""Recalculate midpoint-threshold votes from saved GenAI reviews; no model calls.

Example:
  python3 genai_midpoint_voting.py --data-dir PATH/TO/data/nsfc_panel_v3 --capacity 3

The strict midpoint rule is S/M < 0.5, with M=12 and S=15-sum(ratings).
This is S<6 (T>50), not the archived routine's inclusive T>=50 rule.
"""
import argparse
import hashlib
import json
import random
from pathlib import Path


def calculate(data_dir, capacity):
    names = ['results.json', 'researcher_values.json', 'materials.json']
    inputs = {name: json.loads((data_dir / name).read_text()) for name in names}
    hashes = {name: hashlib.sha256((data_dir / name).read_bytes()).hexdigest() for name in names}
    ids = [item['id'] for item in inputs['materials.json']['projects']]
    experts = [item['id'] for item in inputs['materials.json']['experts']]
    if not 1 <= capacity <= len(ids):
        raise ValueError('Capacity must be between one and the project-pool size')
    votes = {project: 0 for project in ids}
    seen = set()
    for record in inputs['results.json']['records']:
        if record['task'] != 'rubric' or record['status'] != 'actual':
            continue
        pair = record['expert_id'], record['project_id']
        if pair in seen:
            raise ValueError('Duplicate reviewer-project pair')
        seen.add(pair)
        scores = record['parsed']['scores']
        if len(scores) != 3 or any(item['score'] not in range(1, 6) for item in scores):
            raise ValueError('Expected three complete integer ratings from one to five')
        reverse_score = 15 - sum(item['score'] for item in scores)
        votes[record['project_id']] += int(reverse_score < 6)
    if seen != {(expert, project) for expert in experts for project in ids}:
        raise ValueError('Incomplete reviewer-project matrix')
    lottery = ids.copy()
    random.Random(1028).shuffle(lottery)
    tie = {project: pos for pos, project in enumerate(lottery)}
    order = sorted(ids, key=lambda project: (-votes[project], tie[project]))
    # Reference values are used only after the voting order has been determined.
    values = {item['project_id']: item['q'] for item in inputs['researcher_values.json']['projects']}
    selected = order[:capacity]
    oracle = sorted(ids, key=lambda project: (-values[project], tie[project]))[:capacity]
    selected_value = sum(values[project] for project in selected)
    oracle_value = sum(values[project] for project in oracle)
    assert hashes == {name: hashlib.sha256((data_dir / name).read_bytes()).hexdigest() for name in names}
    return {
        'analysis': 'midpoint_voting_recalculation_from_saved_reviews',
        'rule': 'S/M < 0.5; M=12; S<6; equivalently T>50',
        'new_model_calls': 0, 'input_sha256': hashes,
        'tie_seed': 1028, 'tie_order': lottery,
        'votes': votes, 'order': order, 'capacity': capacity,
        'selected': selected, 'value': round(selected_value, 6),
        'loss': round(oracle_value-selected_value, 6),
        'oracle_value': round(oracle_value, 6),
        'top_m_recovery': len(set(selected) & set(oracle))/capacity,
    }


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data-dir', type=Path, required=True)
    parser.add_argument('--capacity', type=int, default=3)
    args = parser.parse_args()
    print(json.dumps(calculate(args.data_dir, args.capacity), ensure_ascii=False, indent=2))
