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

## 🔧 Step 2: Generate the Profile

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

## 📄 Report

A detailed PDF report summarizing the methodology, plugin behavior, observations, and findings is included in this repository.

---


