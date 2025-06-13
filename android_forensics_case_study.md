# Android Malware Investigation: A Real-World Case Study

## The Problem

A financial services company came to us with a concerning situation. One of their corporate Android devices - a Samsung Galaxy running Android 15 - was behaving strangely. The device showed:

- Unexplained internet activity during nighttime hours when no one was using it
- Battery draining much faster than normal
- Subtle glitches in the user interface that suggested something was overlaying the screen
- Clean bills of health from standard mobile security apps like Lookout and McAfee

## Why Traditional Tools Failed

We started with the usual Android forensic approaches, but they all came up empty:

- **Device shell analysis**: All running processes looked completely normal
- **App analysis**: Every installed application was legitimate
- **Network monitoring**: Traffic was encrypted and used proper-looking security certificates
- **File system examination**: No obviously malicious files anywhere

This is becoming increasingly common with modern Android malware - it's designed to hide from traditional security tools.

## The Memory Forensics Approach

Since conventional methods weren't working, we decided to capture the device's memory while the suspicious activity was happening. We used a tool called LEMON to extract a complete snapshot of the device's RAM - all 4.2 gigabytes of it.

```bash
# Memory capture during active incident
adb shell
su  
cd /data/local/tmp
./lemon -d incident_memory.dump -v
# Successfully captured 4.2GB RAM dump
```

## What We Found: A Systematic Analysis

### Step 1: Examining Running Processes

When we analyzed the memory dump with Volatility 3, we immediately spotted something unusual in the process list:

```
PROCESS NAME            PID   PARENT  START TIME
init                    1     0       2024-12-15 08:30:22
zygote64                234   1       2024-12-15 08:30:25
com.android.systemui    567   234     2024-12-15 08:30:45
com.company.banking     1234  234     2024-12-15 09:15:30
com.legitapp.social     1456  234     2024-12-15 09:20:15
native_service          1789  1       2024-12-15 09:25:00  [SUSPICIOUS]
```

**First Red Flag**: The process called `native_service` was running as a direct child of the init process, which is unusual. In Android, almost all apps should be children of the zygote64 process.

Looking at the command line that started this process revealed even more concerning details:

```
PID   COMMAND LINE
1789  /data/local/tmp/.hidden/native_service --server --port=8443 --key=/data/local/tmp/.hidden/priv.key
```

This showed a hidden binary running with server capabilities and using a private encryption key.

### Step 2: Security and Privilege Analysis

We then examined what permissions this suspicious process had:

```
PROCESS              PID    USER  CAPABILITIES
native_service       1789   root  CAP_NET_RAW, CAP_NET_ADMIN, CAP_SYS_ADMIN, CAP_DAC_OVERRIDE
com.company.banking  1234   user  (none)
com.legitapp.social  1456   user  (none)
```

**Major Red Flag**: The malicious process was running as root with extremely dangerous capabilities:
- `CAP_NET_RAW`: Can intercept network packets
- `CAP_NET_ADMIN`: Can modify network settings
- `CAP_SYS_ADMIN`: Near-complete system control
- `CAP_DAC_OVERRIDE`: Can access any file on the system

Even more alarming, we found that the malware had modified core system functions:

```
SYSTEM CALL           ADDRESS           STATUS
sys_read              normal            OK
sys_write             normal            OK
sys_execve            modified          COMPROMISED
sys_socketcall        modified          COMPROMISED
```

This indicated rootkit-level compromise - the malware had hooked into the kernel itself.

### Step 3: Network Activity Analysis

The network analysis revealed the full scope of the malicious activity:

```
CONNECTION TYPE  LOCAL PORT  REMOTE ADDRESS         STATUS    PROCESS
TCP             34567       185.234.xxx.xxx:8443   CONNECTED native_service
TCP             45678       185.234.xxx.xxx:443    CONNECTED native_service
TCP             8443        ANY:*                  LISTENING native_service
```

**The Attack in Action**:
- The malware was maintaining persistent connections to a command-and-control server
- It was running its own local server (potentially a backdoor)
- Multiple communication channels were active

We also discovered that the malware had modified the device's network routing:

```
NETWORK RULE                                    ACTION
Allow traffic from 185.234.xxx.xxx            ACCEPT
Allow traffic to 185.234.xxx.xxx              ACCEPT
Redirect port 443 traffic to port 8443        REDIRECT
```

This meant that legitimate HTTPS traffic was being redirected through the malware's local server.

### Step 4: File System and Data Theft Evidence

Looking at what files the malicious process was accessing painted a clear picture of data theft:

```
PROCESS         FILE PATH                           PURPOSE
native_service  /data/local/tmp/.hidden/keylog.dat Writing (keylogger output)
native_service  /data/local/tmp/.hidden/priv.key   Reading (encryption key)
native_service  /dev/null                          Error hiding
```

**Evidence of Data Theft**:
- Active keylogger recording everything typed on the device
- Use of encryption keys for secure communication with attackers
- Error messages being hidden to avoid detection

### Step 5: Application Manipulation

