#!/usr/bin/env python3

"""
Server Manager Script with Memory Usage
Detects and interactively allows killing of server processes with memory info using tabulate
"""

import subprocess
import os
import sys
import psutil
import re
from tabulate import tabulate

# Color codes for output
COLORS = {
    'red': '\033[0;31m',
    'green': '\033[0;32m',
    'yellow': '\033[1;33m',
    'blue': '\033[0;34m',
    'purple': '\033[0;35m',
    'cyan': '\033[0;36m',
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

def format_memory(mem_kb):
    """Format memory size in a human-readable format"""
    if mem_kb >= 1048576:  # GB
        return f"{mem_kb/1048576:.1f} GB"
    elif mem_kb >= 1024:   # MB
        return f"{mem_kb/1024:.1f} MB"
    else:                  # KB
        return f"{mem_kb} KB"

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
        print("  'q' to quit")
        print("Choice: ", end="")
        
        try:
            choice = input().strip().lower()
            
            if choice == 'q':
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
                    log_warning(f"Invalid choice. Please enter a number between 1 and {len(processes)}, 'a', 'r', or 'q'.")
            else:
                log_warning("Invalid choice. Please enter a number, 'a', 'r', or 'q'.")
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
    print("3. Present them in an interactive menu")
    print("4. Allow you to selectively kill them")
    print()
    print("Features:")
    print("• Shows memory usage for each process using tabulate for formatting")
    print("• Safe process killing (SIGTERM first, then SIGKILL if needed)")
    print("• Process details display")
    print("• Selective or bulk killing options")
    print("• Refresh option to update the process list")
    print("• Confirmation prompts for safety")

def main():
    """Main function"""
    # Check for help flag
    if len(sys.argv) > 1 and sys.argv[1] in ['-h', '--help']:
        show_help()
        return
    
    # Check if required commands are available
    required_commands = ['lsof']
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
        
        # Run interactive menu
        should_refresh = interactive_menu(processes)
        if not should_refresh:
            break

if __name__ == "__main__":
    main()