#!/usr/bin/env python3

"""
Vampire Hunter - Enhanced Process Manager with Memory Usage
Detects and interactively allows killing of server processes with memory info using tabulate
"""

import subprocess
import os
import sys
import psutil
import re
import time
import json
from tabulate import tabulate

# Color codes for output
COLORS = {
    'red': '\033[0;31m',
    'green': '\033[0;32m',
    'yellow': '\033[1;33m',
    'blue': '\033[0;34m',
    'purple': '\033[0;35m',
    'cyan': '\033[0;36m',
    'orange': '\033[0;33m',
    'nc': '\033[0m'  # No Color
}

def log_info(message):
    print(f"{COLORS['blue']}🔹 {message}{COLORS['nc']}")

def log_success(message):
    print(f"{COLORS['green']}✅ {message}{COLORS['nc']}")

def log_warning(message):
    print(f"{COLORS['yellow']}⚠️  {message}{COLORS['nc']}")

def log_error(message):
    print(f"{COLORS['red']}❌ {message}{COLORS['nc']}", file=sys.stderr)

def log_vampire(message):
    print(f"{COLORS['orange']}🧛 {message}{COLORS['nc']}")

def format_memory(mem_kb):
    """Format memory size in a human-readable format"""
    if mem_kb >= 1048576:  # GB
        return f"{mem_kb/1048576:.1f} GB"
    elif mem_kb >= 1024:   # MB
        return f"{mem_kb/1024:.1f} MB"
    else:                  # KB
        return f"{mem_kb} KB"

def get_system_memory_info():
    """Get overall system memory information"""
    try:
        # Use vm_stat on macOS to get memory information
        result = subprocess.run(['vm_stat'], capture_output=True, text=True)
        lines = result.stdout.strip().split('\n')
        
        memory_info = {}
        for line in lines:
            if 'Pages free:' in line:
                pages_free = int(line.split(':')[1].strip().replace('.', ''))
                memory_info['free_pages'] = pages_free
            elif 'Pages active:' in line:
                pages_active = int(line.split(':')[1].strip().replace('.', ''))
                memory_info['active_pages'] = pages_active
            elif 'Pages inactive:' in line:
                pages_inactive = int(line.split(':')[1].strip().replace('.', ''))
                memory_info['inactive_pages'] = pages_inactive
            elif 'Pages wired down:' in line:
                pages_wired = int(line.split(':')[1].strip().replace('.', ''))
                memory_info['wired_pages'] = pages_wired
            elif 'Pages stored in compressor:' in line:
                pages_compressed = int(line.split(':')[1].strip().replace('.', ''))
                memory_info['compressed_pages'] = pages_compressed
        
        # Calculate memory in MB (16384 bytes per page on macOS)
        page_size = 16384  # bytes per page on macOS
        memory_info['free_mb'] = (memory_info.get('free_pages', 0) * page_size) / (1024 * 1024)
        memory_info['active_mb'] = (memory_info.get('active_pages', 0) * page_size) / (1024 * 1024)
        memory_info['inactive_mb'] = (memory_info.get('inactive_pages', 0) * page_size) / (1024 * 1024)
        memory_info['wired_mb'] = (memory_info.get('wired_pages', 0) * page_size) / (1024 * 1024)
        memory_info['compressed_mb'] = (memory_info.get('compressed_pages', 0) * page_size) / (1024 * 1024)
        
        return memory_info
    except Exception as e:
        log_error(f"Error getting system memory info: {e}")
        return {}

