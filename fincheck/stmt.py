"""One company-year of statements (FY and Q1-Q4), consistent by construction, with accounting identities as checks and a single-line repair search.

All values are integers in millions. Periods: FY, Q1..Q4. Income statement and cash flow lines are flows (Q1+Q2+Q3+Q4 = FY).
The balance sheet exists for FY only. EPS and diluted shares are separate lines.
"""
import random

IS_IN = ["revenue", "cogs", "rd", "sga", "interest", "tax"]
IS_OUT = ["gross_profit", "operating_income", "pretax_income", "net_income"]
BS_ASSET = ["cash", "receivables", "inventory", "other_current_assets", "ppe", "other_assets"]
BS_LIAB = ["payables", "debt_current", "other_current_liab", "debt_noncurrent", "other_liab"]
CF_IN = ["cfo", "cfi", "cff"]
PERIODS = ["Q1", "Q2", "Q3", "Q4"]
LINES_IS = IS_IN + IS_OUT
LINES_CF = CF_IN + ["net_change"]
LINES_BS = BS_ASSET + ["total_assets"] + BS_LIAB + ["total_liabilities", "equity"]


def split(rng, total, n=4):
    w = [rng.uniform(0.5, 1.5) for _ in range(n)]
    parts = [int(total * x / sum(w)) for x in w]
    parts[-1] += total - sum(parts)
    return parts


def derive_is(d):
    d["gross_profit"] = d["revenue"] - d["cogs"]
    d["operating_income"] = d["gross_profit"] - d["rd"] - d["sga"]
    d["pretax_income"] = d["operating_income"] - d["interest"]
    d["net_income"] = d["pretax_income"] - d["tax"]


def make_company(seed):
    rng = random.Random(seed)
    R = rng.randint(800, 60000)
    fy = {"revenue": R, "cogs": int(R * rng.uniform(0.45, 0.8)), "rd": int(R * rng.uniform(0.02, 0.15)), "sga": int(R * rng.uniform(0.05, 0.2)),
          "interest": int(R * rng.uniform(0.0, 0.03))}
    fy["tax"] = max(0, int((fy["revenue"] - fy["cogs"] - fy["rd"] - fy["sga"] - fy["interest"]) * 0.21))
    derive_is(fy)
    shares = rng.randint(50, 3000)
    fy["shares"] = shares
    fy["eps_x100"] = round(fy["net_income"] * 100 / shares)
    cf = {"cfo": int(fy["net_income"] * rng.uniform(0.8, 1.6)), "cfi": -int(R * rng.uniform(0.02, 0.12)), "cff": -int(R * rng.uniform(0.0, 0.08))}
    cf["net_change"] = cf["cfo"] + cf["cfi"] + cf["cff"]
    bs = {"cash": rng.randint(max(50, abs(cf["net_change"]) + 50), max(200, int(R * 0.5)) + abs(cf["net_change"]))}
    for k in BS_ASSET[1:]:
        bs[k] = rng.randint(10, int(R * 0.6) + 20)
    bs["total_assets"] = sum(bs[k] for k in BS_ASSET)
    for k in BS_LIAB:
        bs[k] = rng.randint(5, int(R * 0.4) + 10)
    bs["total_liabilities"] = sum(bs[k] for k in BS_LIAB)
    bs["equity"] = bs["total_assets"] - bs["total_liabilities"]
    data = {"FY": {**fy, **cf, **bs, "begin_cash": bs["cash"] - cf["net_change"]}}
    qs = {k: split(rng, fy[k]) for k in IS_IN}
    qc = {k: split(rng, cf[k]) for k in CF_IN}
    for i, p in enumerate(PERIODS):
        d = {k: qs[k][i] for k in IS_IN}
        derive_is(d)
        d["shares"] = shares
        d["eps_x100"] = round(d["net_income"] * 100 / shares)
        for k in CF_IN:
            d[k] = qc[k][i]
        d["net_change"] = d["cfo"] + d["cfi"] + d["cff"]
        data[p] = d
    return data


def identities(data):
    """-> list of (name, residual, [(period, line) it involves])"""
    out = []
    for p in ["FY"] + PERIODS:
        d = data[p]
        out.append((f"{p} gross profit", d["gross_profit"] - (d["revenue"] - d["cogs"]), [(p, k) for k in ("gross_profit", "revenue", "cogs")]))
        out.append((f"{p} operating income", d["operating_income"] - (d["gross_profit"] - d["rd"] - d["sga"]), [(p, k) for k in ("operating_income", "gross_profit", "rd", "sga")]))
        out.append((f"{p} pretax", d["pretax_income"] - (d["operating_income"] - d["interest"]), [(p, k) for k in ("pretax_income", "operating_income", "interest")]))
        out.append((f"{p} net income", d["net_income"] - (d["pretax_income"] - d["tax"]), [(p, k) for k in ("net_income", "pretax_income", "tax")]))
        out.append((f"{p} cash flow", d["net_change"] - (d["cfo"] + d["cfi"] + d["cff"]), [(p, k) for k in ("net_change", "cfo", "cfi", "cff")]))
        out.append((f"{p} EPS", d["eps_x100"] * d["shares"] / 100 - d["net_income"] if abs(d["eps_x100"] * d["shares"] / 100 - d["net_income"]) > d["shares"] / 100 else 0, [(p, k) for k in ("eps_x100", "shares", "net_income")]))
    fy = data["FY"]
    out.append(("balance sheet total assets", fy["total_assets"] - sum(fy[k] for k in BS_ASSET), [("FY", k) for k in ["total_assets"] + BS_ASSET]))
    out.append(("balance sheet total liabilities", fy["total_liabilities"] - sum(fy[k] for k in BS_LIAB), [("FY", k) for k in ["total_liabilities"] + BS_LIAB]))
    out.append(("balance sheet balances", fy["total_assets"] - fy["total_liabilities"] - fy["equity"], [("FY", k) for k in ("total_assets", "total_liabilities", "equity")]))
    out.append(("cash ties to cash flow", fy["cash"] - fy["begin_cash"] - fy["net_change"], [("FY", k) for k in ("cash", "begin_cash", "net_change")]))
    for k in IS_IN + IS_OUT + CF_IN + ["net_change"]:
        out.append((f"quarters sum to FY {k}", data["FY"][k] - sum(data[p][k] for p in PERIODS), [("FY", k)] + [(p, k) for p in PERIODS]))
    return out


def violations(data):
    return [(n, r, s) for n, r, s in identities(data) if abs(r) > 0]
