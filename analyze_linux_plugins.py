import subprocess
import os

# Setup
plugins = [
    "linux.pslist",
    "linux.psscan",
    "linux.bash",
    "linux.proc_maps",
    "linux.netstat",
    "linux.lsof",
    "linux.tty_check",
    "linux.lsmod",
    "linux.dmesg",
    "linux.mount"
]

symbol_dir = r"C:\Users\sanda\btf2json-android"
dump_file = r"C:\Users\sanda\memory_dumps\android_memory_du.bin"
output_dir = "plugin_outputs"

# Create output directory if it doesn't exist
os.makedirs(output_dir, exist_ok=True)

print("Running Volatility3 plugins and saving results...\n")

# Run each plugin
summary = []
for plugin in plugins:
    output_file = os.path.join(output_dir, f"{plugin}.txt")
    cmd = [
        "python", "vol.py",
        "-s", symbol_dir,
        "-f", dump_file,
        plugin
    ]
    print(f"Running {plugin}...")
    with open(output_file, "w", encoding="utf-8") as f:
        result = subprocess.run(cmd, stdout=f, stderr=subprocess.STDOUT)
    
    # Analyze output
    with open(output_file, "r", encoding="utf-8") as f:
        lines = f.readlines()
        line_count = len(lines)
        status = "✅ OK" if line_count > 5 else "⚠️ Possibly failed or empty"
        summary.append((plugin, line_count, status))

# Show summary
print("\n--- Analysis Summary ---")
for plugin, count, status in summary:
    print(f"{plugin}: {count} lines - {status}")

print(f"\nAll outputs saved in '{output_dir}' folder.")
