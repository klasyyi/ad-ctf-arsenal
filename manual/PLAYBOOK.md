# 24-Hour Attack & Defense CTF Operational Playbook

Rules compliance, team alignment, and operational protocols.

---

## 1. Rules Compliance Summary

| Category | Rule | Action |
| :--- | :--- | :--- |
| Environment | Pwnbox only | All testing, tools, attacks, and sniffing run inside Pwnbox. Laptops act as thin displays only. |
| AI Usage | Strictly prohibited | No AI tools, extensions, copilot, or AI queries during the 24 hours. |
| Throttling | Minimum 2.0s delay | Hardcode `time.sleep(2.1)` in all automated loops. |
| Traffic | Local capture only | Capture strictly on assigned Pwnbox interfaces (`eth0`, `docker0`). |
| Enumeration | No target scanning | Do not run nmap, masscan, or ffuf against competing teams. |
| Firewall | No iptables modifications | All filtering must occur at Layer 7 (application code or local proxy). |
| Service Integrity | No crashing enemy services | Exploits must only read flags and exit cleanly. |

---

## 2. Team Roles & Substitutions

- Lineup: 3 active players, 1 substitute.
- Substitutions allowed only between Phase 1 and Phase 2.
- Player 4 (Substitute) cannot communicate with active players while a phase is in progress.
- Strategy: Player 4 enters Phase 2 rested to take over overnight operations.

---

## 3. Physical Setup Checklist

- 1x Gigabit network switch or router (WAN on DHCP, pre-configured LAN).
- 4x Ethernet cables (Cat6, labeled).
- 1x Multi-plug power extension board (4+ outlets).
- 1x USB flash drive with offline repo copy and documentation.
