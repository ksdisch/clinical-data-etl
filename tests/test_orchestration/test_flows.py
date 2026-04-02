"""Tests for Prefect flows."""

from unittest.mock import patch, MagicMock


class TestPipelineFlow:
    @patch("clinical_data_etl.orchestration.flows.validate_marts_task")
    @patch("clinical_data_etl.orchestration.flows.dbt_test_task")
    @patch("clinical_data_etl.orchestration.flows.dbt_run_task")
    @patch("clinical_data_etl.orchestration.flows.ingest_task")
    def test_full_pipeline_calls_all_tasks(
        self, mock_ingest, mock_dbt_run, mock_dbt_test, mock_validate
    ):
        from clinical_data_etl.orchestration.flows import pipeline_flow

        mock_ingest.return_value = {"beneficiary": {"loaded": 100, "rejected": 0}}
        mock_dbt_run.return_value = "PASS=9"
        mock_dbt_test.return_value = "PASS=28"
        mock_validate.return_value = {"fct_claims": 500, "dim_beneficiary": 100, "dim_provider": 50}

        result = pipeline_flow(run_ingestion=True, run_dbt=True)

        mock_ingest.assert_called_once()
        mock_dbt_run.assert_called_once()
        mock_dbt_test.assert_called_once()
        mock_validate.assert_called_once()
        assert "ingestion" in result
        assert "dbt_run" in result
        assert "mart_row_counts" in result

    @patch("clinical_data_etl.orchestration.flows.validate_marts_task")
    @patch("clinical_data_etl.orchestration.flows.dbt_test_task")
    @patch("clinical_data_etl.orchestration.flows.dbt_run_task")
    @patch("clinical_data_etl.orchestration.flows.ingest_task")
    def test_ingest_only_skips_dbt(
        self, mock_ingest, mock_dbt_run, mock_dbt_test, mock_validate
    ):
        from clinical_data_etl.orchestration.flows import pipeline_flow

        mock_ingest.return_value = {"beneficiary": {"loaded": 100, "rejected": 0}}
        mock_validate.return_value = {"fct_claims": 500, "dim_beneficiary": 100, "dim_provider": 50}

        result = pipeline_flow(run_ingestion=True, run_dbt=False)

        mock_ingest.assert_called_once()
        mock_dbt_run.assert_not_called()
        mock_dbt_test.assert_not_called()
        mock_validate.assert_called_once()
        assert "ingestion" in result
        assert "dbt_run" not in result

    @patch("clinical_data_etl.orchestration.flows.validate_marts_task")
    @patch("clinical_data_etl.orchestration.flows.dbt_test_task")
    @patch("clinical_data_etl.orchestration.flows.dbt_run_task")
    @patch("clinical_data_etl.orchestration.flows.ingest_task")
    def test_dbt_only_skips_ingestion(
        self, mock_ingest, mock_dbt_run, mock_dbt_test, mock_validate
    ):
        from clinical_data_etl.orchestration.flows import pipeline_flow

        mock_dbt_run.return_value = "PASS=9"
        mock_dbt_test.return_value = "PASS=28"
        mock_validate.return_value = {"fct_claims": 500, "dim_beneficiary": 100, "dim_provider": 50}

        result = pipeline_flow(run_ingestion=False, run_dbt=True)

        mock_ingest.assert_not_called()
        mock_dbt_run.assert_called_once()
        mock_dbt_test.assert_called_once()
        assert "ingestion" not in result
        assert "dbt_run" in result
