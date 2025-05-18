#!/bin/bash

# capture_memory.sh - Script to capture memory from an Android emulator
# This script provides two methods to capture memory:
# 1. QEMU Monitor Method
# 2. ADB snapshot method

# Configuration
EMULATOR_NAME=""
QEMU_PORT="5555"
OUTPUT_DIR="memory_dumps"
DUMP_NAME="android_memory_dump.bin"

# Function to display help
show_help() {
    echo "Android Memory Capture Tool"
    echo ""
    echo "Usage: $0 -e <emulator_name> [-p <port>] [-o <output_dir>] [-n <dump_name>] [-m <method>]"
    echo ""
    echo "Options:"
    echo "  -e <emulator_name>  Name of the Android emulator (required)"
    echo "  -p <port>           QEMU monitor port (default: 5555)"
    echo "  -o <output_dir>     Directory to save memory dumps (default: memory_dumps)"
    echo "  -n <dump_name>      Name of the memory dump file (default: android_memory_dump.bin)"
    echo "  -m <method>         Capture method: qemu or adb (default: qemu)"
    echo "  -h                  Show this help message"
    echo ""
    echo "Example:"
    echo "  $0 -e Pixel_5_API_30 -m qemu"
    echo "  $0 -e Pixel_5_API_30 -m adb -o ~/dumps"
    echo ""
}

# Function to check if the emulator is running
check_emulator() {
    local emulator_name=$1
    adb devices | grep -q "emulator"
    if [ $? -ne 0 ]; then
        echo "[-] Error: No emulator is running."
        echo "    Please start the emulator first with:"
        echo "    emulator -avd $emulator_name -qemu -monitor telnet:localhost:$QEMU_PORT,server,nowait"
        exit 1
    fi
    echo "[+] Emulator is running."
}

# Function to capture memory using QEMU monitor
capture_memory_qemu() {
    echo "[*] Capturing memory using QEMU monitor method..."
    echo "[*] Connecting to QEMU monitor on port $QEMU_PORT..."
    
    # Create expect script for telnet automation
    EXPECT_SCRIPT=$(mktemp)
    cat > $EXPECT_SCRIPT <<EOL
#!/usr/bin/expect
set timeout 600
spawn telnet localhost $QEMU_PORT
expect "QEMU"
send "dump-guest-memory $OUTPUT_DIR/$DUMP_NAME\r"
expect {
    "100%" { puts "Memory dump completed successfully" }
    timeout { puts "Memory dump timed out"; exit 1 }
}
send "quit\r"
expect eof
EOL
    
    # Run expect script
    chmod +x $EXPECT_SCRIPT
    expect -f $EXPECT_SCRIPT
    rm $EXPECT_SCRIPT
    
    if [ -f "$OUTPUT_DIR/$DUMP_NAME" ]; then
        echo "[+] Memory dump created: $OUTPUT_DIR/$DUMP_NAME"
        echo "[+] File size: $(du -h $OUTPUT_DIR/$DUMP_NAME | cut -f1)"
    else
        echo "[-] Failed to create memory dump"
        exit 1
    fi
}

# Function to capture memory using ADB snapshot
capture_memory_adb() {
    echo "[*] Capturing memory using ADB snapshot method..."
    
    # Check if ADB can access the emulator
    adb devices | grep -q "emulator"
    if [ $? -ne 0 ]; then
        echo "[-] Error: Cannot access emulator via ADB"
        exit 1
    fi
    
    # Create avd.snapshot.pull command
    echo "[*] Creating memory snapshot via ADB..."
    adb emu avd snapshot save memsnap
    
    if [ $? -ne 0 ]; then
        echo "[-] Error: Failed to create memory snapshot"
        exit 1
    fi
    
    # Find the AVD home directory
    AVD_HOME="$HOME/.android/avd/${EMULATOR_NAME}.avd"
    
    if [ ! -d "$AVD_HOME" ]; then
        echo "[-] Error: AVD home directory not found: $AVD_HOME"
        exit 1
    fi
    
    # Copy the snapshot memory file
    SNAPSHOT_PATH="$AVD_HOME/snapshots/memsnap/memory.bin"
    
    if [ -f "$SNAPSHOT_PATH" ]; then
        echo "[*] Copying memory snapshot to output directory..."
        cp "$SNAPSHOT_PATH" "$OUTPUT_DIR/$DUMP_NAME"
        
        if [ $? -eq 0 ]; then
            echo "[+] Memory dump created: $OUTPUT_DIR/$DUMP_NAME"
            echo "[+] File size: $(du -h $OUTPUT_DIR/$DUMP_NAME | cut -f1)"
        else
            echo "[-] Error: Failed to copy memory snapshot file"
            exit 1
        fi
    else
        echo "[-] Error: Memory snapshot file not found: $SNAPSHOT_PATH"
        exit 1
    fi
}

# Parse command line arguments
while getopts "e:p:o:n:m:h" opt; do
    case $opt in
        e)
            EMULATOR_NAME="$OPTARG"
            ;;
        p)
            QEMU_PORT="$OPTARG"
            ;;
        o)
            OUTPUT_DIR="$OPTARG"
            ;;
        n)
            DUMP_NAME="$OPTARG"
            ;;
        m)
            CAPTURE_METHOD="$OPTARG"
            ;;
        h)
            show_help
            exit 0
            ;;
        \?)
            echo "Invalid option: -$OPTARG" >&2
            show_help
            exit 1
            ;;
    esac
done

# Check if emulator name is provided
if [ -z "$EMULATOR_NAME" ]; then
    echo "Error: Emulator name is required"
    show_help
    exit 1
fi

# Create output directory
mkdir -p "$OUTPUT_DIR"
echo "[+] Output directory: $OUTPUT_DIR"

# Check if emulator is running
check_emulator "$EMULATOR_NAME"

# Capture memory based on selected method
if [ "$CAPTURE_METHOD" = "adb" ]; then
    capture_memory_adb
else
    # Default to QEMU method
    capture_memory_qemu
fi

echo "[+] Memory capture completed"
echo "[*] You can now analyze this memory dump with Volatility3"
echo "[*] Example command: python3 -m volatility3 -f $OUTPUT_DIR/$DUMP_NAME linux.pslist"
exit 0