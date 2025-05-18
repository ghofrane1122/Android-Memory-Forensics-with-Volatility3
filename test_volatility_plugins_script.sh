#!/bin/bash
# Android Memory Forensics Project - Testing Script
# This script automates testing of Volatility3 plugins on Android memory dumps

# Configuration - modify these variables
MEMORY_DUMP_PATH="/path/to/your/android_memory.dump"
OUTPUT_DIR="./plugin_results"
VOLATILITY_CMD="python -m volatility3.volshell"

# Create output directory if it doesn't exist
mkdir -p $OUTPUT_DIR

# Function to run a plugin and save its output
run_plugin() {
    local plugin_name=$1
    echo "Testing plugin: $plugin_name"
    echo "------------------------"
    
    # Create a log file for this plugin
    local log_file="$OUTPUT_DIR/${plugin_name}_results.txt"
    
    # Run the plugin and capture both output and error
    echo "Running $plugin_name on $(date)" > $log_file
    echo "Command: $VOLATILITY_CMD -f $MEMORY_DUMP_PATH linux.$plugin_name" >> $log_file
    echo "------------------------" >> $log_file
    
    # Run the command with timeout (some plugins might hang)
    timeout 300s $VOLATILITY_CMD -f $MEMORY_DUMP_PATH linux.$plugin_name >> $log_file 2>&1
    
    # Check if the command timed out or failed
    if [ $? -eq 124 ]; then
        echo "WARNING: Plugin $plugin_name timed out after 5 minutes" >> $log_file
        echo "Plugin $plugin_name: TIMED OUT"
    elif [ $? -ne 0 ]; then
        echo "Plugin $plugin_name: FAILED"
    else
        echo "Plugin $plugin_name: COMPLETED"
    fi
    echo ""
}

# List of Linux plugins to test
plugins=(
    "pslist"
    "psscan"
    "proc_maps"
    "bash"
    "check_modules"
    "dmesg"
    "dump_map"
    "elfs"
    "lsmod"
    "lsof"
    "memmap"
    "mountinfo"
    "netstat"
    "proc_maps"
    "psaux"
    "pstree"
    "tty_check"
    "vma_maps"
)

echo "=== Android Memory Forensics - Volatility3 Plugin Testing ==="
echo "Memory Dump: $MEMORY_DUMP_PATH"
echo "Results Directory: $OUTPUT_DIR"
echo "================================================="

# First, check if volatility can recognize the file
echo "Verifying memory dump file format..."
$VOLATILITY_CMD -f $MEMORY_DUMP_PATH banners

# Run each plugin and save results
for plugin in "${plugins[@]}"; do
    run_plugin $plugin
done

# Create a summary report
echo "Creating summary report..."
summary_file="$OUTPUT_DIR/summary_report.txt"
echo "VOLATILITY3 PLUGIN TEST SUMMARY" > $summary_file
echo "Generated on: $(date)" >> $summary_file
echo "Memory Dump: $MEMORY_DUMP_PATH" >> $summary_file
echo "------------------------------------------------" >> $summary_file
echo "" >> $summary_file

# Check each result file for success indicators
for plugin in "${plugins[@]}"; do
    result_file="$OUTPUT_DIR/${plugin}_results.txt"
    if grep -q "TIMED OUT" $result_file; then
        echo "Plugin $plugin: TIMED OUT" >> $summary_file
    elif grep -q "Error" $result_file || grep -q "Exception" $result_file; then
        echo "Plugin $plugin: FAILED - See log for details" >> $summary_file
    elif [ -s $result_file ]; then
        echo "Plugin $plugin: SUCCESS - Produced output" >> $summary_file
    else
        echo "Plugin $plugin: UNKNOWN - No clear output" >> $summary_file
    fi
done

echo ""
echo "Testing complete! Summary available at: $summary_file"
