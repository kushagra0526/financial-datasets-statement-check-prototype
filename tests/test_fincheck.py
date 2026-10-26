import copy

from fincheck import repair, stmt


def test_generated_statements_satisfy_every_identity():
    for s in range(30):
        assert stmt.violations(stmt.make_company(s)) == []


def test_scale_error_is_named_and_undone():
    d = stmt.make_company(1)
    truth = d["Q2"]["sga"]
    d["Q2"]["sga"] = truth * 1000
    r = repair.repair(d)
    assert r and r[0][:3] == ("Q2", "sga", "SCALE_x1000_too_big") and r[0][3] == truth


def test_sign_error_on_the_balance_sheet_is_found_and_undone():
    d = stmt.make_company(2)
    truth = d["FY"]["inventory"]
    d["FY"]["inventory"] = -truth
    assert any(x[:3] == ("FY", "inventory", "SIGN") and x[3] == truth for x in repair.repair(d))


def test_swapped_tags_are_detected_but_not_silently_repaired_as_one_line():
    d = stmt.make_company(3)
    d["FY"]["cogs"], d["FY"]["rd"] = d["FY"]["rd"], d["FY"]["cogs"]
    assert stmt.violations(d)
    assert repair.repair(d) == ["UNRESOLVED"]
