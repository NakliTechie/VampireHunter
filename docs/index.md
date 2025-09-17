# Vampire Hunter Documentation

Welcome to the Vampire Hunter documentation. This guide will help you understand how to use Vampire Hunter to manage your system's vampire processes.

## Table of Contents

- [Installation](#installation)
- [Quick Start](#quick-start)
- [Usage](#usage)
- [Advanced Configuration](#advanced-configuration)
- [Troubleshooting](#troubleshooting)
- [FAQ](#faq)

## Installation

### Prerequisites

- Python 3.6 or higher
- pip (Python package installer)

### Installing Dependencies

Vampire Hunter requires two Python packages:

1. `tabulate` - For beautiful table formatting
2. `psutil` - For system and process utilities

Install them using pip:

```bash
pip3 install tabulate psutil
```

Or install them using the requirements file:

```bash
pip3 install -r requirements.txt
```

### Downloading Vampire Hunter

You can download Vampire Hunter in two ways:

1. Clone the repository:
   ```bash
   git clone https://github.com/NakliTechie/VampireHunter.git
   cd VampireHunter
   ```

2. Download the script directly:
   ```bash
   wget https://raw.githubusercontent.com/yourusername/vampire-hunter/main/vampire_hunter.py
   ```

## Quick Start

After installing the dependencies, you can run Vampire Hunter directly:

```bash
python3 vampire_hunter.py
```

Or make it executable and run it:

```bash
chmod +x vampire_hunter.py
./vampire_hunter.py
```

## Usage

### Basic Usage

When you run Vampire Hunter, it will:

1. Scan your system for processes listening on TCP ports
2. Display them in a formatted table with memory usage
3. Present an interactive menu for managing processes

### Interactive Menu Options

- **Number**: Enter the ID of a process to kill it
- **a**: Kill all processes (with confirmation)
- **r**: Refresh the process list
- **q**: Quit the program

### Example Output

```
+----+-------+------------+-----------------+----------+---------------------------------------------+
| ID | PID   | Name       | Port            | Memory   | Command                                     |
+====+=======+============+=================+==========+=============================================+
| 1  | 1234  | node       | *:3000          | 45.2 MB  | node server.js                              |
| 2  | 5678  | Python     | 127.0.0.1:8000  | 32.1 MB  | python -m http.server                       |
| 3  | 9012  | webpack    | *:8080          | 120.5 MB | webpack serve --mode development            |
+----+-------+------------+-----------------+----------+---------------------------------------------+

🔹 Total processes: 3
🔹 Total estimated memory usage: 197.8 MB

Select action:
  Enter number to kill a specific process
  'a' to kill ALL processes
  'r' to refresh the list
  'q' to quit
Choice:
```

## Advanced Configuration

### Command Line Arguments

Vampire Hunter supports the following command line arguments:

- `-h`, `--help`: Show help message

### Environment Variables

Vampire Hunter currently doesn't use environment variables, but this may change in future versions.

## Troubleshooting

### Common Issues

1. **Permission Denied**: Some processes may require administrator privileges to kill
   - Solution: Run Vampire Hunter with sudo (not recommended for regular use)

2. **Process Not Found**: A process may have ended between scanning and killing
   - Solution: Refresh the list with 'r'

3. **Module Not Found**: Missing dependencies
   - Solution: Install required packages with `pip3 install tabulate psutil`

### Reporting Issues

If you encounter any issues, please report them on the GitHub repository with:

- Your operating system and version
- Python version
- Error message
- Steps to reproduce

## FAQ

### What are "vampire processes"?

Vampire processes are server processes that continue running in the background, consuming system resources without your active use. They're commonly created during development when starting local servers for testing.

### Is it safe to kill all processes?

Vampire Hunter asks for confirmation before killing any processes. However, be cautious when using the "kill all" option, as it will terminate all detected server processes, which might include important system services.

### Can Vampire Hunter harm my system?

Vampire Hunter is designed to be safe:
- It only targets processes listening on TCP ports
- It asks for confirmation before killing processes
- It uses graceful termination first
- It provides detailed information about each process

### Does Vampire Hunter work on Windows?

Vampire Hunter works on Windows through Windows Subsystem for Linux (WSL). Native Windows support may be added in future versions.

### How often should I run Vampire Hunter?

You can run Vampire Hunter whenever you notice your system slowing down or when you want to clean up unused server processes. There's no harm in running it frequently.