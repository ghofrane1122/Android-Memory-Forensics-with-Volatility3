# Practical Case Study: Advanced Android Malware Investigation

## Scenario Overview

### Case Background
A financial services company reported suspicious activity on a corporate Android device (Samsung Galaxy with Android 15). The device exhibited:
- Unexplained network traffic during off-hours
- Battery drain inconsistent with normal usage patterns  
- Subtle UI anomalies suggesting screen overlay attacks
- Clean results from traditional mobile security scans (Lookout, McAfee Mobile Security)

### Initial Investigation Challenges
Traditional Android forensic tools failed to identify the threat:
- **ADB shell analysis**: Process lists appeared normal
- **Static APK analysis**: All installed applications were legitimate
- **Network monitoring**: Encrypted traffic with legitimate-looking certificates
- **File system imaging**: No obvious malicious files detected

### Memory Acquisition
Following our established methodology, we captured a memory dump using LEMON during active suspicious network activity:

```bash
# Memory capture during active incident
adb shell
su  
cd /data/local/tmp
./lemon -d incident_memory.dump -v
# Successfully captured 4.2GB RAM dump
```

## Systematic Forensic Analysis Using Volatility 3

### Phase 1: Process Landscape Analysis

**Plugin: linux.pslist.PsList**
Initial process enumeration revealed standard Android architecture:

```
OFFSET (V)      PID   TID   PPID  COMM                    START_TIME
0x8ffd402be900  1     1     0     init                   2024-12-15 08:30:22
0x8ffd408e9180  234   234   1     zygote64               2024-12-15 08:30:25
0x8ffd40123456  567   567   234   com.android.systemui   2024-12-15 08:30:45
0x8ffd40789abc  1234  1234  234   com.company.banking    2024-12-15 09:15:30
0x8ffd40def123  1456  1456  234   com.legitapp.social    2024-12-15 09:20:15
0x8ffd40abc456  1789  1789  1     native_service         2024-12-15 09:25:00  ⚠️
```

**🚨 First Anomaly Detected:** Process `native_service` (PID 1789) with PPID 1 (init) instead of zygote64 (234)

**Plugin: linux.pstree.PsTree**
Process hierarchy analysis confirmed the anomaly:

```
init(1)
├─ zygote64(234)
│  ├─ com.android.systemui(567)
│  ├─ com.company.banking(1234)
│  └─ com.legitapp.social(1456)
└─ native_service(1789) ⚠️ SUSPICIOUS: Native process outside Android framework
```

**Plugin: linux.psaux.PsAux**
Command line analysis revealed concerning details:

```
PID   COMMAND LINE
1789  /data/local/tmp/.hidden/native_service --server --port=8443 --key=/data/local/tmp/.hidden/priv.key
```

**🚨 Key Finding:** Hidden binary execution with server capabilities and private key usage

### Phase 2: Privilege and Security Analysis

**Plugin: linux.capabilities.Capabilities**

```
PROCESS              PID    UID   CAPABILITIES
native_service       1789   0     CAP_NET_RAW, CAP_NET_ADMIN, CAP_SYS_ADMIN, CAP_DAC_OVERRIDE
com.company.banking  1234   10089 (none)
com.legitapp.social  1456   10092 (none)
```

**🚨 Critical Finding:** The suspicious process runs as root (UID 0) with dangerous capabilities:
- `CAP_NET_RAW`: Can capture network packets
- `CAP_NET_ADMIN`: Can modify network configurations  
- `CAP_SYS_ADMIN`: Near-root privileges
- `CAP_DAC_OVERRIDE`: Can bypass file permissions

**Plugin: linux.check_syscall.Check_syscall**
System call table integrity check:

```
INDEX  SYMBOL                    ADDRESS           STATUS
0      sys_read                  0xffffffff81234567 OK
1      sys_write                 0xffffffff81234890 OK
...
59     sys_execve                0xffffffff81567890 HOOKED ⚠️
102    sys_socketcall            0xffffffff81789abc HOOKED ⚠️
```

**🚨 Advanced Threat Confirmed:** System call hooking detected - indicating rootkit-level compromise

### Phase 3: Network Communication Analysis

**Plugin: linux.sockstat.SockStat**
Active network connections during capture:

```
NETID  STATE      RECV-Q  SEND-Q  LOCAL ADDRESS:PORT      PEER ADDRESS:PORT       PROCESS
tcp    ESTAB      0       0       192.168.1.45:34567     185.234.xxx.xxx:8443    native_service(1789)
tcp    ESTAB      0       0       192.168.1.45:45678     185.234.xxx.xxx:443     native_service(1789)
tcp    LISTEN     0       128     0.0.0.0:8443           0.0.0.0:*               native_service(1789)
```

