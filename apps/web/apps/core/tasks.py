"""
Celery tasks for ScanNifty100
"""
from celery import shared_task
import logging
import sys
import importlib

logger = logging.getLogger(__name__)

@shared_task
def run_etl_pipeline():
    """Run the complete end-to-end ETL and ML scoring pipeline."""
    logger.info("Starting scheduled ETL pipeline...")
    
    try:
        # Import dynamically to avoid loading all ETL deps at startup
        extract_module = importlib.import_module("apps.etl.pipelines.01_extract_n100")
        clean_module = importlib.import_module("apps.etl.pipelines.02_clean_transform")
        load_module = importlib.import_module("apps.etl.pipelines.03_load_warehouse")
        
        logger.info("Running 01_extract_n100...")
        if hasattr(extract_module, 'main'):
            extract_module.main()
        
        logger.info("Running 02_clean_transform...")
        if hasattr(clean_module, 'main'):
            clean_module.main()
            
        logger.info("Running 03_load_warehouse...")
        if hasattr(load_module, 'main'):
            res = load_module.main()
            if res != 0:
                raise RuntimeError(f"03_load_warehouse failed with code {res}")
                
        logger.info("ETL pipeline completed successfully.")
        return "SUCCESS"
        
    except Exception as e:
        logger.error(f"ETL pipeline failed: {e}", exc_info=True)
        return f"FAILED: {e}"