def find_node_packages(root_path=None, max_depth=5):
    """Find all Node.js packages (directories with package.json) recursively"""
    if root_path is None:
        # Default to common locations where Node projects might be found
        root_paths = [
            os.path.expanduser("~"),
            os.getcwd(),
            "/Users",  # macOS default user directory
        ]
    else:
        root_paths = [root_path]
    
    node_packages = []
    package_json_pattern = re.compile(r'package\.json$', re.IGNORECASE)
    
    for root_path in root_paths:
        if not os.path.exists(root_path):
            continue
            
        for dirpath, dirnames, filenames in os.walk(root_path):
            # Calculate current depth from root
            current_depth = dirpath[len(root_path):].count(os.sep)
            if current_depth > max_depth:
                # Prune the search by clearing dirnames
                dirnames.clear()
                continue
            
            if 'node_modules' in dirpath:
                # Skip node_modules directories (they contain many packages but are dependencies)
                dirnames.clear()
                continue
                
            for filename in filenames:
                if package_json_pattern.match(filename):
                    package_path = os.path.join(dirpath, filename)
                    try:
                        with open(package_path, 'r', encoding='utf-8') as f:
                            # Try to parse package.json to get project info
                            try:
                                package_data = json.load(f)
                                name = package_data.get('name', 'Unknown')
                                version = package_data.get('version', 'Unknown')
                                scripts = package_data.get('scripts', {})
                                dependencies = package_data.get('dependencies', {})
                                dev_dependencies = package_data.get('devDependencies', {})
                                total_deps = len(dependencies) + len(dev_dependencies)
                            except json.JSONDecodeError:
                                name = 'Unknown (malformed package.json)'
                                version = 'Unknown'
                                scripts = {}
                                total_deps = 0
                        
                        # Get directory info
                        project_dir = os.path.dirname(package_path)
                        
                        node_packages.append({
                            'path': project_dir,
                            'name': name,
                            'version': version,
                            'scripts': list(scripts.keys()),
                            'dependency_count': total_deps,
                            'has_dev_server': any(script for script in ['start', 'dev', 'serve', 'watch'] if script in scripts)
                        })
                    except (PermissionError, UnicodeDecodeError):
                        # Skip files we can't read
                        continue
    
    return node_packages


def display_node_packages(node_packages):
    """Display Node packages in a formatted table"""
    if not node_packages:
        log_success("No Node.js packages found")
        return
    
    # Prepare table data
    table_data = []
    
    for i, pkg in enumerate(node_packages, 1):
        # Truncate long fields for better display
        display_name = pkg['name'][:20] if len(pkg['name']) > 20 else pkg['name']
        display_path = pkg['path'][-30:] if len(pkg['path']) > 30 else pkg['path']  # Show last 30 chars
        display_scripts = ', '.join(pkg['scripts'][:3]) + '...' if len(pkg['scripts']) > 3 else ', '.join(pkg['scripts'])
        display_scripts = display_scripts[:20] if len(display_scripts) > 20 else display_scripts
        
        table_data.append([
            i,
            display_name,
            pkg['version'],
            pkg['dependency_count'],
            'Yes' if pkg['has_dev_server'] else 'No',
            display_scripts,
            display_path
        ])
    
    # Display table
    headers = ["ID", "Name", "Version", "Deps", "Dev Server", "Scripts", "Path"]
    print(tabulate(table_data, headers=headers, tablefmt="grid"))
    
    # Display summary
    print()
    log_info(f"Total Node.js packages found: {len(node_packages)}")


def interactive_node_package_manager(node_packages):
    """Interactive menu for managing Node packages"""
    if not node_packages:
        log_success("No Node.js packages found to manage")
        return
    
    while True:
        print("\nSelect action for Node packages:")
        print("  Enter number to view package details")
        print("  'l' to list all packages again")
        print("  'q' to return to main menu")
        print("Choice: ", end="")
        
        try:
            choice = input().strip().lower()
            
            if choice == 'q':
                log_info("Returning to main menu...")
                break
            elif choice == 'l':
                display_node_packages(node_packages)
            elif choice.isdigit():
                index = int(choice)
                if 1 <= index <= len(node_packages):
                    pkg = node_packages[index - 1]
                    
                    print(f"\n{COLORS['yellow']}Package Details:{COLORS['nc']}")
                    print(f"  Name: {pkg['name']}")
                    print(f"  Version: {pkg['version']}")
                    print(f"  Path: {pkg['path']}")
                    print(f"  Dependencies: {pkg['dependency_count']}")
                    print(f"  Has Development Server: {'Yes' if pkg['has_dev_server'] else 'No'}")
                    print(f"  Scripts: {', '.join(pkg['scripts'])}")
                    
                    print("\nOptions:")
                    print("  'o' to open package directory in Finder (macOS) or file manager")
                    print("  'e' to explore package directory in terminal")
                    print("  'r' to return to package list")
                    print("Choice: ", end="")
                    
                    sub_choice = input().strip().lower()
                    if sub_choice == 'o':
                        # Open package directory in Finder/Explorer
                        try:
                            if sys.platform.startswith('darwin'):  # macOS
                                subprocess.run(['open', pkg['path']], check=True)
                            elif sys.platform.startswith('win'):  # Windows
                                subprocess.run(['explorer', pkg['path']], check=True)
                            elif sys.platform.startswith('linux'):  # Linux
                                subprocess.run(['xdg-open', pkg['path']], check=True)
                            log_success(f"Opened {pkg['path']} in file manager")
                        except subprocess.CalledProcessError:
                            log_error(f"Failed to open {pkg['path']}")
                    elif sub_choice == 'e':
                        print(f"\nTo explore this directory in terminal, run:")
                        print(f"  cd '{pkg['path']}'")
                    elif sub_choice != 'r':
                        log_warning("Invalid choice, returning to package list...")
                else:
                    log_warning(f"Invalid choice. Please enter a number between 1 and {len(node_packages)}, 'l', or 'q'.")
            else:
                log_warning("Invalid choice. Please enter a number, 'l', or 'q'.")
        except KeyboardInterrupt:
            print("\n")
            log_info("Returning to main menu...")
            break
        except EOFError:
            print()
            log_info("Returning to main menu...")
            break


