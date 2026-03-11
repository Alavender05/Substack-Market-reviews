from src.status_rules import classify_discovery_result, classify_final_run, classify_preflight_result


def test_classify_preflight_result_degraded():
    status, stage = classify_preflight_result({"core_status": "degraded", "failure_stage": "preflight_dns"})
    assert status == "degraded"
    assert stage == "preflight_dns"


def test_classify_discovery_result_degraded_when_all_fail():
    status, stage = classify_discovery_result(0, 2)
    assert status == "degraded"
    assert stage == "discovery"


def test_classify_final_run_prioritizes_failure():
    assert classify_final_run(internal_error=True, degraded=True) == "failed"
    assert classify_final_run(internal_error=False, degraded=True) == "degraded"
    assert classify_final_run(internal_error=False, degraded=False) == "healthy"
