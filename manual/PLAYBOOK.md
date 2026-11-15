# ⚔️ 24-Hour Attack & Defense CTF Master Operational Playbook

> **CRITICAL PRE-COMPETITION NOTICE: AI PROHIBITION**
> The competition rules strictly ban all AI tools (ChatGPT, Claude, Gemini, Copilot, Cursor, etc.) once the competition begins. 
> Download, review, test, and save all scripts, templates, and reference materials onto your local machine and offline repository before 10:00 AM.

---

## 1. Rules Compliance & "Red Line" Cheat Sheet

| Category | Strict Rule | Compliance Solution |
| :--- | :--- | :--- |
| **Pwnbox** | ALL actions MUST be on organizer-provided Pwnbox only. | Never run attacks or sniffers from your personal laptop or VPS. Personal laptops only act as displays or thin clients to access Pwnbox. |
| **Rate Limit / DDoS** | Min **2.0s delay** between requests per target. | Hardcode `time.sleep(2.1)` in all automated exploit loops. Never blast concurrent threads at a single target team. |
| **Sniffing** | Sniff ONLY inside your own assigned environment. | Run `tcpdump` / `tshark` strictly on your own Pwnbox/service interfaces (`eth0`, `docker0`, etc.). Never attempt network-wide promiscuous capture on the organizer switch. |
| **Recon / Scanning** | **NO port scanning or directory scanning** of other teams. | Do not use `nmap`, `masscan`, `ffuf`, or `nuclei` against other teams! The organizer already provides the service ports/IPs. Only scan `localhost` for testing. |
| **Firewall** | **NO iptables/nftables modifications or IP blocking.** | **Do not touch iptables!** Do all filtering via application code patches or L7 reverse proxies on your own services. |
| **Stability** | No service crashing / fork bombing. | Ensure your exploits exit cleanly after printing the flag. Do not delete files or drop DB tables on target teams. |

---

## 2. Team Role Distribution & 24-Hour Shift Plan

With **3 active players** and **1 substitute** (switchable only between Phase 1 and Phase 2), role clarity is essential.

- **Player 1 (Defense & Traffic Lead):** Service backups, SLA health checks, PCAP analysis, zero-firewall proxy deployment.
- **Player 2 (Exploit Engineer & Automation):** Weaponizes exploits, runs attack dispatchers (>=2.1s delay), manages flag submissions.
- **Player 3 (Vulnerability Analyst & Reverser):** Binary reverse engineering, web code audits, authoring SLA-safe patches.
- **Player 4 (Substitute & Operations Lead):** Hardware/router setup, rest schedule, food/water; **tags into the game between Phase 1 and Phase 2** to replace fatigued players with 100% fresh cognitive capacity.
