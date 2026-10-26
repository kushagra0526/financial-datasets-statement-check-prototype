import copy
import json
import random
from collections import Counter

from . import repair, stmt

DEV_KINDS = ["SCALE", "SIGN", "DIGIT_SWAP", "DUPLICATE_ROW", "VALUE_TYPO"]
HELD_KINDS = DEV_KINDS + ["TAG_SWAP", "SHARES_UNIT"]
NUMERIC = stmt.LINES_IS + stmt.LINES_CF
FY_ONLY = stmt.LINES_BS


def corrupt(data, kind, rng):
    d = copy.deepcopy(data)
    if kind == "SHARES_UNIT":
        p = rng.choice(["FY"] + stmt.PERIODS)
        d[p]["shares"] *= 1000
        return d, (p, "shares")
    if kind == "TAG_SWAP":
        p = rng.choice(["FY"] + stmt.PERIODS)
        a, b = rng.sample(["cogs", "rd", "sga"], 2)
        if d[p][a] == d[p][b]:
            return None, None
        d[p][a], d[p][b] = d[p][b], d[p][a]
        return d, (p, a)
    p = rng.choice(["FY"] + stmt.PERIODS)
    lines = [l for l in (NUMERIC + (FY_ONLY + ["begin_cash"] if p == "FY" else [])) if d[p][l] not in (0,)]
    line = rng.choice(lines)
    v = d[p][line]
    if kind == "SCALE":
        d[p][line] = v * 1000
    elif kind == "SIGN":
        d[p][line] = -v
    elif kind == "DIGIT_SWAP":
        ts = repair.transposes(v)
        if not ts:
            return None, None
        d[p][line] = rng.choice(sorted(ts))
    elif kind == "DUPLICATE_ROW":
        others = [d[p][k] for k in d[p] if k != line and isinstance(d[p][k], int) and d[p][k] != v]
        d[p][line] = rng.choice(others)
    elif kind == "VALUE_TYPO":
        s = list(str(abs(v)))
        i = rng.randrange(len(s))
        s[i] = str((int(s[i]) + rng.randint(1, 9)) % 10)
        nv = int("".join(s))
        if nv == abs(v):
            return None, None
        d[p][line] = nv * (1 if v >= 0 else -1)
    return d, (p, line)


def schema_check(d):
    """Baseline: every value present and an integer; revenue and total assets positive."""
    return all(isinstance(v, int) for p in d.values() for v in p.values()) and d["FY"]["revenue"] > 0 and d["FY"]["total_assets"] > 0


def score(seeds, held):
    kinds = HELD_KINDS if held else DEV_KINDS
    t, per = Counter(), {}
    for s in seeds:
        rng = random.Random(s)
        clean = stmt.make_company(s)
        kind = rng.choice(kinds + [None] * 2)
        if kind:
            bad, where = corrupt(clean, kind, rng)
            if bad is None:
                continue
        else:
            bad, where = clean, None
        r = repair.repair(bad)
        flagged = bool(r)
        key = kind or "clean"
        p = per.setdefault(key, Counter())
        p["n"] += 1
        p["flagged"] += flagged
        p["baseline_flagged"] += not schema_check(bad)
        if kind:
            ok = [x for x in r if x != "UNRESOLVED" and x[0] == where[0] and x[1] == where[1] and x[3] == clean[where[0]][where[1]]]
            p["repaired_correct_value"] += bool(ok)
            p["unique_and_correct"] += len(r) == 1 and bool(ok)
            p["unresolved"] += r == ["UNRESOLVED"]
    return {k: dict(v) for k, v in sorted(per.items())}


def main():
    res = {"dev": score(range(0, 700), False), "held_out": score(range(10000, 10700), True)}
    json.dump(res, open("out/result.json", "w"), indent=1)
    for k, v in res.items():
        print(k)
        for d, c in v.items():
            print("  ", d, c)


if __name__ == "__main__":
    main()
