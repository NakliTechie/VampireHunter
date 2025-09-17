# Vampire Hunter

_kill those memory-draining vampire processes_

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

If you're a newbie coder or "vibe coder", you'll end up spawning many small servers to serve projects locally. Some will be from the terminal window, but others may be from coding agents. This utility helps you list and then interactively kill the vampire processes. This name is inspired from "vampire draw", used for home electronics drawing small bits of power.

## Why Vampire Hunter?

As developers, we often start local development servers, testing environments, and various tools that listen on ports. Over time, these processes accumulate and consume system resources without us realizing it. They're like vampires slowly draining your system's memory and CPU - hence the name "Vampire Hunter".

## Features

- 🔍 **Process Discovery**: Automatically detects all processes listening on TCP ports
- 📊 **Memory Monitoring**: Shows detailed memory usage for each process
- 🎯 **Interactive Selection**: Clean interface to selectively kill processes
- 🛡️ **Safe Operations**: Uses graceful termination before force killing
- 🔄 **Live Refresh**: Update the process list without restarting
- 📋 **Formatted Display**: Beautiful table formatting with tabulate
- ⚡ **Cross-platform**: Works on macOS, Linux, and Windows (WSL)

## Installation

### Prerequisites

- Python 3.6+
- pip (Python package installer)

### Install Required Dependencies

```bash
pip3 install tabulate psutil
```

### Clone the Repository

```bash
git clone https://github.com/NakliTechie/VampireHunter.git
cd VampireHunter
```

## Usage

### Quick Start (Python Version - Recommended)

```bash
python3 vampire_hunter.py
```

### Alternative (Bash Version)

```bash
chmod +x vampire_hunter.sh
./vampire_hunter.sh
```

### Make it Executable (Optional)

```bash
chmod +x vampire_hunter.py
./vampire_hunter.py
```

### Command Line Options

```bash
# Show help
python3 vampire_hunter.py -h

# Run with default settings
python3 vampire_hunter.py
```

## Interface

When you run Vampire Hunter, you'll see a formatted table like this:

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
```

### Interactive Options

- Enter a number to kill a specific process
- `a` to kill ALL processes (with confirmation)
- `r` to refresh the process list
- `q` to quit

## Alternative Implementations

Vampire Hunter comes with two implementations:

1. **Python Version** (`vampire_hunter.py`) - Recommended with better formatting and features
2. **Bash Version** (`vampire_hunter.sh`) - Lightweight alternative with minimal dependencies

See [Alternative Versions](docs/alternatives.md) for detailed comparison.

## Common Vampire Processes

Vampire Hunter is particularly useful for identifying these common resource-draining processes:

- **Development Servers**: Node.js, Python Flask/Django, React/Vue development servers
- **Build Tools**: Webpack dev servers, Vite, Parcel
- **Database Tools**: Local MongoDB, PostgreSQL, MySQL instances
- **IDE Helpers**: VS Code helpers, JetBrains background processes
- **Media Apps**: Spotify, Discord, Slack background processes
- **AI Tools**: Ollama, local LLM servers
- **Cloud Tools**: Docker containers, Kubernetes minikube

## Safety Features

- ✅ Confirmation prompts before killing any process
- ✅ Graceful termination (SIGTERM) before force killing (SIGKILL)
- ✅ Process details displayed before action
- ✅ Ability to cancel at any point
- ✅ Error handling for permission issues

## Contributing

Contributions are welcome! Feel free to submit issues and pull requests.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a pull request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Inspired by the concept of "vampire draw" in electronics
- Uses [psutil](https://github.com/giampaolo/psutil) for system monitoring
- Uses [tabulate](https://github.com/astanin/python-tabulate) for beautiful table formatting