from flask import Flask, render_template, request, flash, redirect, url_for, jsonify
import os
import json
import tempfile
from werkzeug.utils import secure_filename
import os
from liquid_bridge import process_liquid_template
from log_builder import LogBuilder

app = Flask(__name__)
app.secret_key = os.urandom(16)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Create folders if they don't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Initialize log builder
log_builder = LogBuilder('sample_logs')

@app.route('/')
def home():
    """Home page with navigation to tools."""
    return render_template('home.html')

@app.route('/liquid-processor')
def liquid_processor():
    """Liquid template processing page."""
    # Get sample logs for dropdown
    logs = log_builder.list_logs()
    return render_template('liquid_processor.html', logs=logs)

@app.route('/process', methods=['POST'])
def process():
    # Get template content
    template_content = None
    if 'template_file' in request.files and request.files['template_file'].filename:
        template_file = request.files['template_file']
        template_content = template_file.read().decode('utf-8')
    else:
        flash('Template file is required')
        return redirect(url_for('liquid_processor'))
    
    # Get log data
    log_data = None
    
    # Check if user is uploading a log file
    if 'log_file' in request.files and request.files['log_file'].filename:
        log_file = request.files['log_file']
        
        try:
            # Read the log file directly without saving to disk first
            log_content = log_file.read().decode('utf-8')
            log_data = json.loads(log_content)
        except json.JSONDecodeError:
            flash('Invalid JSON file')
            return redirect(url_for('liquid_processor'))
        except Exception as e:
            flash(f'Error reading log file: {str(e)}')
            return redirect(url_for('liquid_processor'))
    
    # Check if user is selecting a sample log
    elif 'sample_log' in request.form and request.form['sample_log']:
        log_id = request.form['sample_log']
        log_data, _ = log_builder.get_log(log_id)
        
        if not log_data:
            flash('Selected sample log not found')
            return redirect(url_for('liquid_processor'))
    
    else:
        flash('Either upload a log file or select a sample log')
        return redirect(url_for('liquid_processor'))
    
    # Process the template
    try:
        result = process_liquid_template(log_data, template_content)
        return render_template('result.html', result=result)
    except Exception as e:
        flash(f'Error processing template: {str(e)}')
        return redirect(url_for('liquid_processor'))

@app.route('/example')
def example():
    """Process and display an example for demonstration."""
    try:
        # Get paths for example files
        script_dir = os.path.dirname(os.path.abspath(__file__))
        examples_dir = os.path.join(script_dir, 'log_examples')
        
        log_path = os.path.join(examples_dir, 'cloudflare_dns.json')
        template_path = os.path.join(examples_dir, 'dns_record_created.liquid')
        
        # Read the log file
        with open(log_path, 'r') as file:
            log_data = json.load(file)
        
        # Read the template file
        with open(template_path, 'r') as file:
            template_content = file.read()
        
        # Process the template
        result = process_liquid_template(log_data, template_content)
        
        return render_template('result.html', result=result, is_example=True)
    
    except Exception as e:
        flash(f'Error processing example: {str(e)}')
        return redirect(url_for('liquid_processor'))

# JSON Analyser Routes
@app.route('/analyser')
def log_analyser():
    """JSON Log analyser page."""
    return render_template('analyser.html')

# Fixed the redirect in analyse_json function
@app.route('/analyze', methods=['POST'])
def analyze_json():
    """Process and analyze JSON log data."""
    try:
        # Get JSON data from form
        json_data = request.form.get('json_data', '{}')
        log_data = json.loads(json_data)
        
        # extract and analyse the log data
        analysis = analyze_log_structure(log_data)
        
        return render_template('analysis_result.html', 
                               analysis=analysis, 
                               raw_json=json.dumps(log_data, indent=2))
    except json.JSONDecodeError:
        flash('Invalid JSON data')
        return redirect(url_for('log_analyser'))  # route name
    except Exception as e:
        flash(f'Error analyzing JSON: {str(e)}')
        return redirect(url_for('log_analyser'))  # route name

