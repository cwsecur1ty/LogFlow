import os
import json
import uuid
from datetime import datetime

class LogBuilder:
    """Simple utility for creating and managing sample log data."""
    
    def __init__(self, logs_dir='sample_logs'):
        self.logs_dir = logs_dir
        
        # Create logs directory if it doesn't exist
        if not os.path.exists(logs_dir):
            os.makedirs(logs_dir)
    
    def create_log(self, log_type, log_data):
        """Create a new sample log file.
        
        Args:
            log_type: Type of log (dns, password, etc.)
            log_data: JSON-compatible dict of log data
            
        Returns:
            str: ID of the created log
        """
        # Generate a unique ID
        log_id = str(uuid.uuid4())[:8]
        
        # Format log data with standard structure
        formatted_log = {
            "logs": {
                "log": log_data if isinstance(log_data, list) else [log_data]
            },
            "meta": {
                "id": log_id,
                "type": log_type,
                "created": datetime.now().isoformat()
            }
        }
        
        # Save to file
        filename = f"{log_type}_{log_id}.json"
        filepath = os.path.join(self.logs_dir, filename)
        
        with open(filepath, 'w') as f:
            json.dump(formatted_log, f, indent=2)
        
        return log_id
    
    def get_log(self, log_id):
        """Get a log by ID.
        
        Args:
            log_id: Log ID to retrieve
            
        Returns:
            tuple: (log_data, filename) or (None, None) if not found
        """
        # Scan directory for matching ID
        for filename in os.listdir(self.logs_dir):
            if not filename.endswith('.json'):
                continue
                
            filepath = os.path.join(self.logs_dir, filename)
            
            try:
                with open(filepath, 'r') as f:
                    log_data = json.load(f)
                
                if log_data.get('meta', {}).get('id') == log_id:
                    return log_data, filename
            except:
                # Skip files with errors
                continue
        
        return None, None
    
    def update_log(self, log_id, log_data):
        """Update an existing log.
        
        Args:
            log_id: Log ID to update
            log_data: New log data (list of log entries)
            
        Returns:
            bool: Success or failure
        """
        # Get the existing log
        existing_log, filename = self.get_log(log_id)
        if not existing_log or not filename:
            return False
        
        # Update only the log entries, preserve metadata
        existing_log['logs']['log'] = log_data
        
        # Save back to file
        filepath = os.path.join(self.logs_dir, filename)
        with open(filepath, 'w') as f:
            json.dump(existing_log, f, indent=2)
        
        return True
    
    def delete_log(self, log_id):
        """Delete a log.
        
        Args:
            log_id: Log ID to delete
            
        Returns:
            bool: Success or failure
        """
        # Get the log file
        _, filename = self.get_log(log_id)
        if not filename:
            return False
        
        # Delete the file
        filepath = os.path.join(self.logs_dir, filename)
        os.remove(filepath)
        
        return True
    
    def list_logs(self):
        """List all logs.
        
        Returns:
            list: Log metadata
        """
        logs = []
        
        for filename in os.listdir(self.logs_dir):
            if not filename.endswith('.json'):
                continue
                
            filepath = os.path.join(self.logs_dir, filename)
            
            try:
                with open(filepath, 'r') as f:
                    log_data = json.load(f)
                
                meta = log_data.get('meta', {})
                entry_count = len(log_data.get('logs', {}).get('log', []))
                
                logs.append({
                    'id': meta.get('id', 'unknown'),
                    'type': meta.get('type', 'unknown'),
                    'created': meta.get('created', ''),
                    'filename': filename,
                    'entry_count': entry_count
                })
            except:
                # Skip files with errors
                continue
        
        # Sort by creation date (newest first)
        logs.sort(key=lambda x: x.get('created', ''), reverse=True)
        
        return logs
    
    def get_templates(self):
        """Get available sample log templates.
        
        Returns:
            dict: Templates by type
        """
        return {
            "dns": {
                "name": "DNS Record Change",
                "structure": {
                    "_source": {
                        "@timestamp": "2023-01-01T12:00:00.000+00:00",
                        "action": {"type": "create", "result": True},
                        "actor": {"type": "user", "email": "user@example.com", "ip": "192.168.1.1"},
                        "when": "2023-01-01T12:00:00.000+00:00",
                        "newValueJson": {
                            "type": "A",
                            "name": "example.com",
                            "content": "192.168.1.1",
                            "zone_name": "example.com"
                        },
                        "oldValueJson": {}
                    }
                }
            },
            "password": {
                "name": "Password Change",
                "structure": {
                    "UserId": "admin@example.com",
                    "ObjectId": "user@example.com",
                    "Operation": "Reset-Password",
                    "ResultStatus": "Success",
                    "@timestamp": "2023-01-01T12:00:00.000+00:00"
                }
            }
        }