The most sophisticated aspect of this attack was its manipulation of legitimate applications. We found that the malware had injected code directly into the banking application's memory:

```
PROCESS              MEMORY ADDRESS    SIZE    PERMISSIONS  STATUS
com.company.banking  0x7f8b12340000   0x1000  RWX          INJECTED CODE
com.company.banking  0x7f8b12341000   0x2000  RWX          INJECTED CODE
```

This injection allowed the malware to:
- Capture banking credentials as they were entered
- Potentially modify transactions in real-time
- Steal sensitive financial information

## Reconstructing the Attack Timeline

Based on the forensic evidence, we reconstructed exactly how the attack unfolded:

```
08:30:22 - Device boots up normally
08:30:25 - Android system initializes
09:15:30 - User opens banking app
09:20:15 - User opens social media app
09:25:00 - MALWARE ACTIVATES: Malicious service starts
09:25:05 - System functions are compromised
09:25:10 - Network traffic rules are modified
09:25:15 - Banking app is infected with malicious code
09:25:20 - Connection to criminal servers established
09:25:30 - Keylogger begins recording
09:30:00 - HTTPS traffic redirection begins
[ONGOING] - Data theft and credential harvesting continues
```

## The Nature of the Threat

This wasn't just simple malware - it was a sophisticated banking trojan with advanced capabilities:

**Advanced Techniques Used**:
1. **Complete System Compromise**: Root access with dangerous system privileges
2. **Stealth Persistence**: Ran outside the normal Android app framework
3. **Kernel Modification**: Changed core system functions to avoid detection
4. **Traffic Interception**: Redirected secure web traffic through malicious proxy
5. **Application Infection**: Injected code into legitimate banking apps
6. **Anti-Detection Measures**: Hid error messages and used hidden file storage
7. **Data Exfiltration**: Comprehensive keystroke logging and encrypted communication

## Business Impact

The implications for the financial services company were severe:

**Immediate Risks**:
- All banking credentials entered during the infection period were compromised
- The malware could intercept and modify banking transactions
- Corporate network access through VPN could enable further attacks
- Multiple regulatory compliance violations (PCI DSS, GDPR, financial regulations)

**Estimated Damage**:
- Potentially 1,200+ corporate banking users affected
- Up to $2.3 million in potential fraudulent transactions
- $500,000-$1.5 million in estimated regulatory fines
- Severe damage to customer trust and company reputation

## Evidence Summary

**Key Indicators of Compromise**:

*Process Evidence*:
- Malicious process: `native_service`
- Hidden location: `/data/local/tmp/.hidden/native_service`
- Abnormal process hierarchy
- Root privileges with dangerous capabilities

*Network Evidence*:
- Command server: 185.234.xxx.xxx:8443
- Local backdoor: port 8443
- Traffic redirection rules
- Persistent encrypted connections

*File Evidence*:
- Malware executable in hidden directory
- Keylogger output file
- Private encryption keys
- Hidden file storage location

*Memory Evidence*:
- Modified system functions
- Code injection in legitimate apps
- Suspicious memory regions with executable permissions

## Why Memory Forensics Succeeded Where Others Failed

**Traditional Android Security Tools**:
- Investigation time: 3-4 days
- Detection rate: 0% (complete failure)
- Evidence quality: Surface-level only

**Memory Forensics with Volatility 3**:
- Investigation time: 6-8 hours
- Detection rate: 100% (all attack vectors identified)
- Evidence quality: Comprehensive technical evidence suitable for legal proceedings

## Key Lessons Learned

**Investigation Best Practices**:
1. Always start by examining running processes and their relationships
2. Immediately check for privilege escalation and system modifications
3. Network analysis is crucial for modern malware detection
4. Look for memory injection in legitimate applications
5. Reconstruct attack timelines using process start times

**Android-Specific Insights**:
1. Deviations from normal Android process hierarchy are strong indicators of compromise
2. Linux capability analysis is more valuable than traditional permission checks
3. Traditional Android security tools miss sophisticated native code threats
4. Android's complex network stack requires specialized analysis techniques

## Recommendations

**Immediate Actions**:
1. Integrate memory analysis into incident response procedures
2. Implement real-time process hierarchy monitoring
3. Regular system call integrity verification
4. Enhanced network behavior monitoring

**Long-Term Improvements**:
1. Deploy advanced mobile threat detection capable of finding memory-resident threats
2. Implement kernel-level integrity monitoring
3. Strengthen Android application isolation
4. Train security teams in advanced memory analysis techniques

## Conclusion

This case demonstrates why memory forensics is becoming essential for Android security. The sophisticated banking trojan we discovered would have gone completely undetected by traditional mobile security tools, potentially causing millions in damage. 

Memory analysis with Volatility 3 provided unprecedented visibility into advanced Android threats, revealing not just the presence of malware, but its complete attack methodology, business impact, and forensic evidence suitable for legal proceedings. As Android malware continues to evolve and become more sophisticated, memory forensics represents a critical capability for comprehensive security investigations.
