# Android Memory Forensics with Volatility3

This repository contains tools and documentation for testing Volatility3 Linux plugins on Android memory dumps. The project evaluates which Linux plugins work effectively on Android memory dumps and documents their limitations. We also provide a detailed PDF report of the analysis, which will be included in this repository.

---

## Prerequisites

- Rust (to build btf2json)
- ADB installed and added to PATH
- Android Emulator installed and running
- Git
- Python 3 + Virtualenv
- Volatility 3 cloned from: https://github.com/volatilityfoundation/volatility3
- [`lemon.x86_64`](https://github.com/eurecom-s3/lemon/releases) binary downloaded

---

## Step 1: Capture the Memory Dump with LEMON

### 1.1 Push lemon.x86_64 binary

```bash
adb root
adb remount
adb push lemon.x86_64 /data/local/tmp/lemon
adb shell chmod +x /data/local/tmp/lemon
```

### 1.2 Dump memory

```bash
adb shell
su
cd /data/local/tmp
./lemon -d memory_on_disk.dump
```

Then pull the file:

```bash
adb pull /data/local/tmp/memory_on_disk.dump memory.bin
```

### 1.3 Pull the dump to your host machine

```bash
adb pull /data/local/tmp/memory_on_disk.dump <your_path>/android_memory_dump.bin
```

---

## Step 2: Generate the Profile

### 2.1 Clone the required `btf2json` tool

```bash
git clone https://github.com/CaptWake/btf2json.git
cd btf2json
cargo build --release
```

### 2.2 Extract required files from emulator

Enter the Android shell:

```bash
adb shell
su
cd /data/local/tmp
echo 0 > /proc/sys/kernel/kptr_restrict
cat /proc/kallsyms > kallsyms
cat /sys/kernel/btf/vmlinux > btf_symb
exit
```

Pull the files:

```bash
adb pull /data/local/tmp/kallsyms ./btf2json
adb pull /data/local/tmp/btf_symb ./btf2json
```

### 2.3 Get the banner from memory

Inside the `volatility3` directory:

```bash
python vol.py -f memory.bin banner
```

Pick the **full banner string** from the output.

### 2.4 Generate the profile

```bash
./target/release/btf2json --map kallsyms --btf btf_symb --banner "your_full_banner_string_here" > profile.json
```

### 2.5 Convert the profile to UTF-8

```powershell
$content = Get-Content profile.json -Encoding Unicode
$content | Out-File profile_utf8.json -Encoding UTF8 -NoNewline

python -c "
import json
with open('profile_utf8.json', 'r', encoding='utf-8-sig') as f:
    data = json.load(f)
with open('profile_clean.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2)
print('BOM removed successfully!')
"
```

### 2.6 Patch the clean profile

Place `patch_profile.py` in the same directory and run:

```bash
python patch_profile.py -f profile_clean.json
```

### 2.7 Patch Volatility3 Schema

Inside `volatility3`:

```bash
git apply new-json-schema.patch
```

---

##  Step 3: Analyze with Volatility 3

### 3.1 Setup environment inside `volatility3` (we should be in volatility3 folder)

```bash
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install --upgrade pip
pip install .
```

### 3.2 Run a test plugin

```bash
python vol.py -s path/to/profile_clean.json -f path/to/android_memory_dump.bin linux.pslist
```

### 3.3 Run all plugins

Adjust paths in `analyze_linux_plugins.py`, then run:

```bash
python analyze_linux_plugins.py
```
---

### How the Plugin Analysis Script Works

The `analyze_linux_plugins.py` script automates the execution of **all Linux plugins** available in Volatility 3 on your Android memory dump.

Here’s what the script does:

1.  **Loads the full list of Linux plugins** from Volatility 3.
2.  **Sets paths** to your memory dump and symbol profile (generated using `btf2json`).
3. **Creates an output directory** (`plugin_outputs`) to store results.
4.  **Loops through each plugin** and runs it using:
   ```bash
   python vol.py -s <path_to_profile> -f <path_to_dump> <plugin_name>
```
### Analyzes the output:
Status:
1. ✅ OK – plugin worked and returned useful output
2. ⚠️ Possibly empty or unusable – plugin ran but returned very little
3. ❌ Failed: Requirement missing – plugin couldn’t run due to unresolved symbols or missing requirements
4. 📁 Saves each plugin’s output into a file under the plugin_outputs/ folder using a safe filename format, like:

After running the script, you can explore all plugin results directly in the plugin_outputs/ folder — this is exactly how we manually analyzed each plugin during the project.
This automation helped us test and document plugin compatibility one by one, and the data from this process fed directly into our final report.

---

## ✅ Plugin Compatibility Table

| Plugin                         | Status | Notes / Limitations |
|--------------------------------|--------|----------------------|
| `pslist`                       | ✅     | Fully functional; 65 processes detected |
| `psscan`                       | ✅     | Detects hidden/terminated processes |
| `proc_maps` (`proc.Maps`)      | ✅     | Rich virtual memory mapping data |
| `bash`                         | ✅     | Minimal data; Android doesn’t use bash by default |
| `check_modules` (`lsmod`)      | ✅     | 50+ Android-specific kernel modules detected |
| `dmesg` (`kmsg`)               | ✅     | Extracts kernel messages (1,225 lines) |
| `lsmod`                        | ✅     | See `check_modules` |
| `lsof`                         | ✅     | Parsed file descriptors successfully |
| `netstat` (`sockstat`)         | ✅     | Socket activity and network info shown |
| `psaux`                        | ✅     | Process command-line arguments recovered |
| `pstree`                       | ✅     | Android zygote hierarchy confirmed |
| `tty_check` (`check_creds`)    | ✅     | Minimal data; basic credential structures present |
| `vma_maps` (`proc.Maps`)       | ✅     | Memory regions per process mapped |
| `fbdev`                        | ❌     | Failed – missing framebuffer symbol |
| `boottime`                     | ❌     | Failed – missing `timekeeper` symbol |
| `library_list`                 | ❌     | Timeout – possibly due to profile/symbol complexity |
| `recoverfs`                    | ❌     | Failed – plugin type error |
| `hidden_modules`               | ❌     | Failed – symbol format incompatibility |
| `keyboard_notifiers`          | ❌     | Failed – structure not present in Android kernel |
| `check_ftrace`                 | ✅     | Minimal output; symbol partially resolved |

> *Note: Some plugins executed successfully but returned limited data due to Android’s architecture. For example, `bash`, `malfind`, and `check_creds` may be of low value unless the device is rooted or uses traditional Linux shells.*

---

## Want to Try It Yourself?

You’ll find everything you need in this [Google Drive folder]([https://your-drive-link-here](https://drive.google.com/drive/folders/1igTvN26OEXcU2gCMnaY_mSRzVTkO5KFl?usp=sharing)).

It contains four folders:

- **`volatility3`**, **`memory_dump`**, and **`btf2json-android`** — These are the exact working directories we used during the project. You can download them and directly run the analysis using the same commands we documented.
- **`starter_pack`** — This folder includes only the essential files: our memory dump and the generated Volatility 3 profile. If you're looking for a quick start, just place these files into the appropriate directories as described at the beginning of this README and begin your Android memory forensics journey.

---

## Android Case Study

**Real-world forensic investigation** of a sophisticated Android banking that evaded traditional mobile security tools. Demonstrates how memory forensics with Volatility 3 successfully detected and analyzed advanced threats.
**File**: `android-banking-trojan-case-study.md`  
**Focus**: Advanced Android malware detection using memory forensics  
**Tools**: Volatility 3, LEMON memory acquisition, Linux forensics plugins


---

## 📄 Report

A detailed PDF report summarizing the methodology, plugin behavior, observations, and findings is included in this repository.

---


