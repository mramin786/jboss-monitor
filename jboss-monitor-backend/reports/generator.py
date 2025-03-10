# reports/generator.py
import os
import csv
import logging
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from config import Config
# Configure logging
logger = logging.getLogger(__name__)

def generate_pdf_report(report_id, environment, host_status):
    """
    Generate a PDF report for the given host status with enhanced color coding
    
    :param report_id: Unique identifier for the report
    :param environment: Production or non-production environment
    :param host_status: List of hosts with their status
    """
    # Use absolute path
    report_path = os.path.join(Config.REPORTS_PATH, f"{report_id}.pdf")
    data_path = os.path.join(Config.REPORTS_PATH, f"{report_id}.json")
    # Store the raw data in JSON format for easy comparison
    try:
        with open(data_path, 'w') as f:
            json.dump(host_status, f, indent=2)
        logger.info(f"Saved report data to {data_path} for future comparisons")
    except Exception as e:
        logger.error(f"Error saving report data: {str(e)}") 
    # Create reports directory if it doesn't exist
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    
    print(f"Generating PDF report at: {report_path}")
    
    # Create PDF document
    doc = SimpleDocTemplate(report_path, pagesize=letter)
    # Create reports directory if it doesn't exist
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    
    print(f"Generating PDF report at: {report_path}")
    
    # Create PDF document
    doc = SimpleDocTemplate(report_path, pagesize=letter)
    
    # Styles
    styles = getSampleStyleSheet()
    title_style = styles['Title']
    heading_style = styles['Heading2']
    normal_style = styles['Normal']
    
    # Create custom styles for status
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
    
    center_style = ParagraphStyle(
        'CenterStyle',
        parent=styles['Normal'],
        alignment=TA_CENTER
    )
    
    # Content components
    content = []
    
    # Title
    content.append(Paragraph(f"{environment.capitalize()} JBoss Monitor Report", title_style))
    content.append(Paragraph(f"Report ID: {report_id}", normal_style))
    content.append(Paragraph(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", normal_style))
    content.append(Spacer(1, 12))
    
    # Prepare table data
    table_data = [
        ['Host', 'Port', 'Instance', 'Status', 'Last Check', 'Datasources', 'Deployments']
    ]
    
    for host in host_status:
        datasource_status = host['status'].get('datasources', [])
        deployment_status = host['status'].get('deployments', [])
        
        last_check = host['status'].get('last_check', 'Never')
        # Format datetime if it exists
        if last_check and last_check != 'Never':
            try:
                # Try to parse ISO format date
                check_date = datetime.fromisoformat(last_check)
                last_check = check_date.strftime('%Y-%m-%d %H:%M:%S')
            except (ValueError, TypeError):
                # Keep as is if parsing fails
                pass
        
        # Create styled status text based on status
        status = host['status'].get('instance_status', 'unknown').upper()
        if status == 'UP':
            status_text = Paragraph(status, up_style)
        elif status == 'DOWN':
            status_text = Paragraph(status, down_style)
        else:
            status_text = Paragraph(status, unknown_style)
        
        # Create datasource and deployment counts with color coding
        ds_up = sum(1 for ds in datasource_status if ds.get('status') == 'up')
        ds_total = len(datasource_status)
        ds_text = f"{ds_up}/{ds_total}"
        
        dep_up = sum(1 for dep in deployment_status if dep.get('status') == 'up')
        dep_total = len(deployment_status)
        dep_text = f"{dep_up}/{dep_total}"
        
        # Add row to table
        table_data.append([
            host['host'],
            str(host['port']),
            host['instance'],
            status_text,
            last_check,
            ds_text,
            dep_text
        ])
    
    # Create table with enhanced styling
    table = Table(table_data, repeatRows=1)
    table.setStyle(TableStyle([
        # Header styling
        ('BACKGROUND', (0,0), (-1,0), colors.darkblue),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('ALIGN', (0,0), (-1,0), 'CENTER'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,0), 12),
        ('BOTTOMPADDING', (0,0), (-1,0), 12),
        
        # Row styling - alternate colors
        ('BACKGROUND', (0,1), (-1,-1), colors.lightgrey),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.lightgrey]),
        
        # Grid
        ('GRID', (0,0), (-1,-1), 1, colors.black),
        
        # Alignment for specific columns
        ('ALIGN', (3,1), (3,-1), 'CENTER'),  # Status column centered
        ('ALIGN', (5,1), (6,-1), 'CENTER'),  # Datasources and Deployments centered
    ]))
    
    content.append(table)
    content.append(Spacer(1, 12))
    
    # Add details for each host
    content.append(Paragraph("Detailed Status", heading_style))
    content.append(Spacer(1, 6))
    
    for host in host_status:
        # Host header with background color based on status
        host_status_value = host['status'].get('instance_status', 'unknown').lower()
        if host_status_value == 'up':
            bg_color = colors.lightgreen
            status_style = up_style
        elif host_status_value == 'down':
            bg_color = colors.lightpink
            status_style = down_style
        else:
            bg_color = colors.lightgrey
            status_style = unknown_style
            
        # Create a mini table for the host header with background color
        host_header = Table(
            [[Paragraph(f"Host: {host['host']}:{host['port']} ({host['instance']})", styles['Heading3']),
              Paragraph(host_status_value.upper(), status_style)]],
            colWidths=['80%', '20%']
        )
        host_header.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), bg_color),
            ('BOX', (0, 0), (-1, -1), 1, colors.black),
            ('PADDING', (0, 0), (-1, -1), 6),
            ('ALIGN', (1, 0), (1, 0), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        content.append(host_header)
        content.append(Spacer(1, 5))
        
        # Status summary
        status_text = f"Last Check: {formatLastCheck(host['status'].get('last_check'))}"
        content.append(Paragraph(status_text, normal_style))
        content.append(Spacer(1, 10))
        
        # Datasources
        datasources = host['status'].get('datasources', [])
        if datasources:
            content.append(Paragraph("Datasources:", styles['Heading4']))
            ds_data = [['Name', 'Type', 'Status']]
            for ds in datasources:
                # Apply color to status
                ds_status = ds.get('status', 'unknown').upper()
                if ds_status == 'UP':
                    status_cell = Paragraph(ds_status, up_style)
                else:
                    status_cell = Paragraph(ds_status, down_style)
                    
                ds_data.append([
                    ds.get('name', 'Unknown'),
                    ds.get('type', 'Unknown'),
                    status_cell
                ])
            
            ds_table = Table(ds_data, repeatRows=1)
            ds_table.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.darkblue),
                ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
                ('ALIGN', (0,0), (-1,-1), 'LEFT'),
                ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                ('FONTSIZE', (0,0), (-1,0), 10),
                ('BOTTOMPADDING', (0,0), (-1,0), 8),
                ('GRID', (0,0), (-1,-1), 1, colors.black),
                ('ALIGN', (2,1), (2,-1), 'CENTER'),  # Status column centered
                ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.lightgrey])
            ]))
            content.append(ds_table)
        else:
            content.append(Paragraph("Datasources: None found", normal_style))
        
        content.append(Spacer(1, 10))
        
        # Deployments
        deployments = host['status'].get('deployments', [])
        if deployments:
            content.append(Paragraph("Deployments:", styles['Heading4']))
            dep_data = [['Name', 'Status']]
            for dep in deployments:
                # Apply color to status
                dep_status = dep.get('status', 'unknown').upper()
                if dep_status == 'UP':
                    status_cell = Paragraph(dep_status, up_style)
                else:
                    status_cell = Paragraph(dep_status, down_style)
                    
                dep_data.append([
                    dep.get('name', 'Unknown'),
                    status_cell
                ])
            
            dep_table = Table(dep_data, repeatRows=1)
            dep_table.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.darkblue),
                ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
                ('ALIGN', (0,0), (-1,-1), 'LEFT'),
                ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                ('FONTSIZE', (0,0), (-1,0), 10),
                ('BOTTOMPADDING', (0,0), (-1,0), 8),
                ('GRID', (0,0), (-1,-1), 1, colors.black),
                ('ALIGN', (1,1), (1,-1), 'CENTER'),  # Status column centered
                ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.lightgrey])
            ]))
            content.append(dep_table)
        else:
            content.append(Paragraph("Deployments: None found", normal_style))
        
        content.append(Spacer(1, 20))
    
    # Legend for status colors
    legend_data = [
        [Paragraph('Status Legend:', styles['Heading4'])]
    ]
    legend_table = Table(legend_data)
    content.append(legend_table)
    content.append(Spacer(1, 5))
    
    # Create status legend
    status_legend = Table([
        [Paragraph('UP', up_style), 'Server/component is running and available'],
        [Paragraph('DOWN', down_style), 'Server/component is not running or not available'],
        [Paragraph('UNKNOWN', unknown_style), 'Status could not be determined']
    ])
    status_legend.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 1, colors.black),
        ('BACKGROUND', (0,0), (0,-1), colors.lightgrey),
        ('PADDING', (0,0), (-1,-1), 6),
    ]))
    content.append(status_legend)
    content.append(Spacer(1, 12))
    
    # Add footer with timestamp
    content.append(Paragraph(f"Report generated by JBoss Monitor on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", 
                            styles['Italic']))
    
    # Build PDF
    try:
        doc.build(content)
        print(f"PDF generated successfully at {report_path}")
    except Exception as e:
        import traceback
        print(f"Error building PDF: {str(e)}")
        print(traceback.format_exc())
        raise
    
    return report_path

