# Arsenal + S4DFarm

Run S4DFarm as the farm (exploit runner + flag submitter) and keep the arsenal
for everything S4DFarm doesn't do: defense, traffic analysis, replay.

## Layout

- `s4dfarm_engine/` = the S4DFarm engine itself (server + client), vendored
  straight into the repo. This is the folder with `server/` and `client/`.
  (Its upstream is github.com/C4T-BuT-S4D/S4DFarm; LICENSE kept intact.)
- `s4dfarm/` = your adapter layer: service-specific exploits + config + this doc.

One clone gets everything, nothing extra to fetch.

## What changes

- Your exploits now **print flags to stdout** and exit. S4DFarm's client runs
  each one against every team per tick; the server dedups, applies the quota,
  and submits.
- **Retire these from standalone mode when using S4DFarm** (don't run them, they
  double-submit or fight the farm):
  - `attack/submitter_daemon.py`
  - the round-loop `attack/exploit_web.py` / `attack/exploit_pwn.py`
    (use `s4dfarm/exploit_web.py` / `s4dfarm/exploit_pwn.py` instead)
- **Keep running from the arsenal** (no conflict): `defense/*`,
  `traffic/sniffer.py` + `pcap_dump.sh`, and `attack/exploit_replay.py` (manual).

## 1. Configure the S4DFarm server

Edit `s4dfarm_engine/server/app/config.py`:

- `TEAMS` = `{name: ip}` for every target (your `attack/targets.txt`).
- `FLAG_FORMAT` = the real flag regex from the rules. Keep `s4dfarm/config.py`'s
  `FLAG_REGEX` identical.
- Submission protocol: set `SYSTEM_PROTOCOL` to the one your scoreboard uses, plus
  its host/port/token fields. Shipped protocols (in
  `s4dfarm_engine/server/app/protocols/`): `faust`, `ructf_http`, `ructf_tcp`,
  `ctf_moscow`, `ctfcup_tcp`, `volgactf`. If yours isn't one of these, copy the
  closest and adapt the submit call to the scoreboard's actual spec (confirm it
  on match day).
- `SUBMIT_FLAG_LIMIT` / `SUBMIT_PERIOD` = the game's submission quota.
- `FLAG_LIFETIME` = flag validity window.
- `SERVER_PASSWORD` = change it.

Start it:
```
cd s4dfarm_engine
docker compose up --build -d
```
Web UI (flags + per-exploit/per-team stats) on `http://localhost:5000`, log in
with `SERVER_PASSWORD`.

## 2. Point the sploits at the server

Edit `s4dfarm/config.py` ports/paths and each sploit's payload block, then run
one client per service:

```
python3 s4dfarm_engine/client/start_sploit.py s4dfarm/exploit_web.py \
    --server-url http://SERVER_IP:5000 --server-pass YOUR_PASS

python3 s4dfarm_engine/client/start_sploit.py s4dfarm/exploit_pwn.py \
    --server-url http://SERVER_IP:5000 --server-pass YOUR_PASS
```

Each client loops over all teams from the server's `TEAMS`. Flags the sploit
prints show up in the web UI and get submitted automatically.

## 3. Rate limit (your 2.1s/target rule)

Each sploit run makes **one request per target**, and the client re-attacks a
target only once per `--attack-period` (default 55s). So per-target spacing is
~55s, far above 2.1s, no in-exploit `sleep` needed. If a tick is very short,
raise `--attack-period`; keep `--pool-size` modest if you're nervous about
concurrency across targets.

## Why this over the arsenal's submitter

S4DFarm's server handles **flag-spam and quota**: it groups flags and submits a
uniform mix, so an enemy stuffing fake flags into their service can't starve
your real ones out of the quota. The arsenal's `submitter_daemon.py` submits
FIFO with no quota awareness and marks transient-error flags as processed
(never retried). S4DFarm also gives the per-exploit accepted/rejected dashboard,
so you see which exploit is landing and who patched you.
