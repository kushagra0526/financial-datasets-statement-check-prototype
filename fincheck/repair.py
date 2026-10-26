"""Name and undo a single extraction error by trying small repairs on the lines inside the violated identities."""
import copy

from .stmt import violations


def transposes(v):
    s = str(abs(v))
    out = set()
    for i in range(len(s) - 1):
        if s[i] != s[i + 1]:
            t = s[:i] + s[i + 1] + s[i] + s[i + 2:]
            if not t.startswith("0") or len(t) == 1:
                out.add(int(t) * (1 if v >= 0 else -1))
    return out


def candidates(data, line_period, line):
    v = data[line_period][line]
    c = []
    if v:
        c.append(("SCALE_x1000_too_big", v // 1000) if v % 1000 == 0 else None)
        c.append(("SCALE_x1000_too_small", v * 1000))
        c.append(("SIGN", -v))
    c += [("DIGIT_SWAP", t) for t in sorted(transposes(v))]
    d = data[line_period]
    c += [("DUPLICATE_ROW", d[k]) for k in d if k != line and isinstance(d[k], int) and d[k] != v]
    return [x for x in c if x]


def implied(data, viols, p, line):
    """Value of the line that satisfies the first violated identity it appears in (last resort)."""
    for name, r, sup in viols:
        if (p, line) in sup:
            return data[p][line] - r, data[p][line] + r
    return ()


def repair(data):
    """-> [] if all identities hold, else a list of (period, line, kind, new_value) that make every identity hold.
    Specific repairs (scale, sign, digit swap, duplicate) are preferred; 'IMPLIED' is used only if none works."""
    viols = violations(data)
    if not viols:
        return []
    lines = {pl for _, _, sup in viols for pl in sup}
    found, loose = [], []
    for p, line in sorted(lines):
        for kind, nv in candidates(data, p, line):
            t = copy.deepcopy(data)
            t[p][line] = nv
            if not violations(t):
                found.append((p, line, kind, nv))
        for nv in implied(data, viols, p, line):
            t = copy.deepcopy(data)
            t[p][line] = nv
            if not violations(t):
                loose.append((p, line, "IMPLIED", nv))
    return found or loose or ["UNRESOLVED"]
