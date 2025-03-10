# reports/comparison.py
import os
import json
import logging
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, ListFlowable, ListItem
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from config import Config

logger = logging.getLogger(__name__)

def compare_reports(report1_id, report2_id):
    """
    Compare two reports and return the differences
    
    Args:
        report1_id (str): ID of the first report (older)
        report2_id (str): ID of the second report (newer)
    
    Returns:
        dict: Comparison results
    """
    try:
        # Load reports data
        reports_dir = Config.REPORTS_PATH
        reports_index_file = os.path.join(reports_dir, 'reports_index.json')
        
        if not os.path.exists(reports_index_file):
            return {"error": "Reports index not found"}
        
        with open(reports_index_file, 'r') as f:
            reports_index = json.load(f)
        
        # Find report entries in the index
        report1 = next((r for r in reports_index if r['id'] == report1_id), None)
        report2 = next((r for r in reports_index if r['id'] == report2_id), None)
        
        if not report1 or not report2:
            return {"error": "One or both reports not found"}
        
        # Ensure both reports are completed
        if report1['status'] != 'completed' or report2['status'] != 'completed':
            return {"error": "One or both reports are not completed"}
            
        # Extract data from report files
        report1_data = extract_data_from_pdf(report1_id)
        report2_data = extract_data_from_pdf(report2_id)
        
        # Compare the data
        comparison_result = {
            "report1": {
                "id": report1_id,
                "created_at": report1.get('created_at'),
                "environment": report1.get('environment')
            },
            "report2": {
                "id": report2_id,
                "created_at": report2.get('created_at'),
                "environment": report2.get('environment')
            },
            "hosts": compare_hosts(report1_data, report2_data),
            "summary": {
                "total_hosts": len(report1_data),
                "status_changes": 0,
                "datasource_changes": 0,
                "deployment_changes": 0
            }
        }
        
        # Update summary with counts
        for host_comparison in comparison_result["hosts"]:
            if host_comparison.get("status_changed"):
                comparison_result["summary"]["status_changes"] += 1
            
            comparison_result["summary"]["datasource_changes"] += len(host_comparison.get("datasource_changes", []))
            comparison_result["summary"]["deployment_changes"] += len(host_comparison.get("deployment_changes", []))
        
        return comparison_result
        
    except Exception as e:
        logger.error(f"Error comparing reports: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return {"error": str(e)}

def extract_data_from_pdf(report_id):
    """
    Extract structured data from a report PDF for comparison purposes.
    Falls back to generated dummy data if no valid data file exists.
    """
    # Look for a data file
    reports_dir = Config.REPORTS_PATH
    data_file = os.path.join(reports_dir, f"{report_id}.json")
    
    if os.path.exists(data_file):
        try:
            with open(data_file, 'r') as f:
                content = f.read().strip()
                if content:  # Check if file is not empty
                    return json.loads(content)
                else:
                    logger.warning(f"Data file for report {report_id} is empty")
        except Exception as e:
            logger.error(f"Error reading data file for report {report_id}: {str(e)}")
    else:
        logger.warning(f"No data file found for report {report_id}")
    
    # Generate dummy data for comparison if no valid data found
    # This provides a structure mimicking real data for older reports
    # or reports with missing/invalid data files
    
    # First, look up the report in the index to get its environment
    env = "unknown"
    try:
        reports_index_file = os.path.join(reports_dir, 'reports_index.json')
        if os.path.exists(reports_index_file):
            with open(reports_index_file, 'r') as f:
                reports = json.load(f)
                for r in reports:
                    if r.get('id') == report_id:
                        env = r.get('environment', 'unknown')
                        break
    except Exception as e:
        logger.error(f"Error loading reports index: {str(e)}")
    
    # Generate placeholder data
    logger.warning(f"Generating placeholder data for report {report_id} in environment {env}")
    return [
        {
            "host": "placeholder-host",
            "port": 9990,
            "instance": "placeholder-instance",
            "id": "placeholder-id",
            "added_by": "system",
            "added_at": datetime.now().isoformat(),
            "status": {
                "instance_status": "unknown",
                "datasources": [],
                "deployments": [],
                "last_check": datetime.now().isoformat()
            }
        }
    ]

def compare_hosts(hosts1, hosts2):
    """
    Compare two sets of host data and identify differences
    
    Args:
        hosts1 (list): Host data from the first report
        hosts2 (list): Host data from the second report
    
    Returns:
        list: Comparison results for each host
    """
    comparison_results = []
    
    # Create dictionaries for quick lookups
    hosts1_dict = {h['host'] + ':' + str(h['port']): h for h in hosts1 if 'host' in h and 'port' in h}
    hosts2_dict = {h['host'] + ':' + str(h['port']): h for h in hosts2 if 'host' in h and 'port' in h}
    
    # Find all unique hosts across both reports
    all_hosts = set(hosts1_dict.keys()) | set(hosts2_dict.keys())
    
    for host_key in all_hosts:
        host1 = hosts1_dict.get(host_key)
        host2 = hosts2_dict.get(host_key)
        
        # Handle cases where a host exists in only one report
        if not host1:
            comparison_results.append({
                "host": host2['host'],
                "port": host2['port'],
                "status": "added",
                "instance": host2.get('instance', 'unknown'),
                "instance_status": host2.get('status', {}).get('instance_status', 'unknown'),
                "old_instance_status": None,
                "status_changed": True,
                "datasource_changes": [],
                "deployment_changes": []
            })
            continue
            
        if not host2:
            comparison_results.append({
                "host": host1['host'],
                "port": host1['port'],
                "status": "removed",
                "instance": host1.get('instance', 'unknown'),
                "instance_status": None,
                "old_instance_status": host1.get('status', {}).get('instance_status', 'unknown'),
                "status_changed": True,
                "datasource_changes": [],
                "deployment_changes": []
            })
            continue
        
        # Now we know both hosts exist, so we can compare them
        host_result = {
            "host": host1['host'],
            "port": host1['port'],
            "instance": host1.get('instance', 'unknown'),
            "status": "changed" if host1.get('status', {}).get('instance_status') != host2.get('status', {}).get('instance_status') else "unchanged",
            "status_changed": host1.get('status', {}).get('instance_status') != host2.get('status', {}).get('instance_status'),
            "instance_status": host2.get('status', {}).get('instance_status', 'unknown'),
            "old_instance_status": host1.get('status', {}).get('instance_status', 'unknown'),
            "datasource_changes": [],
            "deployment_changes": []
        }
        
        # Compare datasources
        ds1 = {ds['name']: ds for ds in host1.get('status', {}).get('datasources', []) if 'name' in ds}
        ds2 = {ds['name']: ds for ds in host2.get('status', {}).get('datasources', []) if 'name' in ds}
        
        # Find all unique datasources
        all_datasources = set(ds1.keys()) | set(ds2.keys())
        
        for ds_name in all_datasources:
            datasource1 = ds1.get(ds_name)
            datasource2 = ds2.get(ds_name)
            
            if not datasource1:
                host_result["datasource_changes"].append({
                    "name": ds_name,
                    "type": datasource2.get('type', 'unknown'),
                    "change": "added",
                    "status": datasource2.get('status', 'unknown'),
                    "old_status": None
                })
            elif not datasource2:
                host_result["datasource_changes"].append({
                    "name": ds_name,
                    "type": datasource1.get('type', 'unknown'),
                    "change": "removed",
                    "status": None,
                    "old_status": datasource1.get('status', 'unknown')
                })
            elif datasource1.get('status') != datasource2.get('status'):
                host_result["datasource_changes"].append({
                    "name": ds_name,
                    "type": datasource2.get('type', 'unknown'),
                    "change": "status_changed",
                    "status": datasource2.get('status', 'unknown'),
                    "old_status": datasource1.get('status', 'unknown')
                })
        
        # Compare deployments
        dep1 = {dep['name']: dep for dep in host1.get('status', {}).get('deployments', []) if 'name' in dep}
        dep2 = {dep['name']: dep for dep in host2.get('status', {}).get('deployments', []) if 'name' in dep}
        
        # Find all unique deployments
        all_deployments = set(dep1.keys()) | set(dep2.keys())
        
        for dep_name in all_deployments:
            deployment1 = dep1.get(dep_name)
            deployment2 = dep2.get(dep_name)
            
            if not deployment1:
                host_result["deployment_changes"].append({
                    "name": dep_name,
                    "change": "added",
                    "status": deployment2.get('status', 'unknown'),
                    "old_status": None
                })
            elif not deployment2:
                host_result["deployment_changes"].append({
                    "name": dep_name,
                    "change": "removed",
                    "status": None,
                    "old_status": deployment1.get('status', 'unknown')
                })
            elif deployment1.get('status') != deployment2.get('status'):
                host_result["deployment_changes"].append({
                    "name": dep_name,
                    "change": "status_changed",
                    "status": deployment2.get('status', 'unknown'),
                    "old_status": deployment1.get('status', 'unknown')
                })
        
        comparison_results.append(host_result)
    
    return comparison_results

def generate_comparison_pdf(comparison_id, comparison_data):
    """
    Generate a PDF report showing the comparison results
    
    Args:
        comparison_id (str): Unique identifier for the comparison
        comparison_data (dict): Comparison results
    
    Returns:
        str: Path to the generated PDF file
    """
    # Create PDF document
    report_path = os.path.join(Config.REPORTS_PATH, f"{comparison_id}.pdf")
    doc = SimpleDocTemplate(report_path, pagesize=letter)
    
    # Styles
    styles = getSampleStyleSheet()
    title_style = styles['Title']
    heading_style = styles['Heading2']
    heading3_style = styles['Heading3']
    normal_style = styles['Normal']
    
    # Create custom styles
    center_style = ParagraphStyle(
        'CenterStyle',
        parent=styles['Normal'],
        alignment=TA_CENTER
    )
    
    up_style = ParagraphStyle(
        'UpStatus',
        parent=styles['Normal'],
        textColor=colors.green,
        fontName='Helvetica-Bold'
    )
    
    down_style = ParagraphStyle(
        'DownStatus',
        parent=styles['Normal'],
        textColor=colors.red,
        fontName='Helvetica-Bold'
    )
    
    unknown_style = ParagraphStyle(
        'UnknownStatus',
        parent=styles['Normal'],
        textColor=colors.gray,
        fontName='Helvetica-Bold'
    )
    
    # Build document content
    content = []
    
    # Add title and summary
    report1_date = format_date(comparison_data['report1']['created_at'])
    report2_date = format_date(comparison_data['report2']['created_at'])
    environment = comparison_data['report1']['environment'].replace('_', ' ').capitalize()
    
    content.append(Paragraph(f"{environment} JBoss Status Comparison", title_style))
    content.append(Spacer(1, 12))
    
    content.append(Paragraph(f"Comparing reports from {report1_date} and {report2_date}", center_style))
    content.append(Spacer(1, 12))
    
    # Summary table
    summary = comparison_data['summary']
    summary_data = [
        ['Total Hosts', str(summary['total_hosts'])],
        ['Hosts with Status Changes', str(summary['status_changes'])],
        ['Datasource Changes', str(summary['datasource_changes'])],
        ['Deployment Changes', str(summary['deployment_changes'])],
    ]
    
    summary_table = Table(summary_data, colWidths=[200, 100])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.black),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('ALIGN', (1, 0), (1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('BOX', (0, 0), (-1, -1), 1, colors.black),
    ]))
    content.append(summary_table)
    content.append(Spacer(1, 20))
    
    # Add host comparison details
    content.append(Paragraph("Host Status Changes", heading_style))
    content.append(Spacer(1, 10))
    
    hosts_with_changes = [h for h in comparison_data['hosts'] if 
        h['status_changed'] or h['datasource_changes'] or h['deployment_changes']]
    
    if not hosts_with_changes:
        content.append(Paragraph("No changes detected between the two reports.", normal_style))
    else:
        for host in hosts_with_changes:
            # Host header
            content.append(Paragraph(f"{host['host']}:{host['port']} ({host['instance']})", heading3_style))
            
            # Host status change
            if host['status_changed']:
                old_status_text = get_status_text(host['old_instance_status'])
                new_status_text = get_status_text(host['instance_status'])
                
                status_data = [
                    ['Host Status', old_status_text, new_status_text]
                ]
                
                status_table = Table(status_data, colWidths=[150, 150, 150])
                status_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ('BOX', (0, 0), (-1, -1), 1, colors.black),
                    ('BACKGROUND', (1, 0), (1, -1), get_status_color(host['old_instance_status'], 0.2)),
                    ('BACKGROUND', (2, 0), (2, -1), get_status_color(host['instance_status'], 0.2)),
                ]))
                content.append(status_table)
                content.append(Spacer(1, 10))
            
            # Datasource changes
            if host['datasource_changes']:
                content.append(Paragraph("Datasource Changes:", normal_style))
                ds_data = [['Datasource', 'Type', 'Change', 'Old Status', 'New Status']]
                
                for ds in host['datasource_changes']:
                    ds_data.append([
                        ds['name'],
                        ds['type'],
                        ds['change'].replace('_', ' ').capitalize(),
                        get_status_text(ds['old_status']) if ds['old_status'] else 'N/A',
                        get_status_text(ds['status']) if ds['status'] else 'N/A',
                    ])
                
                ds_table = Table(ds_data, colWidths=[120, 80, 80, 80, 80])
                ds_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ('BOX', (0, 0), (-1, -1), 1, colors.black),
                ]))
                
                # Add colors for status cells
                for i, row in enumerate(ds_data[1:], 1):
                    old_status = row[3]
                    new_status = row[4]
                    
                    if old_status != 'N/A':
                        ds_table.setStyle(TableStyle([
                            ('BACKGROUND', (3, i), (3, i), get_status_color(old_status.lower(), 0.2)),
                        ]))
                    
                    if new_status != 'N/A':
                        ds_table.setStyle(TableStyle([
                            ('BACKGROUND', (4, i), (4, i), get_status_color(new_status.lower(), 0.2)),
                        ]))
                
                content.append(ds_table)
                content.append(Spacer(1, 10))
            
            # Deployment changes
            if host['deployment_changes']:
                content.append(Paragraph("Deployment Changes:", normal_style))
                dep_data = [['Deployment', 'Change', 'Old Status', 'New Status']]
                
                for dep in host['deployment_changes']:
                    dep_data.append([
                        dep['name'],
                        dep['change'].replace('_', ' ').capitalize(),
                        get_status_text(dep['old_status']) if dep['old_status'] else 'N/A',
                        get_status_text(dep['status']) if dep['status'] else 'N/A',
                    ])
                
                dep_table = Table(dep_data, colWidths=[200, 80, 80, 80])
                dep_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ('BOX', (0, 0), (-1, -1), 1, colors.black),
                ]))
                
                # Add colors for status cells
                for i, row in enumerate(dep_data[1:], 1):
                    old_status = row[2]
                    new_status = row[3]
                    
                    if old_status != 'N/A':
                        dep_table.setStyle(TableStyle([
                            ('BACKGROUND', (2, i), (2, i), get_status_color(old_status.lower(), 0.2)),
                        ]))
                    
                    if new_status != 'N/A':
                        dep_table.setStyle(TableStyle([
                            ('BACKGROUND', (3, i), (3, i), get_status_color(new_status.lower(), 0.2)),
                        ]))
                
                content.append(dep_table)
            
            content.append(Spacer(1, 20))
    
    # Add legend
    content.append(Paragraph("Status Legend:", heading3_style))
    
    legend_data = [
        ["UP", "Server/component is running and available"],
        ["DOWN", "Server/component is not running or not available"],
        ["UNKNOWN", "Status could not be determined"]
    ]
    
    legend_table = Table(legend_data, colWidths=[100, 300])
    legend_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, 0), colors.lightgreen),
        ('BACKGROUND', (0, 1), (0, 1), colors.lightpink),
        ('BACKGROUND', (0, 2), (0, 2), colors.lightgrey),
        ('ALIGN', (0, 0), (0, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    content.append(legend_table)
    
    # Add footer
    content.append(Spacer(1, 30))
    content.append(Paragraph(f"Comparison generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", 
                            styles['Italic']))
    
    # Build PDF
    try:
        doc.build(content)
        return report_path
    except Exception as e:
        logger.error(f"Error building comparison PDF: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        raise

def format_date(date_string):
    """Format a date string for display"""
    try:
        dt = datetime.fromisoformat(date_string)
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except Exception as e:
        logger.error(f"Error formatting date {date_string}: {e}")
        return date_string or "Unknown"

def get_status_text(status):
    """Convert status to display text"""
    if not status:
        return "UNKNOWN"
    
    return status.upper()

def get_status_color(status, alpha=1.0):
    """Get color for a status"""
    if not status:
        return colors.lightgrey
    
    status = status.lower()
    if status == 'up':
        return colors.lightgreen
    elif status == 'down':
        return colors.lightpink
    else:
        return colors.lightgrey