def get_memory_health_report():
    """Generate a comprehensive memory health report"""
    system_info = get_system_memory_info()
    node_processes = get_node_processes()
    
    total_node_memory_kb = sum(proc['rss_kb'] for proc in node_processes)
    total_node_memory_formatted = format_memory(total_node_memory_kb)
    
    report = {
        'system_info': system_info,
        'node_processes': node_processes,
        'total_node_memory_kb': total_node_memory_kb,
        'total_node_memory_formatted': total_node_memory_formatted,
        'node_process_count': len(node_processes)
    }
    
    return report

def display_memory_health():
    """Display comprehensive memory health information"""
    report = get_memory_health_report()
    system_info = report['system_info']
    node_processes = report['node_processes']
    
    print(f"\n{COLORS['cyan']}📊 System Memory Health Report{COLORS['nc']}")
    print("=" * 50)
    
    # Display system memory info
    if system_info:
        print(f"{COLORS['blue']}System Memory:{COLORS['nc']}")
        print(f"  Free: {system_info.get('free_mb', 0):.1f} MB")
        print(f"  Active: {system_info.get('active_mb', 0):.1f} MB")
        print(f"  Inactive: {system_info.get('inactive_mb', 0):.1f} MB")
        print(f"  Wired: {system_info.get('wired_mb', 0):.1f} MB")
        print(f"  Compressed: {system_info.get('compressed_mb', 0):.1f} MB")
    
    print(f"\n{COLORS['green']}Node.js Processes:{COLORS['nc']}")
    print(f"Total Node.js processes: {report['node_process_count']}")
    print(f"Total Node.js memory usage: {report['total_node_memory_formatted']}")
    
    # Display top Node.js processes
    if node_processes:
        # Sort by memory usage (descending)
        sorted_nodes = sorted(node_processes, key=lambda x: x['rss_kb'], reverse=True)
        
        table_data = []
        for proc in sorted_nodes[:10]:  # Show top 10
            command = proc['command'][:50] + '...' if len(proc['command']) > 50 else proc['command']
            table_data.append([
                proc['pid'],
                f"{proc['mem_percent']:.1f}%",
                proc['rss_formatted'],
                proc['type'],
                command
            ])
        
        headers = ["PID", "Mem%", "RSS", "Type", "Command"]
        print(f"\n{COLORS['yellow']}Top Node.js Processes by Memory Usage:{COLORS['nc']}")
        print(tabulate(table_data, headers=headers, tablefmt="grid"))

