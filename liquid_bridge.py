import subprocess
import os
import json
import tempfile

def process_liquid_template(log_data, template_content):
    """
    Process a Liquid template with log data using Node.js.
    
    Args:
        log_data (dict): The log data to process
        template_content (str): The Liquid template content
    
    Returns:
        str: The processed template output
    """
    # Create temporary files for the log data and template
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as log_file:
        json.dump(log_data, log_file)
        log_file_path = log_file.name
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.liquid', delete=False) as template_file:
        template_file.write(template_content)
        template_file_path = template_file.name
    
    try:
        # Get the directory of the current script
        script_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Path to the Node.js script
        node_script = os.path.join(script_dir, 'node_scripts', 'liquid_processor.js')
        
        # Run the Node.js script
        result = subprocess.run(
            ['node', node_script, log_file_path, template_file_path],
            capture_output=True,
            text=True,
            check=True
        )
        
        # Return the output
        return result.stdout
    
    except subprocess.CalledProcessError as e:
        # Handle errors from the Node.js script
        error_message = e.stderr.strip()
        raise RuntimeError(f"Error processing template: {error_message}")
    
    finally:
        # Clean up temporary files
        os.unlink(log_file_path)
        os.unlink(template_file_path)

def process_log_file(log_file_path, template_file_path):
    """
    Process a log file using a Liquid template.
    
    Args:
        log_file_path (str): Path to the log file
        template_file_path (str): Path to the template file
    
    Returns:
        str: The processed template output
    """
    # Read the log file
    with open(log_file_path, 'r') as file:
        log_data = json.load(file)
    
    # Read the template file
    with open(template_file_path, 'r') as file:
        template_content = file.read()
    
    # Process the template
    return process_liquid_template(log_data, template_content)