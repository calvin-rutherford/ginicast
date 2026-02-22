import pandas as pd
import logging
from pathlib import Path

from ginicast_data.io.paths import AUDIT_DIR
from ginicast_data.io.readers import list_standardized_files

logger = logging.getLogger(__name__)

def infer_frequency(df: pd.DataFrame) -> str:
    """Simple heuristic to infer frequency from daily spacing."""
    if len(df) < 2: return "unknown"
    df["date"] = pd.to_datetime(df["date"])
    diffs = df["date"].diff().dropna().dt.days
    median_diff = diffs.median()
    
    if median_diff <= 1: return "daily"
    elif median_diff <= 7: return "weekly"
    elif 28 <= median_diff <= 31: return "monthly"
    elif 85 <= median_diff <= 95: return "quarterly"
    elif 360 <= median_diff <= 370: return "annual"
    return "unknown"

def generate_audit_report():
    """Reads all standardized files and computes a metric coverage report."""
    logger.info("Generating metadata audit report...")
    files = list_standardized_files()
    
    if not files:
        logger.warning("No standardized CSV files found. Cannot generate audit.")
        return
        
    records = []
    
    for pf in files:
        try:
            df = pd.read_csv(pf)
            metric_id = df["metric"].iloc[0] if not df.empty and "metric" in df.columns else pf.stem
            source = df["source"].iloc[0] if not df.empty and "source" in df.columns else "unknown"
            
            row_count = len(df)
            missing_count = int(df["value"].isna().sum())
            
            if row_count > 0:
                df["date_parse"] = pd.to_datetime(df["date"], errors="coerce")
                start_date = df["date_parse"].min().strftime("%Y-%m-%d")
                end_date = df["date_parse"].max().strftime("%Y-%m-%d")
                inf_freq = infer_frequency(df)
            else:
                start_date = "N/A"
                end_date = "N/A"
                inf_freq = "N/A"
                
            records.append({
                "metric_id": metric_id,
                "source": source,
                "start_date": start_date,
                "end_date": end_date,
                "row_count": row_count,
                "missing_values": missing_count,
                "inferred_freq": inf_freq,
                "coverage_pct": round(100 - (missing_count/row_count*100), 2) if row_count > 0 else 0
            })
            
        except Exception as e:
            logger.error(f"Error auditing file {pf.name}: {e}")
            
    if not records:
        logger.info("No records to summarize.")
        return
        
    summary_df = pd.DataFrame(records).sort_values("metric_id")
    
    csv_path = AUDIT_DIR / "summary.csv"
    summary_df.to_csv(csv_path, index=False)
    
    md_path = AUDIT_DIR / "summary.md"
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("# GiniCast Phase 1 Data Audit Summary\n\n")
        f.write(summary_df.to_markdown(index=False))
        
    logger.info(f"Audit report saved to {csv_path} and {md_path}")