def analyze_log_structure(log_data):
    """Analyze the structure of a JSON log and extract key information."""
    analysis = {
        'summary': {},
        'structure': {},
        'fields': [],
        'samples': {},
        'statistics': {},
        'patterns': {}
    }
    
    # Check if it follows the logs.log pattern
    if isinstance(log_data, dict) and 'logs' in log_data and 'log' in log_data['logs']:
        log_entries = log_data['logs']['log']
        analysis['summary']['format'] = 'Standard logs.log format'
        analysis['summary']['entry_count'] = len(log_entries)
        
        # Get the structure from the first entry
        if log_entries and len(log_entries) > 0:
            first_entry = log_entries[0]
            
            # Check for _source field (common in elasticsearch logs)
            if '_source' in first_entry:
                analysis['summary']['has_source'] = True
                source_fields = extract_fields(first_entry['_source'])
                analysis['fields'] = source_fields
                
                # Get samples and statistics of important fields
                analysis['samples'] = extract_samples(log_entries, source_fields, '_source')
                analysis['statistics'] = calculate_field_statistics(log_entries, source_fields, '_source')
                analysis['patterns'] = identify_patterns(log_entries, source_fields, '_source')
            else:
                analysis['summary']['has_source'] = False
                analysis['fields'] = extract_fields(first_entry)
                
                # Get samples and statistics of important fields
                analysis['samples'] = extract_samples(log_entries, analysis['fields'])
                analysis['statistics'] = calculate_field_statistics(log_entries, analysis['fields'])
                analysis['patterns'] = identify_patterns(log_entries, analysis['fields'])
    else:
        # Handle other JSON structures
        analysis['summary']['format'] = 'Non-standard JSON structure'
        analysis['fields'] = extract_fields(log_data)
    
    return analysis

def extract_fields(data, prefix=''):
    """Extract all fields from a JSON object with their types."""
    fields = []
    
    if isinstance(data, dict):
        for key, value in data.items():
            full_key = f"{prefix}.{key}" if prefix else key
            
            if isinstance(value, dict):
                fields.append({
                    'path': full_key,
                    'type': 'object',
                    'sample': str(value)[:50] + ('...' if len(str(value)) > 50 else '')
                })
                fields.extend(extract_fields(value, full_key))
            elif isinstance(value, list):
                fields.append({
                    'path': full_key,
                    'type': 'array',
                    'sample': str(value)[:50] + ('...' if len(str(value)) > 50 else '')
                })
                # If list has items, analyze the first one
                if value and len(value) > 0 and isinstance(value[0], dict):
                    fields.extend(extract_fields(value[0], f"{full_key}[0]"))
            else:
                fields.append({
                    'path': full_key,
                    'type': type(value).__name__,
                    'sample': str(value)[:50] + ('...' if len(str(value)) > 50 else '')
                })
    
    return fields

def extract_samples(log_entries, fields, source_field=None):
    """Extract sample values for important fields."""
    samples = {}
    important_fields = ['type', 'id', 'action', 'actor', 'timestamp', '@timestamp', 'when']
    
    for field in fields:
        field_path = field['path']
        base_name = field_path.split('.')[-1]
        
        if any(key in base_name.lower() for key in important_fields):
            values = set()
            
            for entry in log_entries[:10]:  # Limit to first 10 entries
                # Handle source field if present
                if source_field and source_field in entry:
                    entry = entry[source_field]
                
                # Navigate to the field using the path
                value = get_nested_value(entry, field_path.split('.'))
                
                if value is not None:
                    # For objects/arrays, convert to string representation
                    if isinstance(value, (dict, list)):
                        value = json.dumps(value)
                    
                    values.add(str(value))
                    
                    # Limit to 5 unique values
                    if len(values) >= 5:
                        break
            
            if values:
                samples[field_path] = list(values)
    
    return samples

