from unittest.mock import MagicMock, patch

from src.logging.query_logger import log_query


def _make_connection_mock():
    cursor = MagicMock()
    cursor.__enter__.return_value = cursor
    cursor.__exit__.return_value = False

    connection = MagicMock()
    connection.cursor.return_value = cursor
    return connection, cursor


@patch("src.logging.query_logger.psycopg2.connect")
@patch("src.logging.query_logger.get_settings")
def test_log_query_marks_high_confidence_as_not_low(mock_get_settings, mock_connect):
    mock_get_settings.return_value = MagicMock(database_url="postgresql://example")
    connection, cursor = _make_connection_mock()
    mock_connect.return_value = connection

    log_query(
        query_text="what is wrong with my maize",
        route_taken="tier1",
        cache_hit=False,
        diagnosis_results=[{"id": "GLS", "confidence": 0.92}],
        chunk_results=[{"metadata": {"chunk_id": "chunk-1"}, "confidence": 0.61}],
        weather_used=False,
        soil_used=True,
        latency_ms=123,
    )

    assert cursor.execute.call_args.args[1][-1] is False


@patch("src.logging.query_logger.psycopg2.connect")
@patch("src.logging.query_logger.get_settings")
def test_log_query_marks_low_confidence_when_all_scores_are_low(
    mock_get_settings,
    mock_connect,
):
    mock_get_settings.return_value = MagicMock(database_url="postgresql://example")
    connection, cursor = _make_connection_mock()
    mock_connect.return_value = connection

    log_query(
        query_text="what is wrong with my maize",
        route_taken="tier2",
        cache_hit=True,
        diagnosis_results=[{"id": "NLB", "confidence": 0.41}],
        chunk_results=[{"metadata": {"chunk_id": "chunk-2"}, "confidence": 0.49}],
        weather_used=True,
        soil_used=False,
        latency_ms=87,
    )

    assert cursor.execute.call_args.args[1][-1] is True


@patch("src.logging.query_logger.psycopg2.connect")
@patch("src.logging.query_logger.get_settings")
def test_log_query_marks_empty_results_as_low_confidence(
    mock_get_settings,
    mock_connect,
):
    mock_get_settings.return_value = MagicMock(database_url="postgresql://example")
    connection, cursor = _make_connection_mock()
    mock_connect.return_value = connection

    log_query(
        query_text="what is wrong with my maize",
        route_taken="none",
        cache_hit=False,
        diagnosis_results=[],
        chunk_results=[],
        weather_used=False,
        soil_used=False,
        latency_ms=12,
    )

    assert cursor.execute.call_args.args[1][-1] is True