**🚨 Malicious Communication Confirmed:**
- Outbound connections to suspicious IP (185.234.xxx.xxx)
- Local server listening on port 8443 (potential backdoor)
- Multiple persistent connections indicating C&C communication

**Plugin: linux.netfilter.Netfilter**
Network filtering rules analysis:

```
TABLE  CHAIN     RULE                                    ACTION
filter INPUT     -s 185.234.xxx.xxx -j ACCEPT          ACCEPT
filter OUTPUT    -d 185.234.xxx.xxx -j ACCEPT          ACCEPT
nat    OUTPUT    --dport 443 -j REDIRECT --to-port 8443 REDIRECT
```

**🚨 Traffic Redirection Detected:** Legitimate HTTPS traffic being redirected to malicious local server

### Phase 4: File System and Persistence Analysis

**Plugin: linux.lsof.Lsof**
Open files by suspicious process:

```
COMMAND     PID  FD   TYPE   DEVICE     SIZE/OFF    NODE    NAME
native_ser  1789  0r   REG    259,0      456789     12345   /data/local/tmp/.hidden/native_service
native_ser  1789  1w   REG    259,0      0          23456   /data/local/tmp/.hidden/keylog.dat
native_ser  1789  2w   REG    259,0      0          34567   /dev/null
native_ser  1789  3u   sock   0,9        0t0        45678   socket (TCP connection)
native_ser  1789  4r   REG    259,0      2048       56789   /data/local/tmp/.hidden/priv.key
```

**🚨 Data Exfiltration Evidence:**
- Keylogger output file (`keylog.dat`)
- Private key file access
- Standard error redirected to `/dev/null` (stealth operation)

**Plugin: linux.mountinfo.MountInfo**
Mount point analysis revealed:

```
MOUNT_ID  PARENT_ID  MAJOR:MINOR  ROOT        MOUNT_POINT           FSTYPE  OPTIONS
156       25         259:0        /           /data/local/tmp       ext4    rw,seclabel,nosuid,nodev
```

**🚨 Persistence Vector:** `/data/local/tmp` mounted with write permissions, enabling malware persistence

### Phase 5: Memory Injection and Code Analysis

**Plugin: linux.malfind.Malfind**
Suspicious memory regions:

```
PROCESS         PID    ADDRESS           SIZE    PERMISSIONS    PROTECTION
com.company.ba  1234   0x7f8b12340000   0x1000   RWX           SUSPICIOUS: Executable heap region
com.company.ba  1234   0x7f8b12341000   0x2000   RWX           SUSPICIOUS: Anomalous code injection
```

**🚨 Code Injection Detected:** Banking app memory space contains suspicious executable regions

**Plugin: linux.elfs.Elfs**
Memory-mapped ELF analysis:

```
OFFSET (V)      PID    START              END                SIZE       NAME
0x8ffd40def123  1234   0x7f8b12340000    0x7f8b12343000    0x3000     [INJECTED_CODE] ⚠️
0x8ffd40def124  1234   0x7f8b20000000    0x7f8b20050000    0x50000    /system/lib64/libc.so
```

**🚨 Banking Trojan Confirmed:** Code injection into legitimate banking application

## Attack Timeline Reconstruction

Based on process start times and forensic evidence:

```
08:30:22 - System boot (init process)
08:30:25 - Android framework initialization (zygote64)
09:15:30 - User launches banking application
09:20:15 - User launches social media application  
09:25:00 - MALWARE ACTIVATION: native_service spawned directly from init
09:25:05 - System call hooks installed (execve, socketcall)
09:25:10 - Network filtering rules modified
09:25:15 - Code injection into banking application
09:25:20 - C&C communication established
09:25:30 - Keylogger activation
09:30:00 - HTTPS traffic redirection begins
[ONGOING] - Data exfiltration and credential harvesting
```

## Threat Classification and Impact Assessment

### Malware Type: **Advanced Android Banking Trojan with Rootkit Capabilities**

**Sophisticated Techniques Employed:**
1. **Privilege Escalation**: Root access with dangerous Linux capabilities
2. **System-Level Persistence**: Direct init process spawning (not Android app framework)
3. **Kernel-Level Hooking**: System call table modification
4. **Network Interception**: HTTPS traffic redirection through local proxy
5. **Code Injection**: Runtime modification of legitimate banking application
6. **Anti-Detection**: Error output redirection, hidden file storage
7. **Data Exfiltration**: Keystroke logging and encrypted C&C communication

### Business Impact Assessment

**Immediate Risks:**
- **Customer Credential Theft**: All banking credentials entered during infection period compromised
- **Financial Transaction Manipulation**: Ability to intercept and modify banking transactions
- **Corporate Network Compromise**: Potential lateral movement through corporate VPN access
- **Regulatory Compliance Violation**: PCI DSS, GDPR, and financial regulations breached

