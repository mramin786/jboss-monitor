# reports/generator.py
import os
import csv
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from config import Config

def generate_pdf_report(report_id, environment, host_status):
    """
    Generate a PDF report for the given host status
    
    :param report_id: Unique identifier for the report
    :param environment: Production or non-production environment
    :param host_status: List of hosts with their status
    """
    # Use absolute path
    report_path = os.path.join(Config.REPORTS_PATH, f"{report_id}.pdf")
    
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
        
        table_data.append([
            host['host'],
            str(host['port']),
            host['instance'],
            host['status'].get('instance_status', 'Unknown').upper(),
            last_check,
            f"{sum(1 for ds in datasource_status if ds.get('status') == 'up')}/{len(datasource_status)}",
            f"{sum(1 for dep in deployment_status if dep.get('status') == 'up')}/{len(deployment_status)}"
        ])
    
    # Create table
    table = Table(table_data, repeatRows=1)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.grey),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,0), 12),
        ('BOTTOMPADDING', (0,0), (-1,0), 12),
        ('BACKGROUND', (0,1), (-1,-1), colors.beige),
        ('GRID', (0,0), (-1,-1), 1, colors.black)
    ]))
    
    content.append(table)
    content.append(Spacer(1, 12))
    
    # Add details for each host
    content.append(Paragraph("Detailed Status", heading_style))
    content.append(Spacer(1, 6))
    
    for host in host_status:
        content.append(Paragraph(f"Host: {host['host']}:{host['port']} ({host['instance']})", styles['Heading3']))
        
        # Status summary
        status_text = f"Status: {host['status'].get('instance_status', 'Unknown').upper()}"
        if host['status'].get('last_check'):
            try:
                check_date = datetime.fromisoformat(host['status'].get('last_check'))
                status_text += f" (Last Check: {check_date.strftime('%Y-%m-%d %H:%M:%S')})"
            except (ValueError, TypeError):
                status_text += f" (Last Check: {host['status'].get('last_check')})"
        
        content.append(Paragraph(status_text, normal_style))
        
        # Datasources
        datasources = host['status'].get('datasources', [])
        if datasources:
            content.append(Paragraph("Datasources:", styles['Heading4']))
            ds_data = [['Name', 'Type', 'Status']]
            for ds in datasources:
                ds_data.append([
                    ds.get('name', 'Unknown'),
                    ds.get('type', 'Unknown'),
                    ds.get('status', 'Unknown').upper()
                ])
            
            ds_table = Table(ds_data, repeatRows=1)
            ds_table.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
                ('TEXTCOLOR', (0,0), (-1,0), colors.black),
                ('ALIGN', (0,0), (-1,-1), 'LEFT'),
                ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                ('FONTSIZE', (0,0), (-1,0), 10),
                ('BOTTOMPADDING', (0,0), (-1,0), 8),
                ('GRID', (0,0), (-1,-1), 1, colors.black)
            ]))
            content.append(ds_table)
        else:
            content.append(Paragraph("Datasources: None found", normal_style))
        
        # Deployments
        deployments = host['status'].get('deployments', [])
        if deployments:
            content.append(Paragraph("Deployments:", styles['Heading4']))
            dep_data = [['Name', 'Status']]
            for dep in deployments:
                dep_data.append([
                    dep.get('name', 'Unknown'),
                    dep.get('status', 'Unknown').upper()
                ])
            
            dep_table = Table(dep_data, repeatRows=1)
            dep_table.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
                ('TEXTCOLOR', (0,0), (-1,0), colors.black),
                ('ALIGN', (0,0), (-1,-1), 'LEFT'),
                ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                ('FONTSIZE', (0,0), (-1,0), 10),
                ('BOTTOMPADDING', (0,0), (-1,0), 8),
                ('GRID', (0,0), (-1,-1), 1, colors.black)
            ]))
            content.append(dep_table)
        else:
            content.append(Paragraph("Deployments: None found", normal_style))
        
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

def generate_csv_report(report_id, environment, host_status):
    """
    Generate a CSV report for the given host status
    
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