def calculate_field_statistics(log_entries, fields, source_prefix=''):
    """Calculate statistical insights for log fields."""
    stats = {}
    
    for entry in log_entries:
        data = entry.get('_source', entry) if source_prefix else entry
        
        for field in fields:
            field_path = field['path']
            field_type = field['type']
            
            # Initialize stats structure if not exists
            if field_path not in stats:
                stats[field_path] = {
                    'value_counts': {},
                    'total_occurrences': 0,
                    'unique_values': 0,
                    'type': field_type
                }
            
            # Extract the field value using the path
            value = get_nested_value(data, field_path.split('.'))
            
            if value is not None:
                # Count frequency of values
                str_value = str(value)
                stats[field_path]['value_counts'][str_value] = stats[field_path]['value_counts'].get(str_value, 0) + 1
                stats[field_path]['total_occurrences'] += 1
    
    # Calculate additional statistics
    for field_path in stats:
        value_counts = stats[field_path]['value_counts']
        stats[field_path]['unique_values'] = len(value_counts)
        
        # Get top 5 most common values
        sorted_values = sorted(value_counts.items(), key=lambda x: x[1], reverse=True)
        stats[field_path]['most_common'] = sorted_values[:5]
        
        # Calculate frequency distribution
        total = stats[field_path]['total_occurrences']
        stats[field_path]['frequency_distribution'] = {
            value: (count / total) * 100 
            for value, count in sorted_values[:5]
        }
    
    return stats

def identify_patterns(log_entries, fields, source_prefix=''):
    """Identify common patterns and correlations in log entries."""
    patterns = {
        'temporal_patterns': {},
        'field_correlations': {},
        'sequence_patterns': []
    }
    
    # Track field value sequences
    field_sequences = {}
    
    for i, entry in enumerate(log_entries):
        data = entry.get('_source', entry) if source_prefix else entry
        
        # Analyze temporal patterns if timestamp field exists
        timestamp = get_nested_value(data, ['when']) or get_nested_value(data, ['timestamp'])
        if timestamp:
            hour = extract_hour_from_timestamp(timestamp)
            patterns['temporal_patterns'][hour] = patterns['temporal_patterns'].get(hour, 0) + 1
        
        # Track field value sequences for pattern detection
        for field in fields:
            field_path = field['path']
            value = get_nested_value(data, field_path.split('.'))
            
            if value is not None:
                if field_path not in field_sequences:
                    field_sequences[field_path] = []
                field_sequences[field_path].append(str(value))
        
        # Analyze field correlations
        if i > 0:
            prev_data = log_entries[i-1].get('_source', log_entries[i-1]) if source_prefix else log_entries[i-1]
            for field1 in fields:
                for field2 in fields:
                    if field1['path'] != field2['path']:
                        value1 = get_nested_value(data, field1['path'].split('.'))
                        value2 = get_nested_value(data, field2['path'].split('.'))
                        prev_value1 = get_nested_value(prev_data, field1['path'].split('.'))
                        
                        if value1 == prev_value1 and value2 is not None:
                            key = f"{field1['path']} → {field2['path']}"
                            if key not in patterns['field_correlations']:
                                patterns['field_correlations'][key] = {
                                    'count': 0,
                                    'examples': []
                                }
                            if len(patterns['field_correlations'][key]['examples']) < 3:
                                patterns['field_correlations'][key]['examples'].append({
                                    'value1': value1,
                                    'value2': value2
                                })
                            patterns['field_correlations'][key]['count'] += 1
    
    # Find common sequences in field values
    for field_path, values in field_sequences.items():
        if len(values) >= 3:
            common_sequences = find_common_sequences(values)
            if common_sequences:
                patterns['sequence_patterns'].append({
                    'field': field_path,
                    'sequences': common_sequences[:3]  # Top 3 most common sequences
                })
    
    return patterns

def get_nested_value(obj, path):
    """Safely get nested value from dictionary using path list."""
    for key in path:
        if isinstance(obj, dict):
            obj = obj.get(key)
        else:
            return None
    return obj

