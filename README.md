# LogFlow

![LogFlow Logo](https://via.placeholder.com/150x50?text=LogFlow)

LogFlow is a flask & web-based toolkit for security professionals to process, analyse and manage logs/json.

## Features

- **Liquid Template Processing**: Transform JSON logs into structured content using custom Liquid templates
- **Log Analysis**: Examine JSON log structures, extract key fields and identify patterns
- **Log Builder**: Create and manage sample logs for testing and template development

## Getting Started

### Prerequisites

- Python 3.8+
- Node.js 14+ and npm

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/logflow.git
   cd logflow
   ```
2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Install Node.js dependencies:
   ```bash
   cd node_scripts
   npm install
   cd..
   ```
4. Run the application:
   ```bash
   py app.py
   ```
5. Open browser to http://127.0.0.1:5000

## Structure
```
logflow/
│
├── app.py                  # Main Flask application
├── liquid_bridge.py        # Bridge between Python and Node.js
├── log_builder.py          # Log building and management utilities
├── templates/              # Flask HTML templates
├── static/                 # Static files (CSS, JS)
├── node_scripts/           # Node.js scripts for Liquid processing
│   ├── liquid_processor.js # Liquid template processor
│   └── package.json        # Node.js dependencies
├── log_examples/           # Example log files and templates
├── sample_logs/            # User-generated sample logs
└── uploads/                # Temporary upload directory
```
### License

This project is licensed under the MIT License - see (LICENSE)[] for details.
