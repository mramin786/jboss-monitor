# reports/generator.py
import os
import csv
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet

def generate_pdf_report(report_id, environment, host_status):
    """
    Generate a PDF report for the given host status
    
    :param report_id: Unique identifier for the report
    :param environment: Production or non-production environment
    :param host_status: List of hosts with their status
    """
    # Create reports directory if it doesn't exist
    os.makedirs(os.path.dirname(f'storage/reports/{report_id}.pdf'), exist_ok=True)
    
    # Create PDF file path
    pdf_path = f'storage/reports/{report_id}.pdf'
    
    # Create PDF document
    doc = SimpleDocTemplate(pdf_path, pagesize=letter)
    
    # Styles
    styles = getSampleStyleSheet()
    title_style = styles['Title']
    heading_style = styles['Heading2']
    
    # Content components
    content = []
    
    # Title
    content.append(Paragraph(f"{environment.capitalize()} JBoss Monitor Report", title_style))
    content.append(Paragraph(f"Report ID: {report_id}", styles['Normal']))
    content.append(Paragraph(f"Generated on: {os.path.getctime(pdf_path)}", styles['Normal']))
    
    # Prepare table data
    table_data = [
        ['Host', 'Port', 'Instance', 'Status', 'Last Check', 'Datasources', 'Deployments']
    ]
    
    for host in host_status:
        datasource_status = host['status'].get('datasources', [])
        deployment_status = host['status'].get('deployments', [])
        
        table_data.append([
            host['host'],
            str(host['port']),
            host['instance'],
            host['status'].get('instance_status', 'Unknown').upper(),
            host['status'].get('last_check', 'Never'),
            f"{sum(1 for ds in datasource_status if ds['status'] == 'up')}/{len(datasource_status)}",
            f"{sum(1 for dep in deployment_status if dep['status'] == 'up')}/{len(deployment_status)}"
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
    
    # Build PDF
    doc.build(content)
    
    return pdf_path

def generate_csv_report(report_id, environment, host_status):
    """
    Generate a CSV report for the given host status
    
    :param report_id: Unique identifier for the report
    :param environment: Production or non-production environment
    :param host_status: List of hosts with their status
    """
    # Create reports directory if it doesn't exist
    os.makedirs(os.path.dirname(f'storage/reports/{report_id}.csv'), exist_ok=True)
    
    # Create CSV file path
    csv_path = f'storage/reports/{report_id}.csv'
    
    # Write CSV file
    with open(csv_path, 'w', newline='') as csvfile:
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
            
            writer.writerow([
                environment.capitalize(),
                host['host'],
                host['port'],
                host['instance'],
                host['status'].get('instance_status', 'Unknown').upper(),
                host['status'].get('last_check', 'Never'),
                f"{sum(1 for ds in datasource_status if ds['status'] == 'up')}/{len(datasource_status)}",
                f"{sum(1 for dep in deployment_status if dep['status'] == 'up')}/{len(deployment_status)}"
            ])
    
    return csv_path
