from __future__ import annotations

from app.career.analysis import analyzer_postprocess, run_deterministic_checks

WEAK_RESUME = "Responsible for managing a team. Helped with onboarding. " * 30

STRONG_RESUME = (
    "Experience\nSenior Engineer, Acme Corp\nJan 2020 - Present\n"
    + "- Reduced latency by 40% across the payments service\n" * 20
)


def test_flags_weak_verbs() -> None:
    findings = run_deterministic_checks(WEAK_RESUME)
    titles = {f["title"] for f in findings}
    assert "Weak, passive bullet openers found" in titles
    assert all(f["rule_based"] for f in findings)


def test_flags_missing_bullets() -> None:
    findings = run_deterministic_checks("Just a paragraph with no structure at all. " * 10)
    titles = {f["title"] for f in findings}
    assert "No bullet points detected" in titles


def test_flags_low_metric_density() -> None:
    text = "- Helped the team ship things\n" * 10
    findings = run_deterministic_checks(text)
    titles = {f["title"] for f in findings}
    assert "Most bullets have no quantified result" in titles


def test_does_not_flag_a_well_quantified_resume() -> None:
    findings = run_deterministic_checks(STRONG_RESUME)
    titles = {f["title"] for f in findings}
    assert "Most bullets have no quantified result" not in titles
    assert "Weak, passive bullet openers found" not in titles


def test_analyzer_postprocess_prepends_deterministic_findings() -> None:
    output = {"summary": "ok", "findings": [{"title": "AI finding", "severity": "info"}]}
    result = analyzer_postprocess(output, {"resume_text": WEAK_RESUME})
    assert result["findings"][-1] == {"title": "AI finding", "severity": "info"}
    assert result["findings"][0]["rule_based"] is True
