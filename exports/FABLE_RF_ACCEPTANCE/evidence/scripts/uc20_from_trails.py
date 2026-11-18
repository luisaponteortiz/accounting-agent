"""Post-hoc reading of the kept trails of fable_rf_step_search.py (read-only on the results).

The search script's own "early" flag fires only when the row that has not arrived is itself a locked row.
In its twelve families the row that arrives late is P, a December row that claims locked A1, and P's own
claim is only known once P is delivered. So that flag is 0 by construction there. This script counts the
UC-20 situation directly from the trail of every order:

  waiting  - a December row is approved at a step although it, or a row it reaches through delivered claims
             (a person's selection overrides the claims of that claimant), claims a target that is not on file.
  direct   - the approved row's OWN claim is the one whose target is not on file (clause 4 says such a row
             is blocked, so any count here would be a failure).
  survived - the approval is still governing at the step at which the missing target arrives.

usage: uc20_from_trails.py <dir with *.results.json> <prefix>
"""
import glob, json, sys
from collections import Counter, defaultdict

SELECT = {'SELB', 'SELP'}
PRE = {'retained-claim+older-conflict': ('B',), 'retained-claim+newer-conflict': ('B',), 'conflict+selection-without-lock': ('B',), 'retained-conflict+confirming-selection': ('B',)}
fam = defaultdict(Counter); examples = {}
for f in sorted(glob.glob(sys.argv[1].rstrip('/') + '/' + sys.argv[2] + '*.results.json')):
    for r in json.load(open(f))['results']:
        c = fam[r['family']]; c['orders'] += 1
        on_file = {'A1'} | set(PRE.get(r['family'], ()))
        waiting_since = {}   # (approved key, missing target) -> step index
        flags = set()
        for i, t in enumerate(r['trail']):
            s = t['step']
            if s not in SELECT and s[0] in 'PBQZ':
                on_file.add(s[0])
            edges = defaultdict(list)
            for d in t['declared']:
                a, b = d.split('>'); edges[a].append(b)
            for a, b in (t['selected'] or {}).items():
                edges[a] = [b]
            c['steps'] += 1
            for k in t['december_approved']:
                stack = [(k, 0)]; seen = set()
                while stack:
                    key, depth = stack.pop()
                    if key in seen:
                        continue
                    seen.add(key)
                    for tgt in edges.get(key, []):
                        if tgt not in on_file:
                            flags.add('direct' if depth == 0 else 'waiting')
                            c['steps_direct' if depth == 0 else 'steps_waiting'] += 1
                            waiting_since.setdefault((k, tgt), i)
                            examples.setdefault((r['family'], 'direct' if depth == 0 else 'waiting'), (r['order'], s, k, tgt))
                        stack.append((tgt, depth + 1))
            for (k, tgt), since in list(waiting_since.items()):
                if tgt in on_file:
                    if k in t['december_approved']:
                        flags.add('survived'); examples.setdefault((r['family'], 'survived'), (r['order'], s, k, tgt))
                    else:
                        flags.add('stopped_on_arrival')
                        if k in t['held']:
                            flags.add('held_on_arrival')
                    del waiting_since[(k, tgt)]
        for x in flags:
            c['orders_' + x] += 1
        if waiting_since:
            c['orders_target_never_arrived'] += 1
tot = Counter()
print('%-42s %6s %8s %8s %8s %10s %8s' % ('family', 'orders', 'waiting', 'direct', 'survived', 'stopped', 'held'))
for name, c in fam.items():
    tot.update(c)
    print('%-42s %6d %8d %8d %8d %10d %8d' % (name, c['orders'], c['orders_waiting'], c['orders_direct'], c['orders_survived'], c['orders_stopped_on_arrival'], c['orders_held_on_arrival']))
print('%-42s %6d %8d %8d %8d %10d %8d' % ('TOTAL', tot['orders'], tot['orders_waiting'], tot['orders_direct'], tot['orders_survived'], tot['orders_stopped_on_arrival'], tot['orders_held_on_arrival']))
print('steps read: %d | steps with a waiting approval: %d | with a direct one: %d | orders whose missing target never arrived: %d' % (tot['steps'], tot['steps_waiting'], tot['steps_direct'], tot['orders_target_never_arrived']))
print('columns: waiting = orders with an approval given or standing while an ancestor claim waits for its target (UC-20); direct = the approved row is itself the waiting claimant;')
print('         survived = approval still governing at the step the target arrived; stopped = approval not governing at that step; held = and the row is held under the locked period at that step')
for k, v in sorted(examples.items()):
    print('example', k, v)
print(json.dumps({'UC20_JSON': {n: {k: int(v) for k, v in c.items()} for n, c in fam.items()}}))
