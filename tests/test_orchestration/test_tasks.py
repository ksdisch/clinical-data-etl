"""Tests for Prefect tasks."""

from unittest.mock import MagicMock, patch

import pytest


class TestIngestTask:
    @patch("clinical_data_etl.ingestion.loaders.run_ingestion")
    def test_calls_run_ingestion(self, mock_run):
        from clinical_data_etl.orchestration.tasks import ingest_task

        mock_run.return_value = {
            "beneficiary": {"loaded": 100, "rejected": 0},
            "providers": {"loaded": 50, "rejected": 0},
        }
        result = ingest_task.fn()
        mock_run.assert_called_once()
        assert result["beneficiary"]["loaded"] == 100


class TestDbtRunTask:
    @patch("clinical_data_etl.orchestration.tasks._run_dbt_command")
    def test_calls_dbt_run(self, mock_dbt):
        from clinical_data_etl.orchestration.tasks import dbt_run_task

        mock_dbt.return_value = "Done. PASS=9"
        result = dbt_run_task.fn()
        mock_dbt.assert_called_once_with(["run"])
        assert "PASS" in result

    @patch("clinical_data_etl.orchestration.tasks._run_dbt_command")
    def test_raises_on_failure(self, mock_dbt):
        from clinical_data_etl.orchestration.tasks import dbt_run_task

        mock_dbt.side_effect = RuntimeError("dbt run failed")
        with pytest.raises(RuntimeError, match="dbt run failed"):
            dbt_run_task.fn()


class TestDbtSeedTask:
    @patch("clinical_data_etl.orchestration.tasks._run_dbt_command")
    def test_calls_dbt_seed(self, mock_dbt):
        from clinical_data_etl.orchestration.tasks import dbt_seed_task

        mock_dbt.return_value = "Done. PASS=1"
        result = dbt_seed_task.fn()
        mock_dbt.assert_called_once_with(["seed"])
        assert "PASS" in result


class TestDbtTestTask:
    @patch("clinical_data_etl.orchestration.tasks._run_dbt_command")
    def test_calls_dbt_test(self, mock_dbt):
        from clinical_data_etl.orchestration.tasks import dbt_test_task

        mock_dbt.return_value = "Done. PASS=28"
        result = dbt_test_task.fn()
        mock_dbt.assert_called_once_with(["test"])
        assert "PASS" in result

    @patch("clinical_data_etl.orchestration.tasks._run_dbt_command")
    def test_raises_on_failure(self, mock_dbt):
        from clinical_data_etl.orchestration.tasks import dbt_test_task

        mock_dbt.side_effect = RuntimeError("dbt test failed")
        with pytest.raises(RuntimeError, match="dbt test failed"):
            dbt_test_task.fn()


class TestValidateMartsTask:
    @patch("clinical_data_etl.orchestration.tasks.get_engine")
    def test_returns_row_counts(self, mock_get_engine):
        from clinical_data_etl.orchestration.tasks import validate_marts_task

        mock_conn = MagicMock()
        mock_engine = MagicMock()
        mock_engine.connect.return_value.__enter__ = MagicMock(return_value=mock_conn)
        mock_engine.connect.return_value.__exit__ = MagicMock(return_value=False)
        mock_conn.execute.return_value.scalar.return_value = 1000
        mock_get_engine.return_value = mock_engine

        result = validate_marts_task.fn()
        assert result["fct_claims"] == 1000
        assert result["dim_beneficiary"] == 1000
        assert result["dim_provider"] == 1000

    @patch("clinical_data_etl.orchestration.tasks.get_engine")
    def test_raises_on_empty_table(self, mock_get_engine):
        from clinical_data_etl.orchestration.tasks import validate_marts_task

        mock_conn = MagicMock()
        mock_engine = MagicMock()
        mock_engine.connect.return_value.__enter__ = MagicMock(return_value=mock_conn)
        mock_engine.connect.return_value.__exit__ = MagicMock(return_value=False)
        mock_conn.execute.return_value.scalar.return_value = 0
        mock_get_engine.return_value = mock_engine

        with pytest.raises(RuntimeError, match="empty"):
            validate_marts_task.fn()