def formatLastCheck(lastCheck):
    """Format the last check timestamp"""
    if not lastCheck:
        return 'Never'
    
    try:
        # Try to parse ISO format date
        check_date = datetime.fromisoformat(lastCheck)
        return check_date.strftime('%Y-%m-%d %H:%M:%S')
    except (ValueError, TypeError):
        # Keep as is if parsing fails
        return lastCheck

def generate_csv_report(report_id, environment, host_status):
    """
    Generate a CSV report for the given host status
    
    Note: This is kept for backward compatibility but no longer exposed in the UI
    
    :param report_id: Unique identifier for the report
    :param environment: Production or non-production environment
    :param host_status: List of hosts with their status
    """
    # Use absolute path
    report_path = os.path.join(Config.REPORTS_PATH, f"{report_id}.csv")
    
    # Create reports directory if it doesn't exist
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    
    print(f"Generating CSV report at: {report_path}")
    
    # Write CSV file
    try:
        with open(report_path, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            
            # Write header
            writer.writerow([
                'Environment', 
                'Host', 
                'Port', 
                'Instance', 
                'Status', 
                'Last Check', 
                'Datasources (UP/Total)', 
                'Deployments (UP/Total)'
            ])
            
            # Write data rows
            for host in host_status:
                datasource_status = host['status'].get('datasources', [])
                deployment_status = host['status'].get('deployments', [])
                
                last_check = host['status'].get('last_check', 'Never')
                # Format datetime if it exists
                if last_check and last_check != 'Never':
                    try:
                        # Try to parse ISO format date
                        check_date = datetime.fromisoformat(last_check)
                        last_check = check_date.strftime('%Y-%m-%d %H:%M:%S')
                    except (ValueError, TypeError):
                        # Keep as is if parsing fails
                        pass
                
                writer.writerow([
                    environment.capitalize(),
                    host['host'],
                    host['port'],
                    host['instance'],
                    host['status'].get('instance_status', 'Unknown').upper(),
                    last_check,
                    f"{sum(1 for ds in datasource_status if ds.get('status') == 'up')}/{len(datasource_status)}",
                    f"{sum(1 for dep in deployment_status if dep.get('status') == 'up')}/{len(deployment_status)}"
                ])
        
        print(f"CSV generated successfully at {report_path}")
    except Exception as e:
        import traceback
        print(f"Error writing CSV: {str(e)}")
        print(traceback.format_exc())
        raise
    
    return report_path
