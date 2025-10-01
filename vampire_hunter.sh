#!/bin/bash

# Vampire Hunter - Enhanced Process Manager with Memory Usage
# Detects and interactively allows killing of server processes with memory info

set -euo pipefail

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
ORANGE='\033[0;33m'
CYAN='\033[0;36m'
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

log_vampire() {
    echo -e "${ORANGE}🧛 $*${NC}"
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

# Function to get system memory information
get_system_memory_info() {
    if command -v vm_stat &>/dev/null; then
        # On macOS
        local vmstat_output
        vmstat_output=$(vm_stat 2>/dev/null)
        
        # Extract values
        local pages_free=$(echo "$vmstat_output" | grep "Pages free:" | awk '{print $3}' | tr -d '.')
        local pages_active=$(echo "$vmstat_output" | grep "Pages active:" | awk '{print $3}' | tr -d '.')
        local pages_inactive=$(echo "$vmstat_output" | grep "Pages inactive:" | awk '{print $3}' | tr -d '.')
        local pages_wired=$(echo "$vmstat_output" | grep "Pages wired down:" | awk '{print $4}' | tr -d '.')
        local pages_compressed=$(echo "$vmstat_output" | grep "Pages stored in compressor:" | awk '{print $5}' | tr -d '.')
        
        # Calculate in MB (16384 bytes per page on macOS)
        local page_size=16384
        local mb_factor=$((1024 * 1024))
        
        # Export values for later use
        export SYSTEM_FREE_MB=$(echo "scale=1; $pages_free * $page_size / $mb_factor" | bc -l)
        export SYSTEM_ACTIVE_MB=$(echo "scale=1; $pages_active * $page_size / $mb_factor" | bc -l)
        export SYSTEM_INACTIVE_MB=$(echo "scale=1; $pages_inactive * $page_size / $mb_factor" | bc -l)
        export SYSTEM_WIRED_MB=$(echo "scale=1; $pages_wired * $page_size / $mb_factor" | bc -l)
        export SYSTEM_COMPRESSED_MB=$(echo "scale=1; $pages_compressed * $page_size / $mb_factor" | bc -l)
    fi
}

# Function to get Node.js processes
get_node_processes() {
    local ps_output
    ps_output=$(ps aux | grep node | grep -v grep 2>/dev/null || true)
    
    if [ -z "$ps_output" ]; then
        return
    fi
    
    while IFS= read -r line; do
        [ -z "$line" ] && continue
        
        local user=$(echo "$line" | awk '{print $1}')
        local pid=$(echo "$line" | awk '{print $2}')
        local cpu_percent=$(echo "$line" | awk '{print $3}')
        local mem_percent=$(echo "$line" | awk '{print $4}')
        local vsz=$(echo "$line" | awk '{print $5}')  # Virtual size in KB
        local rss=$(echo "$line" | awk '{print $6}')  # RSS in KB
        local command=$(echo "$line" | cut -d' ' -f11-)
        
        # Classify as development or system based on command
        local process_type="system"
        if [[ $command == *"mcp-server"* || $command == *"hybrowser"* || $command == *"stagehand"* || $command == *"ollama"* || $command == *"qwen"* || $command == *".js"* || $command == *"server"* || $command == *"app"* || $command == *"index"* || $command == *"main"* ]]; then
            process_type="development"
        fi
        
        echo "$user|$pid|$cpu_percent|$mem_percent|$vsz|$rss|$process_type|$command"
    done <<< "$ps_output"
}

# Function to display memory health report
display_memory_health() {
    echo
    echo -e "${CYAN}📊 System Memory Health Report${NC}"
    echo "=================================================="
    
    # Get system memory info
    get_system_memory_info
    
    # Display system memory info
    if [ -n "${SYSTEM_FREE_MB:-}" ]; then
        echo -e "${BLUE}System Memory:${NC}"
        echo "  Free: ${SYSTEM_FREE_MB} MB"
        echo "  Active: ${SYSTEM_ACTIVE_MB} MB"
        echo "  Inactive: ${SYSTEM_INACTIVE_MB} MB"
        echo "  Wired: ${SYSTEM_WIRED_MB} MB"
        echo "  Compressed: ${SYSTEM_COMPRESSED_MB} MB"
    fi
    
    # Get and display Node.js processes
    local node_processes
    node_processes=$(get_node_processes)
    
    if [ -n "$node_processes" ]; then
        local node_count=$(echo "$node_processes" | wc -l | tr -d ' ')
        local total_node_memory=0
        
        # Calculate total Node.js memory
        while IFS= read -r node_line; do
            [ -z "$node_line" ] && continue
            local rss=$(echo "$node_line" | cut -d'|' -f6)
            total_node_memory=$((total_node_memory + rss))
        done <<< "$node_processes"
        
        echo -e "\n${GREEN}Node.js Processes:${NC}"
        echo "Total Node.js processes: $node_count"
        echo "Total Node.js memory usage: $(format_memory $total_node_memory)"
        
        # Display top Node.js processes
        echo -e "\n${YELLOW}Top Node.js Processes by Memory Usage:${NC}"
        echo "PID     CPU%   Mem%   RSS      Type         Command"
        echo "------- ------ ------ -------- ------------ --------------------------------------------------"
        
        # Sort by RSS (memory usage) and show top 10
        echo "$node_processes" | sort -t'|' -k6 -nr | head -10 | while IFS='|' read -r user pid cpu mem vsz rss type command; do
            local rss_formatted=$(format_memory $rss)
            local display_command=${command:0:50}
            printf "%-7s %-6s %-6s %-8s %-12s %s\n" "$pid" "$cpu" "$mem" "$rss_formatted" "$type" "$display_command"
        done
    else
        echo -e "\n${GREEN}Node.js Processes:${NC}"
        echo "No Node.js processes found"
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
        echo "  'm' to show memory health"
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
            m|M)
                display_memory_health
                ;;
            ''|*[!0-9]*)
                log_warning "Invalid choice. Please enter a number, 'a', 'm', or 'q'."
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
                    log_warning "Invalid choice. Please enter a number between 1 and ${#pids[@]}, 'a', 'm', or 'q'."
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
    echo "3. Analyze Node.js processes and memory usage"
    echo "4. Present them in an interactive menu"
    echo "5. Allow you to selectively kill them"
    echo
    echo "Features:"
    echo "• Shows memory usage for each process"
    echo "• Safe process killing (SIGTERM first, then SIGKILL if needed)"
    echo "• Process details display"
    echo "• Selective or bulk killing options"
    echo "• Memory health report with Node.js analysis"
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
    for cmd in lsof ps bc vm_stat; do
        if ! command -v "$cmd" &>/dev/null; then
            log_error "$cmd command not found. Please install $cmd to use this script."
            exit 1
        fi
    done
    
    echo -e "${GREEN}🧛 Vampire Hunter - Process Manager${NC}"
    echo "=================================="
    echo
    
    # Show initial memory health
    display_memory_health
    
    manage_servers
}

# Run main function with all arguments
main "$@"