def get_listening_processes():
    """Get all processes listening on TCP ports with memory info"""
    try:
        # Use lsof to find processes listening on ports
        result = subprocess.run(['lsof', '-iTCP', '-sTCP:LISTEN', '-P', '-n'], 
                              capture_output=True, text=True, check=True)
        
        lines = result.stdout.strip().split('\n')
        if not lines or len(lines) <= 1:
            return []
        
        # Skip header line
        data_lines = lines[1:]
        
        processes = []
        seen_processes = set()
        
        for line in data_lines:
            parts = line.split()
            if len(parts) < 10:
                continue
                
            try:
                pid = parts[1]
                name = parts[0]
                port = parts[8]
                
                # Create a unique identifier for the process
                process_key = f"{pid}:{port}"
                if process_key in seen_processes:
                    continue
                seen_processes.add(process_key)
                
                # Get process details using psutil
                try:
                    proc = psutil.Process(int(pid))
                    memory_info = proc.memory_info()
                    memory_kb = memory_info.rss / 1024  # RSS in KB
                    cmdline = ' '.join(proc.cmdline())
                except (psutil.NoSuchProcess, psutil.AccessDenied, ValueError):
                    # Fallback to ps command if psutil fails
                    try:
                        ps_result = subprocess.run(['ps', '-o', 'rss,command=', '-p', pid], 
                                                 capture_output=True, text=True, check=True)
                        ps_lines = ps_result.stdout.strip().split('\n')
                        if ps_lines and ps_lines[0]:
                            ps_parts = ps_lines[0].split(None, 1)
                            memory_kb = int(ps_parts[0]) if ps_parts else 0
                            cmdline = ps_parts[1] if len(ps_parts) > 1 else "Details unavailable"
                        else:
                            memory_kb = 0
                            cmdline = "Details unavailable"
                    except (subprocess.CalledProcessError, ValueError, IndexError):
                        memory_kb = 0
                        cmdline = "Details unavailable"
                
                processes.append({
                    'pid': pid,
                    'name': name,
                    'port': port,
                    'memory_kb': memory_kb,
                    'memory_formatted': format_memory(memory_kb),
                    'command': cmdline
                })
            except (IndexError, ValueError):
                continue
                
        return processes
    except subprocess.CalledProcessError as e:
        log_error(f"Error running lsof: {e}")
        return []

def kill_process(pid, name, force=False):
    """Kill a process with the given PID"""
    try:
        proc = psutil.Process(int(pid))
        if force:
            proc.kill()  # SIGKILL
            log_warning(f"Force killed process {name} (PID: {pid})")
        else:
            proc.terminate()  # SIGTERM
            log_success(f"Successfully terminated process {name} (PID: {pid})")
        return True
    except psutil.NoSuchProcess:
        log_error(f"Process {name} (PID: {pid}) not found")
        return False
    except psutil.AccessDenied:
        log_error(f"Access denied when trying to kill process {name} (PID: {pid})")
        return False
    except Exception as e:
        log_error(f"Error killing process {name} (PID: {pid}): {e}")
        return False

def display_processes(processes):
    """Display processes in a formatted table"""
    if not processes:
        log_success("No server processes found")
        return
    
    # Prepare table data
    table_data = []
    total_memory_kb = 0
    
    for i, proc in enumerate(processes, 1):
        # Truncate long fields for better display
        display_name = proc['name'][:15] if len(proc['name']) > 15 else proc['name']
        display_port = proc['port'][:15] if len(proc['port']) > 15 else proc['port']
        display_memory = proc['memory_formatted']
        display_command = proc['command'][:50] + '...' if len(proc['command']) > 50 else proc['command']
        
        table_data.append([
            i,
            proc['pid'],
            display_name,
            display_port,
            display_memory,
            display_command
        ])
        
        total_memory_kb += proc['memory_kb']
    
    # Display table
    headers = ["ID", "PID", "Name", "Port", "Memory", "Command"]
    print(tabulate(table_data, headers=headers, tablefmt="grid"))
    
    # Display summary
    print()
    log_info(f"Total processes: {len(processes)}")
    if total_memory_kb > 0:
        total_formatted = format_memory(total_memory_kb)
        log_info(f"Total estimated memory usage: {total_formatted}")