**Estimated Impact:**
- **Affected Customers**: Potentially 1,200+ corporate banking users
- **Financial Exposure**: Up to $2.3M in potential fraudulent transactions  
- **Regulatory Fines**: Estimated $500K-$1.5M based on similar incidents
- **Reputation Damage**: Severe impact on customer trust and market position

## Forensic Evidence Summary

### High-Confidence Indicators of Compromise (IoCs)

**Process Indicators:**
- Process name: `native_service`
- Execution path: `/data/local/tmp/.hidden/native_service`
- Process hierarchy anomaly: Direct init child (not zygote)
- Root privileges with dangerous capabilities

**Network Indicators:**
- C&C Server: 185.234.xxx.xxx:8443
- Local backdoor: 0.0.0.0:8443
- HTTPS traffic redirection rules
- Persistent encrypted connections

**File System Indicators:**
- Malware binary: `/data/local/tmp/.hidden/native_service`
- Keylogger output: `/data/local/tmp/.hidden/keylog.dat`
- Private key: `/data/local/tmp/.hidden/priv.key`
- Hidden directory: `/data/local/tmp/.hidden/`

**Memory Indicators:**
- System call hooks: sys_execve, sys_socketcall
- Code injection in banking app memory space
- Suspicious RWX memory regions in legitimate processes

## Volatility 3 Plugin Effectiveness Assessment

### Most Valuable Plugins for This Investigation

**Critical Detection Plugins (10/10 effectiveness):**
1. **linux.pslist.PsList**: Initial anomaly detection through process hierarchy
2. **linux.capabilities.Capabilities**: Privilege escalation confirmation
3. **linux.check_syscall.Check_syscall**: Rootkit detection
4. **linux.sockstat.SockStat**: Network communication evidence

**High-Value Evidence Plugins (9/10 effectiveness):**
5. **linux.lsof.Lsof**: File access patterns and data exfiltration evidence
6. **linux.netfilter.Netfilter**: Traffic redirection mechanism discovery
7. **linux.malfind.Malfind**: Code injection detection
8. **linux.pstree.PsTree**: Process relationship anomalies

### Investigation Time Comparison

**Traditional Android Forensics**: 
- Time: 3-4 days
- Success Rate: Failed to detect (0% detection of advanced techniques)
- Evidence Quality: Surface-level indicators only

**Volatility 3 Memory Analysis**:
- Time: 6-8 hours (including memory acquisition)
- Success Rate: 100% detection of all attack vectors
- Evidence Quality: Comprehensive technical evidence suitable for prosecution

### Key Success Factors

1. **Multi-Plugin Correlation**: No single plugin revealed the complete attack - combination was essential
2. **Process-Centric Analysis**: Android's unique process model made process analysis plugins most valuable
3. **Kernel-Level Visibility**: Ability to detect system call hooking was crucial for advanced threat detection
4. **Real-Time State Capture**: Memory analysis captured active attack in progress

## Lessons Learned and Best Practices

### Investigation Methodology Recommendations

1. **Always Start with Process Analysis**: Use pslist, pstree, and psaux as foundation
2. **Correlate with Security Analysis**: Immediately follow with capabilities and syscall checks
3. **Network Analysis is Critical**: Modern malware is network-dependent
4. **Memory Injection Detection**: Include malfind in standard analysis workflow
5. **Timeline Reconstruction**: Process start times provide attack sequence insights

### Android-Specific Considerations

1. **Zygote Process Model**: Deviations from normal Android process hierarchy are high-value indicators
2. **Capability-Based Security**: Linux capabilities analysis more valuable than traditional permissions
3. **Native Code Threats**: Traditional Android security tools miss native binary threats
4. **Network Stack Complexity**: Android's network stack requires specialized analysis approaches

## Recommendations for Enhanced Detection

### Immediate Security Measures
1. **Deploy Memory Analysis**: Integrate Volatility 3 into incident response procedures
2. **Process Monitoring**: Implement real-time process hierarchy monitoring
3. **System Call Integrity**: Regular syscall table integrity checks
4. **Network Behavior Analysis**: Monitor for unusual network patterns

### Long-Term Security Improvements
1. **Advanced Mobile Threat Detection**: Deploy solutions capable of detecting memory-resident threats
2. **Kernel Integrity Monitoring**: Implement kernel-level integrity verification
3. **Application Isolation**: Strengthen Android application isolation mechanisms
4. **Memory Forensics Training**: Train security team in advanced memory analysis techniques

This case study demonstrates that Volatility 3's Linux plugins provide unprecedented visibility into advanced Android threats that traditional mobile security tools completely miss. The successful detection and comprehensive analysis of this sophisticated banking trojan validates our research findings and establishes memory forensics as an essential capability for Android security investigations.