def extract_hour_from_timestamp(timestamp):
    """Extract hour from timestamp string."""
    try:
        # Add different timestamp format parsing as needed
        if isinstance(timestamp, str):
            if 'T' in timestamp:
                return int(timestamp.split('T')[1].split(':')[0])
            return int(timestamp.split(' ')[1].split(':')[0])
    except:
        return None

def find_common_sequences(values, min_length=2, max_sequences=3):
    """Find common sequences in a list of values."""
    sequences = {}
    
    for i in range(len(values) - min_length + 1):
        for j in range(i + min_length, min(i + 5, len(values) + 1)):
            sequence = tuple(values[i:j])
            if sequence not in sequences:
                sequences[sequence] = 0
            sequences[sequence] += 1
    
    # Sort by frequency and sequence length
    sorted_sequences = sorted(
        sequences.items(),
        key=lambda x: (x[1], len(x[0])),
        reverse=True
    )
    
    return [
        {
            'sequence': list(seq),
            'count': count,
            'length': len(seq)
        }
        for seq, count in sorted_sequences[:max_sequences]
        if count > 1  # Only return sequences that appear more than once
    ]

# Log Builder Routes
@app.route('/logs/templates')
def log_templates():
    """Get log templates as JSON."""
    templates = log_builder.get_templates()
    return jsonify(templates)

@app.route('/logs/templates/<template_type>')
def get_log_template(template_type):
    """Get a specific log template as JSON."""
    templates = log_builder.get_templates()
    if template_type in templates:
        return jsonify(templates[template_type])
    return jsonify({"error": "Template not found"}), 404

@app.route('/logs')
def log_list():
    """Display the list of sample logs."""
    logs = log_builder.list_logs()
    return render_template('logs.html', logs=logs)

@app.route('/logs/create', methods=['GET', 'POST'])
def create_log():
    """Create a new sample log."""
    if request.method == 'POST':
        log_type = request.form.get('log_type')
        
        try:
            # Parse JSON data
            log_data = json.loads(request.form.get('log_data', '[]'))
            
            # Create log
            log_id = log_builder.create_log(log_type, log_data)
            
            flash(f'Sample log created successfully')
            return redirect(url_for('edit_log', log_id=log_id))
        
        except json.JSONDecodeError:
            flash('Invalid JSON data')
            return render_template('create_log.html', templates=log_builder.get_templates())
        
        except Exception as e:
            flash(f'Error creating log: {str(e)}')
            return render_template('create_log.html', templates=log_builder.get_templates())
    
    # GET request
    return render_template('create_log.html', templates=log_builder.get_templates())

@app.route('/logs/edit/<log_id>', methods=['GET', 'POST'])
def edit_log(log_id):
    """Edit a sample log."""
    log_data, filename = log_builder.get_log(log_id)
    
    if not log_data:
        flash('Sample log not found')
        return redirect(url_for('log_list'))
    
    if request.method == 'POST':
        try:
            # Parse JSON data
            new_log_data = json.loads(request.form.get('log_data', '[]'))
            
            # Update log
            if log_builder.update_log(log_id, new_log_data):
                flash('Sample log updated successfully')
            else:
                flash('Failed to update sample log')
            
            # Reload log data
            log_data, _ = log_builder.get_log(log_id)
            
        except json.JSONDecodeError:
            flash('Invalid JSON data')
        
        except Exception as e:
            flash(f'Error updating log: {str(e)}')
    
    # Prepare log data for display
    log_entries = log_data.get('logs', {}).get('log', [])
    log_entries_json = json.dumps(log_entries, indent=2)
    
    return render_template(
        'edit_log.html',
        log_id=log_id,
        log_type=log_data.get('meta', {}).get('type', 'unknown'),
        log_data=log_entries_json,
        filename=filename
    )

@app.route('/logs/delete/<log_id>', methods=['POST'])
def delete_log(log_id):
    """Delete a sample log."""
    if log_builder.delete_log(log_id):
        flash('Sample log deleted successfully')
    else:
        flash('Failed to delete sample log')
    
    return redirect(url_for('log_list'))

if __name__ == '__main__':
    app.run(debug=True)