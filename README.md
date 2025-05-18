# Android Memory Forensics with Volatility3

This repository contains tools and documentation for testing Volatility3 Linux plugins on Android memory dumps. The project evaluates which Linux plugins work effectively on Android memory dumps and documents their limitations.

## Table of Contents

- [Overview](#overview)
- [Requirements](#requirements)
- [Installation](#installation)
- [Usage](#usage)
  - [Capturing Memory](#capturing-memory)
  - [Testing Plugins](#testing-plugins)
  - [Analyzing Results](#analyzing-results)
- [Plugin Compatibility](#plugin-compatibility)
- [Methodology](#methodology)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [License](#license)

## Overview

Android uses a modified Linux kernel with unique memory management and process handling mechanisms. While Volatility3 offers numerous plugins for analyzing Linux memory dumps, their compatibility with Android systems varies. This project systematically tests Volatility3's Linux plugins against Android memory dumps, documenting which plugins work, which fail, and what limitations exist.

## Requirements

- Python 3.6 or higher
- Volatility3 framework
- Android Studio (for emulator)
- ADB (Android Debug Bridge)
- Expect (for QEMU monitor scripting)
- Matplotlib and Pandas (for visualization)

## Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/yourusername/android-memory-forensics.git
   cd android-memory-forensics
   ```

2. Install Volatility3:
   ```bash
   git clone https://github.com/volatilityfoundation/volatility3.git
   cd volatility3
   pip install -e .
   cd ..
   ```

3. Install dependencies:
   ```bash
   pip install matplotlib pandas
   ```

4. Make the scripts executable:
   ```bash
   chmod +x capture_memory.sh test_volatility_plugins.sh analyze_results.py
   ```

## Usage

### Capturing Memory

1. Set up the Android emulator:
   - Open Android Studio
   - Go to Tools > Device Manager
   - Create a new virtual device (preferably x86 architecture)
   - Start the emulator

2. Capture memory using the capture script:
   ```bash
   ./capture_memory.sh -e <emulator_name> -m qemu
   ```

   Options:
   - `-e <emulator_name>`: Name of the Android emulator (required)
   - `-p <port>`: QEMU monitor port (default: 5555)
   - `-o <output_dir>`: Directory to save memory dumps (default: memory_dumps)
   - `-n <dump_name>`: Name of the memory dump file (default: android_memory_dump.bin)
   - `-m <method>`: Capture method: qemu or adb (default: qemu)

### Testing Plugins

1. Test all Volatility3 Linux plugins against your memory dump:
   ```bash
   ./test_volatility_plugins.sh -f memory_dumps/android_memory_dump.bin -a
   ```

   Options:
   - `-f <memory_dump>`: Path to the memory dump file (required)
   - `-o <output_dir>`: Directory to store results (default: plugin_results)
   - `-p <plugin>`: Test a specific plugin only (e.g., pslist)
   - `-a`: Test all plugins

2. Test a specific plugin:
   ```bash
   ./test_volatility_plugins.sh -f memory_dumps/android_memory_dump.bin -p pslist
   ```

### Analyzing Results

1. Analyze test results and generate visualizations:
   ```bash
   ./analyze_results.py plugin_results -o plugin_compatibility.png
   ```

   Options:
   - `results_dir`: Directory containing test results (required)
   - `-o, --output`: Output file for visualization (default: plugin_compatibility.png)
   - `-c, --csv`: Output results as CSV file

## Plugin Compatibility

Based on our testing, the compatibility of Volatility3 Linux plugins with Android memory dumps is as follows:

| Plugin | Status | Notes/Limitations |
|--------|--------|-------------------|
| pslist | Partial | Process names are truncated due to Android's unique process naming conventions |
| psscan | Fails | Unable to identify processes in Android memory structure |
| proc_maps | Works | Successfully shows memory mappings for processes |
| bash | Fails | Not applicable as Android doesn't use bash shell by default |
| check_modules | Works | Shows loaded kernel modules |
| dmesg | Works | Retrieves kernel messages buffer |
| lsmod | Works | Lists loaded kernel modules |
| lsof | Partial | Shows some open files but misses Android-specific file descriptors |
| netstat | Partial | Shows some network connections but misses socket information specific to Android |
| psaux | Fails | Not compatible with Android process structure |
| pstree | Partial | Shows process hierarchy but with truncated names |
| tty_check | Fails | Not applicable to Android environment |
| vma_maps | Works | Shows virtual memory areas for processes |

## Methodology

Our testing methodology includes:

1. **Environment Setup**:
   - Using Android emulator with x86 architecture
   - Android version 10-13 for broader compatibility
   - 4GB RAM allocation

2. **Memory Dump Acquisition**:
   - QEMU Monitor method for raw memory dumps
   - ADB snapshot method as an alternative

3. **Plugin Testing**:
   - Automated testing with timeout limits
   - Systematic evaluation of output quality
   - Documentation of errors and limitations

4. **Result Analysis**:
   - Categorization of plugins by compatibility
   - Visualization of results
   - Documentation of Android-specific memory structure differences

## Troubleshooting

### Common Issues

1. **Error: No emulator is running**
   - Start the emulator from Android Studio or command line
   - Ensure the emulator name matches what's provided in the command

2. **Plugin fails with "Unable to find valid kernel DTB"**
   - This is expected for some plugins as Android's kernel structure differs from standard Linux

3. **QEMU monitor connection fails**
   - Verify the QEMU monitor port (default: 5555)
   - Check if another process is using the port

4. **Memory dump is very large**
   - This is normal for full system dumps
   - Consider using the `-m adb` method for smaller files

## Contributing

Contributions are welcome! Please feel free to submit pull requests or open issues to improve the project.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
