# Updated parsing logic for monitor_host function

def parse_datasources(ds_data):
    """Parse datasources from JBoss CLI response"""
    datasources = []
    
    # Handle data-source
    if isinstance(ds_data, dict) and 'data-source' in ds_data:
        # In your JBoss version, data-source is a dictionary with datasource names as keys
        for ds_name, ds_details in ds_data['data-source'].items():
            enabled = ds_details.get('enabled', False)
            datasources.append({
                'name': ds_name,
                'type': 'data-source',
                'status': 'up' if enabled else 'down'
            })
    
    # Handle xa-data-source if present
    if isinstance(ds_data, dict) and 'xa-data-source' in ds_data and ds_data['xa-data-source']:
        if isinstance(ds_data['xa-data-source'], dict):
            for ds_name, ds_details in ds_data['xa-data-source'].items():
                enabled = ds_details.get('enabled', False)
                datasources.append({
                    'name': ds_name,
                    'type': 'xa-data-source',
                    'status': 'up' if enabled else 'down'
                })
    
    return datasources
