#!/bin/bash

# Server Manager Script with Memory Usage
# Detects and interactively allows killing of server processes with memory info

set -euo pipefail

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Utility functions
log_info() {
    echo -e "${BLUE}🔹 $*${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $*${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $*${NC}"
}

log_error() {
    echo -e "${RED}❌ $*${NC}" >&2
}

# Function to format memory size
format_memory() {
    local mem_kb=$1
    if [ "$mem_kb" -ge 1048576 ]; then
        # GB
        printf "%.1f GB" "$(echo "scale=1; $mem_kb/1048576" | bc -l)"
    elif [ "$mem_kb" -ge 1024 ]; then
        # MB
        printf "%.1f MB" "$(echo "scale=1; $mem_kb/1024" | bc -l)"
    else
        # KB
        echo "${mem_kb} KB"
    fi
}

# Function to get listening processes with memory info
get_listening_processes_with_memory() {
    # Use lsof to find processes listening on ports
    # Filter out common non-server processes and system processes
    local lsof_data
    lsof_data=$(lsof -iTCP -sTCP:LISTEN -P -n 2>/dev/null | grep -v "COMMAND")
    
    if [ -z "$lsof_data" ]; then
        return
    fi
    
    # Process each line
    while IFS= read -r line; do
        [ -z "$line" ] && continue
        
        local pid=$(echo "$line" | awk '{print $2}')
        local name=$(echo "$line" | awk '{print $1}')
        local port=$(echo "$line" | awk '{print $9}')
        
        # Get memory usage (RSS in KB)
        local mem_kb
        mem_kb=$(ps -o rss= -p "$pid" 2>/dev/null | tr -d ' ' || echo "0")
        
        # Get more details about the process
        local details
        details=$(ps -o command= -p "$pid" 2>/dev/null || echo "Details unavailable")
        
        # Format memory
        local mem_formatted
        if [ "$mem_kb" -gt 0 ]; then
            mem_formatted=$(format_memory "$mem_kb")
        else
            mem_formatted="N/A"
        fi
        
        echo "$pid|$name|$port|$mem_formatted|$details"
    done <<< "$lsof_data" | sort -u
}

# Function to kill a process
kill_process() {
    local pid=$1
    local name=$2
    
    if kill "$pid" 2>/dev/null; then
        log_success "Successfully killed process $name (PID: $pid)"
        return 0
    else
        log_error "Failed to kill process $name (PID: $pid)"
        return 1
    fi
}

# Function to kill process forcefully
kill_process_force() {
    local pid=$1
    local name=$2
    
    if kill -9 "$pid" 2>/dev/null; then
        log_warning "Force killed process $name (PID: $pid)"
        return 0
    else
        log_error "Failed to force kill process $name (PID: $pid)"
        return 1
    fi
}

