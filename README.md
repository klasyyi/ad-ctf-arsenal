# AD-CTF Arsenal + S4DFarm

An operational framework for 24-hour Attack & Defense CTFs, built to run entirely
inside the organizer "Pwnbox" (Debian + a fixed toolset + Docker via `docker.sock`).
It pairs two things:

- **S4DFarm** (`s4dfarm_engine/`) — the automated exploit runner and flag submitter.
  Vendored from upstream [C4T-BuT-S4D/S4DFarm](https://github.com/C4T-BuT-S4D/S4DFarm)
  (LICENSE kept intact). This is the engine that attacks every team every tick and
  submits the flags.
- **The arsenal** (`attack/`, `defense/`, `traffic/`, `s4dfarm/`, `manual/`) — the
  exploits S4DFarm runs, plus everything S4DFarm does not do: defense, traffic
  capture, replay, and the field manuals.

Built for environments that prohibit AI tooling, firewall changes, and port
scanning, and that enforce a per-target rate limit.

---

## How it works (the loop)

One S4DFarm server runs on the shared Pwnbox. Each vulnerable service has one small
exploit script. The farm does the repetitive work: it runs each exploit against
every enemy team on every tick, collects whatever the exploit prints, deduplicates,
applies the submission quota, and submits to the scoreboard.

```text
S4DFarm server (one, shared on the Pwnbox)
│
├─ [ONCE] farm owner configures and boots it
│     server/app/config.py: TEAMS, FLAG_FORMAT, SYSTEM_PROTOCOL + token, quota
│     docker compose up --build -d   ->  web UI on http://localhost:5000
│
└─ [EVERY TICK] one branch per service, run by its owner
      s4dfarm/exploit_<service>.py   (payload only: print flag(s), exit)
          │  start_sploit.py runs it against every team from TEAMS
          ▼
      prints FLAG{...} to stdout
          │
          ▼
   SERVER: extract (FLAG_FORMAT) -> dedup -> quota -> submit -> UI stats
```

Your job as a service owner is **one exploit file and one client command**. You
never loop over teams, never retype IPs, never submit flags yourself — the farm
owns all of that.

---

## Team roles

Everyone works on the **same** Pwnbox, so roles exist to stop people stepping on
each other. Run everything in one shared tmux session (`tmux new -s ctf`, others
`tmux attach -t ctf`) with one window per role.

| Role | Owns | Responsibilities |
| --- | --- | --- |
| **Farm owner** | The S4DFarm server | Sets `TEAMS`, `FLAG_FORMAT`, protocol, quota once; boots the server; is the only person who edits server config or restarts it; watches the UI for accepted/rejected trends. |
| **Service owner** (one per service) | One `s4dfarm/exploit_<service>.py` + its client | Writes and tunes that service's exploit; starts one client for it; re-adapts when a target patches. Edits only their own files. |
| **Defense owner** (one per service you run) | Your own service's source + container | Diffs clean vs patched, applies the fix, rebuilds, keeps a known-good image, runs the WAF shim. Only this person rebuilds the service. |
| **Traffic / replay** | `traffic/` + `attack/exploit_replay.py` | Captures incoming enemy exploits, hands new exploits to service owners, fires captured exploits back at every team. |

Single-owner, shared resources: the farm server, `TEAMS`, and `FLAG_FORMAT` belong
to the farm owner only. Never run two servers, never run two clients for the same
service, never edit another person's exploit, never rebuild a service without a
shout.

---

## Repository structure

```text
ad-ctf-arsenal/
├── README.md
├── s4dfarm_engine/              # Vendored S4DFarm engine (upstream C4T-BuT-S4D/S4DFarm)
│   ├── server/                  #   farm server: web UI, dedup, quota, submission
│   │   └── app/
│   │       ├── config.py        #     TEAMS, FLAG_FORMAT, protocol, quota, password
│   │       └── protocols/       #     submission protocols (one module per scoreboard)
│   │           ├── faust.py ... volgactf.py   # shipped protocols
│   │           ├── custom.py    #     TEMPLATE: edit for a custom scoreboard
│   │           └── stub.py      #     testing: accepts all, submits nowhere
│   └── client/
│       └── start_sploit.py      #   runs one exploit against all teams each tick
├── s4dfarm/                     # Adapter: the exploits S4DFarm runs
│   ├── exploit_web.py           #   web sploit (print flags to stdout, exit)
│   ├── exploit_pwn.py           #   pwn sploit (print flags to stdout, exit)
│   ├── config.py                #   per-service ports/paths + FLAG_REGEX
│   └── INTEGRATION.md           #   full wiring notes
├── attack/
│   ├── exploit_replay.py        # Replay a captured enemy payload (manual, keep)
│   ├── submitter_daemon.py      # RETIRED under S4DFarm (standalone fallback only)
│   ├── exploit_web.py           # RETIRED round-loop version (standalone fallback)
│   ├── exploit_pwn.py           # RETIRED round-loop version (standalone fallback)
│   └── targets.txt              # Standalone target list (farm uses server TEAMS instead)
├── defense/
│   ├── backup_services.sh       # Snapshot + git-init your services
│   ├── bot_watcher.sh           # Watch the organizer SLA bot
│   ├── proxy_logger.py          # Layer 7 proxy logger (no firewall change)
│   ├── waf_python_shim.py       # Flask WAF shim (monitor by default)
│   └── waf_php_shim.php         # PHP WAF shim (monitor by default)
├── traffic/
│   ├── sniffer.py               # Packet sniffer + exploit dumper
│   └── pcap_dump.sh             # Rolling tcpdump ring buffer
└── manual/
    ├── FIRST_HOUR_CHECKLIST.md
    ├── GAME_DYNAMICS_AND_CHEATCODES.md
    ├── FIELD_MANUAL.md
    └── PLAYBOOK.md
```

---

## Setup checklist

### A. Farm server — `s4dfarm_engine/server/app/config.py` (farm owner, once)

1. `TEAMS` — the real `{name: ip}` of every target team. This is the **only** place
   team IPs go; the client reads them from here.
2. `FLAG_FORMAT` — the real flag regex from the rules.
3. `SYSTEM_PROTOCOL` — how flags reach the scoreboard. Choose one:
   - a shipped module: `faust`, `ructf_http`, `ructf_tcp`, `ctf_moscow`,
     `ctfcup_tcp`, `volgactf`;
   - `custom` — edit `server/app/protocols/custom.py` for the organizers' own
     scoreboard (see "Custom scoreboard" below);
   - `stub` — the default; accepts every flag and submits nowhere, for testing the
     pipeline before the scoreboard spec is known. **Change it before the real game.**
   Then set only the keys that protocol reads (`SYSTEM_URL` / `SYSTEM_HOST` /
   `SYSTEM_PORT` / `TEAM_TOKEN` / `SYSTEM_TOKEN`).
4. `SUBMIT_FLAG_LIMIT` / `SUBMIT_PERIOD` — the game's submission quota.
5. `FLAG_LIFETIME` — how long a flag stays valid.
6. `SERVER_PASSWORD` — change it from the default.
7. `TIMEZONE` — set to the game's timezone.

### B. Adapter — `s4dfarm/` (each service owner)

8. `s4dfarm/config.py` `FLAG_REGEX` — keep **identical** to the server `FLAG_FORMAT`.
9. Per service: set the ports/paths in `s4dfarm/config.py` and write the payload
   block in your `exploit_<service>.py`. Contract: `argv[1]` is the victim host,
   steal the flag(s), `print()` each one, exit. No loop, no submitter.

### C. Defense (each service you run)

10. Prepend the WAF shim to your service, in monitor mode first.
11. Tag a known-good Docker image once SLA is green (your fast rollback).
12. Start the sniffer and bot watcher.

---

## Important commands

### Clone and bootstrap (every teammate, on the Pwnbox)

```bash
git clone https://github.com/klasyyi/ad-ctf-arsenal.git
cd ad-ctf-arsenal
chmod +x bootstrap/setup_pwnbox.sh && ./bootstrap/setup_pwnbox.sh
source ~/.bashrc
tmux new -s ctf      # others: tmux attach -t ctf
```

### Start the farm (farm owner, once)

```bash
cd s4dfarm_engine
docker compose up --build -d
# web UI: http://localhost:5000  (log in with SERVER_PASSWORD)
```

### Run an exploit (service owner, one client per service)

```bash
python3 s4dfarm_engine/client/start_sploit.py s4dfarm/exploit_web.py \
    --server-url http://127.0.0.1:5000 --server-pass YOUR_PASS

python3 s4dfarm_engine/client/start_sploit.py s4dfarm/exploit_pwn.py \
    --server-url http://127.0.0.1:5000 --server-pass YOUR_PASS
# add --attack-period <seconds> if the tick is short
```

Quick local test of an exploit, outside the farm:

```bash
python3 s4dfarm/exploit_web.py 127.0.0.1    # should print a flag
```

### Defense

```bash
# Snapshot + git-init your services (once, first 15 minutes)
chmod +x defense/backup_services.sh && sudo ./defense/backup_services.sh

# WAF shim: monitor mode is the default (logs, never blocks).
# Watch for would-be blocks, confirm no SLA-checker traffic is caught:
tail -f /tmp/flask_waf_blocked.log       # or /tmp/php_blocked_attacks.log
# Only once the patterns are safe, enable blocking for your service:
WAF_MODE=block <start your service>

# Watch the organizer SLA bot
chmod +x defense/bot_watcher.sh && ./defense/bot_watcher.sh &
```

### Patch and roll back a service (defense owner)

```bash
# Before patching, pin the working state both ways:
git add -A && git commit -m "known-good baseline"
docker tag <service>:latest <service>:good

# Patch on a branch, one commit per change, then deploy:
git switch -c patch-<bug>
# ...edit source...
git commit -am "patch <bug>"
docker compose up -d --build

# If SLA goes red, roll the runtime back in seconds (no rebuild):
docker tag <service>:good <service>:latest
docker compose up -d --force-recreate --no-build

# Then fix in git without clock pressure:
git diff known-good..patch-<bug>
# re-tag :good when SLA is green again
```

### Traffic and replay

```bash
# Capture incoming enemy exploits
sudo python3 traffic/sniffer.py eth0 &
chmod +x traffic/pcap_dump.sh && ./traffic/pcap_dump.sh &

# Fire a captured enemy exploit back at everyone
python3 attack/exploit_replay.py traffic/captured_exploits/<file>.bin --port 8080
```

### Custom scoreboard

If the organizers run their own submission system and no shipped protocol fits,
edit the template, point the config at it, and restart:

```bash
# 1. edit the request + response parsing
nano s4dfarm_engine/server/app/protocols/custom.py
# 2. in server/app/config.py set  'SYSTEM_PROTOCOL': 'custom'  + its keys
# 3. restart the server
cd s4dfarm_engine && docker compose up --build -d
```

In any protocol, map flag verdicts carefully: `ACCEPTED` = scored, `REJECTED` =
permanently dead, `QUEUED` = transient (retried next tick). When unsure, use
`QUEUED` — a wrongly rejected flag is a lost point.

---

## Retired under S4DFarm

When S4DFarm is the exploiter and submitter, do **not** run these — they
double-submit or fight the farm:

- `attack/submitter_daemon.py`
- the round-loop `attack/exploit_web.py` / `attack/exploit_pwn.py`
  (use `s4dfarm/exploit_web.py` / `s4dfarm/exploit_pwn.py` instead)

They are kept only as a standalone fallback if the farm is unavailable.

---

## Rules compliance

- **Rate limit:** the S4DFarm client re-attacks a target only once per
  `--attack-period` (default 55s), so per-target spacing is far above any 2.1s
  minimum without any in-exploit sleep.
- **Zero firewall changes:** all defense runs at Layer 7 (application code, local
  proxies, the WAF shim).
- **Non-destructive:** exploits only read flags; they do not crash or disrupt enemy
  services.
- **Internal sniffing only:** capture is restricted to local host interfaces.

Credit for the vendored engine: upstream
[C4T-BuT-S4D/S4DFarm](https://github.com/C4T-BuT-S4D/S4DFarm).
