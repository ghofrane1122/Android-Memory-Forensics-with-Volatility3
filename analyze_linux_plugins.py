import subprocess
import os

# Full list of Linux plugins based on --help output
plugins = [
    "linux.bash.Bash",
    "linux.boottime.Boottime",
    "linux.capabilities.Capabilities",
    "linux.check_afinfo.Check_afinfo",
    "linux.check_creds.Check_creds",
    "linux.check_idt.Check_idt",
    "linux.check_modules.Check_modules",
    "linux.check_syscall.Check_syscall",
    "linux.ebpf.EBPF",
    "linux.elfs.Elfs",
    "linux.envars.Envars",
    "linux.graphics.fbdev.Fbdev",
    "linux.hidden_modules.Hidden_modules",
    "linux.iomem.IOMem",
    "linux.ip.Addr",
    "linux.ip.Link",
    "linux.kallsyms.Kallsyms",
    "linux.keyboard_notifiers.Keyboard_notifiers",
    "linux.kmsg.Kmsg",
    "linux.kthreads.Kthreads",
    "linux.library_list.LibraryList",
    "linux.lsmod.Lsmod",
    "linux.lsof.Lsof",
    "linux.malfind.Malfind",
    "linux.module_extract.ModuleExtract",
    "linux.modxview.Modxview",
    "linux.mountinfo.MountInfo",
    "linux.netfilter.Netfilter",
    "linux.pagecache.Files",
    "linux.pagecache.InodePages",
    "linux.pagecache.RecoverFs",
    "linux.pidhashtable.PIDHashTable",
    "linux.proc.Maps",
    "linux.psaux.PsAux",
    "linux.pscallstack.PsCallStack",
    "linux.pslist.PsList",
    "linux.psscan.PsScan",
    "linux.pstree.PsTree",
    "linux.ptrace.Ptrace",
    "linux.sockstat.Sockstat",
    "linux.tracing.ftrace.CheckFtrace",
    "linux.tracing.perf_events.PerfEvents",
    "linux.tracing.tracepoints.CheckTracepoints",
    "linux.tty_check.tty_check",
    "linux.vmaregexscan.VmaRegExScan",
    "linux.vmcoreinfo.VMCoreInfo"
]

# Setup paths
symbol_dir = r"{You should put your path here}\btf2json-android"
dump_file = r"{You should put your path here}\android_memory_du.bin"
output_dir = "plugin_outputs"

# Create output directory
os.makedirs(output_dir, exist_ok=True)

print("Running Volatility3 plugins and saving results...\n")

summary = []
for plugin in plugins:
    # Clean file name (remove dots)
    file_safe_name = plugin.replace(".", "_")
    output_file = os.path.join(output_dir, f"{file_safe_name}.txt")
    
    cmd = [
        "python", "vol.py",
        "-s", symbol_dir,
        "-f", dump_file,
        plugin
    ]
    print(f"Running {plugin}...")
    with open(output_file, "w", encoding="utf-8") as f:
        result = subprocess.run(cmd, stdout=f, stderr=subprocess.STDOUT)
    
    # Read back output to evaluate
    with open(output_file, "r", encoding="utf-8") as f:
        lines = f.readlines()
        line_count = len(lines)
        if "Unsatisfied requirement" in ''.join(lines):
            status = "❌ Failed: Requirement missing"
        elif line_count < 5:
            status = "⚠️ Possibly empty or unusable"
        else:
            status = "✅ OK"
        summary.append((plugin, line_count, status))

# Summary output
print("\n--- Analysis Summary ---")
for plugin, count, status in summary:
    print(f"{plugin:<45} {count:>5} lines - {status}")

print(f"\n✅ All plugin outputs saved in '{output_dir}'")