def interactive_menu(processes):
    """Interactive menu for managing processes"""
    if not processes:
        return
    
    while True:
        print("\nSelect action:")
        print("  Enter number to kill a specific process")
        print("  'a' to kill ALL processes")
        print("  'r' to refresh the list")
        print("  'n' to find and manage Node.js packages")
        print("  'm' to show memory health")
        print("  'q' to quit")
        print("Choice: ", end="")
        
        try:
            choice = input().strip().lower()
            
            if choice == 'n':
                log_info("Scanning for Node.js packages...")
                node_packages = find_node_packages()
                display_node_packages(node_packages)
                interactive_node_package_manager(node_packages)
            elif choice == 'q':
                log_info("Exiting...")
                break
            elif choice == 'a':
                confirm = input("Are you sure you want to kill ALL server processes? (y/N): ").strip().lower()
                if confirm in ['y', 'yes']:
                    killed_count = 0
                    for proc in processes:
                        if kill_process(proc['pid'], proc['name']):
                            killed_count += 1
                    log_success(f"Killed {killed_count}/{len(processes)} processes")
                else:
                    log_info("Cancelled")
            elif choice == 'm':
                display_memory_health()
            elif choice == 'r':
                log_info("Refreshing process list...")
                return True  # Signal to refresh
            elif choice.isdigit():
                index = int(choice)
                if 1 <= index <= len(processes):
                    proc = processes[index - 1]
                    confirm = input(f"Kill process {proc['name']} (PID: {proc['pid']}, Memory: {proc['memory_formatted']})? (y/N): ").strip().lower()
                    if confirm in ['y', 'yes']:
                        if not kill_process(proc['pid'], proc['name']):
                            force_confirm = input("Try force kill? (y/N): ").strip().lower()
                            if force_confirm in ['y', 'yes']:
                                kill_process(proc['pid'], proc['name'], force=True)
                    else:
                        log_info("Cancelled")
                else:
                    log_warning(f"Invalid choice. Please enter a number between 1 and {len(processes)}, 'a', 'r', 'n', 'm', or 'q'.")
            else:
                log_warning("Invalid choice. Please enter a number, 'a', 'r', 'n', 'm', or 'q'.")
        except KeyboardInterrupt:
            print("\n")
            log_info("Exiting...")
            break
        except EOFError:
            print()
            log_info("Exiting...")
            break
    
    return False  # Signal not to refresh

def show_help():
    """Display help information"""
    print("Vampire Hunter - Process Manager with Memory Usage")
    print("=" * 50)
    print("This script helps you detect and manage server processes (vampire processes) running on your machine with memory information.")
    print()
    print("Usage:")
    print("  ./vampire_hunter.py     # Run interactive vampire hunter")
    print("  ./vampire_hunter.py -h  # Show this help")
    print()
    print("The script will:")
    print("1. Scan for processes listening on TCP ports (vampire processes)")
    print("2. Show memory usage for each process in a formatted table")
    print("3. Analyze Node.js processes and memory usage")
    print("4. Present them in an interactive menu")
    print("5. Allow you to selectively kill them")
    print()
    print("Features:")
    print("• Shows memory usage for each process using tabulate for formatting")
    print("• Safe process killing (SIGTERM first, then SIGKILL if needed)")
    print("• Process details display")
    print("• Selective or bulk killing options")
    print("• Refresh option to update the process list")
    print("• Memory health report with Node.js analysis")
    print("• Confirmation prompts for safety")

def main():
    """Main function"""
    # Check for help flag
    if len(sys.argv) > 1 and sys.argv[1] in ['-h', '--help']:
        show_help()
        return
    
    # Check if required commands are available
    required_commands = ['lsof', 'vm_stat', 'ps']
    for cmd in required_commands:
        if not subprocess.run(['which', cmd], capture_output=True).returncode == 0:
            log_error(f"{cmd} command not found. Please install {cmd} to use this script.")
            sys.exit(1)
    
    print(f"{COLORS['green']}🧛 Vampire Hunter - Process Manager{COLORS['nc']}")
    print("=" * 38)
    print()
    
    # Main loop to allow refreshing
    while True:
        log_info("Scanning for server processes...")
        processes = get_listening_processes()
        display_processes(processes)
        
        # Also show memory health
        display_memory_health()
        
        # Run interactive menu
        should_refresh = interactive_menu(processes)
        if not should_refresh:
            break


def main():
    """Main function"""
    # Check for help flag
    if len(sys.argv) > 1 and sys.argv[1] in ['-h', '--help']:
        show_help()
        return
    
    # Check if required commands are available
    required_commands = ['lsof', 'vm_stat', 'ps']
    for cmd in required_commands:
        if not subprocess.run(['which', cmd], capture_output=True).returncode == 0:
            log_error(f"{cmd} command not found. Please install {cmd} to use this script.")
            sys.exit(1)
    
    print(f"{COLORS['green']}🧛 Vampire Hunter - Process Manager{COLORS['nc']}")
    print("=" * 38)
    print()
    
    # Main loop to allow refreshing
    while True:
        log_info("Scanning for server processes...")
        processes = get_listening_processes()
        display_processes(processes)
        
        # Also show memory health
        display_memory_health()
        
        # Run interactive menu
        should_refresh = interactive_menu(processes)
        if not should_refresh:
            break

if __name__ == "__main__":
    main()
