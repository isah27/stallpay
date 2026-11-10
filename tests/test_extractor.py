from stallpay.extractors.heuristic import HeuristicExtractor
from stallpay.samples import failure_samples, demo_samples
from stallpay.services import _matches_expected, evaluate_samples
from stallpay.checker import check_order


def test_five_demo_chats_extract_and_pass_checker():
    extractor = HeuristicExtractor()
    for sample in demo_samples():
        order = extractor.extract(sample["text"])
        assert _matches_expected(order, sample["expected"]), sample["id"]
        check = check_order(order)
        assert check.ok, (sample["id"], check.errors)


def test_failure_cases_are_blocked():
    extractor = HeuristicExtractor()
    for sample in failure_samples():
        order = extractor.extract(sample["text"])
        check = check_order(order)
        assert not check.ok, sample["id"]


def test_missing_price_has_no_usable_total_or_price():
    sample = next(s for s in failure_samples() if s["id"] == "missing_price")
    order = HeuristicExtractor().extract(sample["text"])
    check = check_order(order)
    assert not check.ok
    assert order.buyer_email.endswith("@example.com")


def test_total_mismatch_extracts_lines_but_checker_stops_paypal():
    sample = next(s for s in failure_samples() if s["id"] == "total_mismatch")
    order = HeuristicExtractor().extract(sample["text"])
    assert len(order.items) == 1
    assert order.stated_total_ngn != order.items[0].line_total_ngn
    assert not check_order(order).ok


def test_prompt_injection_does_not_skip_the_checker():
    sample = next(s for s in failure_samples() if s["id"] == "prompt_injection")
    order = HeuristicExtractor().extract(sample["text"])
    check = check_order(order)
    assert not check.ok
    assert any("greater than zero" in err or "stated total" in err.lower() for err in check.errors)
    assert any("instruction-like" in w.lower() for w in check.warnings)


def test_published_metrics_match_the_sample_set():
    metrics = evaluate_samples()
    assert metrics["success_extracted_and_checked"] == 5
    assert metrics["success_samples"] == 5
    assert metrics["failure_blocked_by_checker"] == 3
    assert metrics["failure_samples"] == 3
