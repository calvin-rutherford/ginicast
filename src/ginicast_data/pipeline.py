import logging
from typing import Any

from ginicast_data.registry import registry
from ginicast_data.fetch import get_fetcher
from ginicast_data.standardize.schema import enforce_schema
from ginicast_data.standardize.normalize_dates import normalize_date_column
from ginicast_data.io.writers import write_raw_csv, write_standardized_csv, write_metadata_json

logger = logging.getLogger(__name__)

def process_metric(metric_config: dict[str, Any]):
    """Processes a single metric: fetches, standardizes, writes."""
    metric_id = metric_config.get("metric_id")
    source_name = metric_config.get("source")
    
    logger.info(f"Processing metric: {metric_id} from source: {source_name}")
    
    source_config = registry.get_source_config(source_name)
    if not source_config:
        logger.warning(f"No source config found for {source_name}. Skipping.")
        return
        
    if not source_config.get("enabled", True):
        logger.info(f"Source {source_name} is disabled. Skipping.")
        return
        
    try:
        fetcher = get_fetcher(source_name, source_config)
        
        # 1. Fetch Raw Data
        df, metadata = fetcher.fetch(metric_config)
        
        if df is None or df.empty:
            logger.warning(f"No data returned for {metric_id}. Skipping outputs.")
            write_metadata_json(metadata, source_name, metric_id)
            return
            
        # 2. Write Raw
        write_raw_csv(df, source_name, metric_id)
        
        # 3. Standardize
        df_std = normalize_date_column(df, date_col="date")
        df_std = enforce_schema(
            df=df_std,
            metric_id=metric_id,
            source=source_name,
            frequency=metric_config.get("expected_frequency", "unknown"),
            units=metric_config.get("units", "unknown")
        )
        
        # 4. Write Standardized & Metadata
        write_standardized_csv(df_std, metric_id)
        write_metadata_json(metadata, source_name, metric_id)
        
        logger.info(f"Successfully processed {metric_id} ({len(df_std)} rows).")

    except Exception as e:
        logger.error(f"Failed to process {metric_id}: {str(e)}", exc_info=True)


def run_pipeline(core_only: bool = False):
    """Runs the full or core fetching pipeline."""
    metrics = registry.get_core_metrics() if core_only else registry.get_all_metrics()
    
    if core_only:
        logger.info(f"Starting pipeline for Core 19 metrics. Total to process: {len(metrics)}")
    else:
        logger.info(f"Starting pipeline for all configured metrics. Total to process: {len(metrics)}")
        
    for idx, metric in enumerate(metrics):
        logger.info(f"--- Metric {idx+1}/{len(metrics)} ---")
        process_metric(metric)
        
    logger.info("Pipeline execution completed.")