# Main interactive function
manage_servers() {
    local processes
    local process_count=0
    
    log_info "Scanning for server processes..."
    
    # Get listening processes with memory info
    processes=$(get_listening_processes_with_memory)
    process_count=$(echo "$processes" | wc -l | tr -d ' ')
    
    # Handle empty result
    if [ "$process_count" -eq 0 ] || [ "$process_count" -eq 1 ] && [ -z "$processes" ]; then
        log_success "No server processes found"
        return 0
    fi
    
    # Adjust count if last line is empty
    if [ -z "${processes##*$'\n'}" ]; then
        process_count=$((process_count - 1))
    fi
    
    log_info "Found $process_count server process(es):"
    echo
    
    # Display table header
    printf "${PURPLE}%-5s %-12s %-25s %-10s %-10s %s${NC}\n" "ID" "PID" "NAME" "PORT" "MEMORY" "COMMAND"
    echo "----- ------------ ------------------------- ---------- ---------- --------------------------------------------------"
    
    # Display processes with numbers
    local i=1
    local pids=()
    local names=()
    local memories=()
    
    while IFS= read -r process; do
        [ -z "$process" ] && continue
        
        local pid=$(echo "$process" | cut -d'|' -f1)
        local name=$(echo "$process" | cut -d'|' -f2)
        local port=$(echo "$process" | cut -d'|' -f3)
        local memory=$(echo "$process" | cut -d'|' -f4)
        local details=$(echo "$process" | cut -d'|' -f5)
        
        # Store for later reference
        pids+=("$pid")
        names+=("$name")
        memories+=("$memory")
        
        # Truncate long fields for display
        local display_name=${name:0:12}
        local display_port=${port:0:10}
        local display_memory=${memory:0:10}
        local display_details=${details:0:50}
        
        printf "%-5s %-12s %-25s %-10s %-10s %s\n" "$i" "$pid" "$display_name" "$display_port" "$display_memory" "$display_details"
        ((i++))
    done <<< "$processes"
    
    echo
    log_info "Total processes: $process_count"
    
    # Calculate total memory usage
    local total_memory_kb=0
    for mem in "${memories[@]}"; do
        if [[ $mem != "N/A" ]]; then
            # Extract numeric part and unit
            local mem_value=$(echo "$mem" | sed 's/[^0-9.]//g')
            if [[ $mem == *"GB"* ]]; then
                total_memory_kb=$((total_memory_kb + $(echo "$mem_value * 1048576" | bc -l | cut -d'.' -f1)))
            elif [[ $mem == *"MB"* ]]; then
                total_memory_kb=$((total_memory_kb + $(echo "$mem_value * 1024" | bc -l | cut -d'.' -f1)))
            elif [[ $mem == *"KB"* ]]; then
                total_memory_kb=$((total_memory_kb + $(echo "$mem_value" | cut -d'.' -f1)))
            fi
        fi
    done
    
    if [ "$total_memory_kb" -gt 0 ]; then
        local total_formatted
        total_formatted=$(format_memory "$total_memory_kb")
        log_info "Total estimated memory usage: $total_formatted"
    fi
    
    echo
    
    # Interactive selection
    while true; do
        echo "Select action:"
        echo "  Enter number to kill a specific process"
        echo "  'a' to kill ALL processes"
        echo "  'q' to quit"
        echo -n "Choice: "
        
        read -r choice
        
        case "$choice" in
            q|Q)
                log_info "Exiting..."
                return 0
                ;;
            a|A)
                echo "Are you sure you want to kill ALL server processes? (y/N): "
                read -r confirm
                if [[ "$confirm" =~ ^[Yy]$ ]]; then
                    local killed_count=0
                    for i in "${!pids[@]}"; do
                        if kill_process "${pids[$i]}" "${names[$i]}"; then
                            ((killed_count++))
                        fi
                    done
                    log_success "Killed $killed_count/$process_count processes"
                else
                    log_info "Cancelled"
                fi
                return 0
                ;;
            ''|*[!0-9]*)
                log_warning "Invalid choice. Please enter a number, 'a', or 'q'."
                ;;
            *)
                if [ "$choice" -ge 1 ] && [ "$choice" -le "${#pids[@]}" ]; then
                    local index=$((choice - 1))
                    local pid=${pids[$index]}
                    local name=${names[$index]}
                    local memory=${memories[$index]}
                    
                    echo "Kill process $name (PID: $pid, Memory: $memory)? (y/N): "
                    read -r confirm
                    if [[ "$confirm" =~ ^[Yy]$ ]]; then
                        if ! kill_process "$pid" "$name"; then
                            echo "Try force kill? (y/N): "
                            read -r force_confirm
                            if [[ "$force_confirm" =~ ^[Yy]$ ]]; then
                                kill_process_force "$pid" "$name"
                            fi
                        fi
                    else
                        log_info "Cancelled"
                    fi
                    
                    # Refresh the list
                    echo
                    log_info "Refreshing process list..."
                    manage_servers
                    return 0
                else
                    log_warning "Invalid choice. Please enter a number between 1 and ${#pids[@]}, 'a', or 'q'."
                fi
                ;;
        esac
    done
}

# Function to show help
show_help() {
    echo "Vampire Hunter - Process Manager with Memory Usage"
    echo "================================================="
    echo "This script helps you detect and manage server processes (vampire processes) running on your machine with memory information."
    echo
    echo "Usage:"
    echo "  ./vampire_hunter.sh     # Run interactive vampire hunter"
    echo "  ./vampire_hunter.sh -h  # Show this help"
    echo
    echo "The script will:"
    echo "1. Scan for processes listening on TCP ports (vampire processes)"
    echo "2. Show memory usage for each process"
    echo "3. Present them in an interactive menu"
    echo "4. Allow you to selectively kill them"
    echo
    echo "Features:"
    echo "• Shows memory usage for each process"
    echo "• Safe process killing (SIGTERM first, then SIGKILL if needed)"
    echo "• Process details display"
    echo "• Selective or bulk killing options"
    echo "• Confirmation prompts for safety"
}

# Main function
main() {
    # Check for help flag
    if [[ "${1:-}" == "-h" ]] || [[ "${1:-}" == "--help" ]]; then
        show_help
        exit 0
    fi
    
    # Check if required commands are available
    for cmd in lsof ps bc; do
        if ! command -v "$cmd" &>/dev/null; then
            log_error "$cmd command not found. Please install $cmd to use this script."
            exit 1
        fi
    done
    
    echo -e "${GREEN}🧛 Vampire Hunter - Process Manager${NC}"
    echo "=================================="
    echo
    
    manage_servers
}

# Run main function with all arguments
main "$@"