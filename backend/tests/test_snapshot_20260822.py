from app.seed.snapshot_20260822 import normalized_spares, validate_snapshot


def test_snapshot_has_three_full_lines_and_no_overlap():
    result = validate_snapshot()
    assert result.running_count == 30
    assert result.duplicate_running_codes == ()
    assert result.running_spare_overlap == ()


def test_ready_wins_over_pending_duplicates():
    spares = normalized_spares()
    assert spares["8A"] == "READY"
    assert spares["9A"] == "READY"
    assert spares["10A"] == "READY"


def test_running_wins_over_spare_lists():
    spares = normalized_spares()
    assert "5D" not in spares
    assert "10C" not in spares


def test_report_is_missing_four_asset_codes():
    result = validate_snapshot()
    assert result.known_total == 50
    assert result.unidentified_count == 4
