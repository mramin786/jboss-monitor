# reports/utils.py
import os
import json
import logging
from datetime import datetime
from config import Config

logger = logging.getLogger(__name__)

def rotate_reports(environment=None, max_reports=None):
    """
    Rotate reports to keep only the most recent ones (per environment if specified)
    
    Args:
        environment (str, optional): If provided, only rotate reports for this environment
        max_reports (int, optional): Maximum number of reports to keep per environment
    
    Returns:
        int: Number of reports deleted
    """
    # Use Config.MAX_REPORTS_PER_ENV if max_reports is not provided
    if max_reports is None:
        max_reports = Config.MAX_REPORTS_PER_ENV
        
    reports_index_file = os.path.join(Config.REPORTS_PATH, 'reports_index.json')
    
    if not os.path.exists(reports_index_file):
        logger.warning(f"Reports index file not found at {reports_index_file}")
        return 0
    
    try:
        # Load reports index
        with open(reports_index_file, 'r') as f:
            reports = json.load(f)
        
        if not reports:
            return 0
            
        # Group reports by environment if environment is None
        if environment is None:
            # Process all environments
            environments = set(report.get('environment') for report in reports if 'environment' in report)
            total_deleted = 0
            
            for env in environments:
                env_deleted = rotate_reports(env, max_reports)
                total_deleted += env_deleted
                
            return total_deleted
        
        # Filter reports for the specified environment
        env_reports = [r for r in reports if r.get('environment') == environment]
        
        # Sort by creation date (newest first)
        env_reports.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        
        if len(env_reports) <= max_reports:
            # No rotation needed
            return 0
        
        # Get reports to delete
        reports_to_delete = env_reports[max_reports:]
        deleted_count = 0
        
        for report in reports_to_delete:
            report_id = report.get('id')
            report_format = report.get('format')
            
            if not report_id or not report_format:
                continue
                
            # Delete report file
            report_file = os.path.join(Config.REPORTS_PATH, f"{report_id}.{report_format}")
            if os.path.exists(report_file):
                try:
                    os.remove(report_file)
                    deleted_count += 1
                    logger.info(f"Deleted old report file: {report_file}")
                except Exception as e:
                    logger.error(f"Error deleting report file {report_file}: {str(e)}")
            
            # Remove from index
            reports.remove(report)
        
        # Save updated index
        with open(reports_index_file, 'w') as f:
            json.dump(reports, f, indent=2)
            
        logger.info(f"Rotated reports for {environment}: kept {max_reports}, deleted {deleted_count}")
        return deleted_count
        
    except Exception as e:
        logger.error(f"Error rotating reports: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return 0

def get_reports_file_path(report_id, format):
    """
    Get the full path to a report file
    
    Args:
        report_id (str): The report ID
        format (str): The report format (pdf, csv)
    
    Returns:
        str: Full path to the report file
    """
    return os.path.join(Config.REPORTS_PATH, f"{report_id}.{format}")
