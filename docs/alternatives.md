# Alternative Versions

Vampire Hunter comes with two implementations to suit different needs and environments.

## Python Version (Recommended)

The Python version (`vampire_hunter.py`) is the recommended implementation with the following advantages:

### Features
- Beautiful table formatting using the `tabulate` library
- More robust process handling with `psutil`
- Better error handling and cross-platform support
- Memory usage displayed in an easily readable format
- Refresh option to update the process list without restarting

### Requirements
- Python 3.6+
- `tabulate` and `psutil` packages

### Usage
```bash
python3 vampire_hunter.py
```

## Bash Version

The bash version (`vampire_hunter.sh`) is a lightweight alternative with minimal dependencies.

### Features
- No external Python dependencies required
- Works on most Unix-like systems with standard utilities
- Basic table formatting
- Memory usage information
- Interactive process management

### Requirements
- Bash shell
- Standard Unix utilities (`lsof`, `ps`, `bc`)
- Available on most macOS and Linux systems

### Usage
```bash
chmod +x vampire_hunter.sh
./vampire_hunter.sh
```

## Choosing the Right Version

### Use the Python version if:
- You want the best user experience
- You have Python installed
- You want more robust process handling
- You appreciate beautiful formatting

### Use the Bash version if:
- You prefer minimal dependencies
- You're on a system without Python
- You want maximum portability
- You prefer lightweight solutions

Both versions provide the core functionality of detecting and killing vampire processes, so choose based on your preferences and system constraints.