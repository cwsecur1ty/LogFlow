#!/usr/bin/env node

// Import required modules
const fs = require('fs');
const { Liquid } = require('liquidjs');

// Initialize the Liquid engine with strict whitespace control
const engine = new Liquid({
  strictFilters: false,
  strictVariables: false,
  trimTagRight: true,
  trimTagLeft: true,
  trimOutputRight: true,
  trimOutputLeft: true,
  greedy: false
});

// Process arguments
const args = process.argv.slice(2);
if (args.length < 2) {
  console.error('Usage: node liquid_processor.js <log_file_path> <template_file_path>');
  process.exit(1);
}

const logFilePath = args[0];
const templateFilePath = args[1];

// Main processing function
async function processTemplate() {
  try {
    // Read the log data
    const logData = JSON.parse(fs.readFileSync(logFilePath, 'utf8'));
    
    // Read the template
    const templateContent = fs.readFileSync(templateFilePath, 'utf8');
    
    // Process the log data to make it match expected format
    const processedLogs = [];
    
    for (const logEntry of logData.logs.log) {
      // If the log entry has a _source field, merge it with the top level
      if (logEntry._source) {
        const processedEntry = { ...logEntry };
        
        // Move _source fields to the top level
        for (const [key, value] of Object.entries(logEntry._source)) {
          processedEntry[key] = value;
        }
        
        // Remove the original _source field
        delete processedEntry._source;
        processedLogs.push(processedEntry);
      } else {
        processedLogs.push(logEntry);
      }
    }
    
    // Prepare the template context
    const context = {
      logs: { log: processedLogs }
    };
    
    // Render the template
    const result = await engine.parseAndRender(templateContent, context);
    
    // First, normalize all line endings
    let processedResult = result.replace(/\r\n/g, '\n');
    
    // Process line by line to handle various whitespace issues
    const lines = processedResult.split('\n');
    const cleanedLines = [];
    let previousLineEmpty = false;
    
    for (let i = 0; i < lines.length; i++) {
      // Trim the current line
      let line = lines[i].trimRight();
      
      // Skip line if empty and previous was empty
      if (line.trim() === '' && previousLineEmpty) {
        continue;
      }
      
      // Fix bullet points with excessive spaces
      line = line.replace(/^(\s*)\*\s{2,}/g, '$1* ');
      
      // Fix specific pattern after bullet points
      line = line.replace(/^(\s*)\*\s+(System|Unknown actor|`.+?`)\s+/g, '$1* $2 ');
      
      // Fix any consecutive spaces between non-whitespace characters
      line = line.replace(/(\S)\s{2,}(\S)/g, '$1 $2');
      
      cleanedLines.push(line);
      previousLineEmpty = line.trim() === '';
    }
    
    // Join the lines back together
    processedResult = cleanedLines.join('\n');
    
    // Remove any empty lines at the beginning
    processedResult = processedResult.replace(/^\n+/, '');
    
    // Remove empty lines at the end
    processedResult = processedResult.replace(/\n+$/, '');
    
    // Fix the specific "observed that" + newline + "System" pattern
    processedResult = processedResult.replace(
      /(observed that)\n\s+(System|Unknown actor|`.+?`)/g, 
      '$1 $2'
    );
    
    // Fix other common patterns with unwanted newlines
    processedResult = processedResult.replace(
      /(at `[^`]+`)\n\s+on/g,
      '$1 on'
    );
    
    // Output the result
    console.log(processedResult);
  } catch (error) {
    console.error('Error processing template:', error.message);
    process.exit(1);
  }
}

// Execute the processing
processTemplate();