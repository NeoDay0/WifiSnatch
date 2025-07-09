![wifisnatcher](https://github.com/user-attachments/assets/25ff7c74-7884-4e11-921d-cea507080c95)


# WifiSnatch
⚠️ **Warning**: This tool is intended for **educational** and **authorized security testing** purposes only. **Do not** use it on any network without **explicit, written permission**. Unauthorized use is **illegal**.
**WifiSnatch** is an advanced wireless auditing tool built with Python. It allows ethical hackers and penetration testers to:

- Scan for WiFi networks
- Capture WPA/WPA2 handshakes
- Perform deauthentication attacks
- Crack captured handshakes using a wordlist

All actions are logged for accountability.

---

## ✨ Features

- Interface selection
- WiFi network discovery using `nmcli`
- Monitor mode setup via `airmon-ng`
- WPA handshake capture via `airodump-ng`
- Deauth attacks via `aireplay-ng`
- Password cracking via `aircrack-ng`
- Action logging to a persistent logfile


---

## ✅ Requirements

- Python 3.x
- Root privileges (`sudo`)
- Tools:
  - `airmon-ng`
  - `airodump-ng`
  - `aireplay-ng`
  - `aircrack-ng`
  - `nmcli`
  - `iw`

These are usually included in **aircrack-ng** and **NetworkManager** packages.

---

## 🚀 Usage

```bash
sudo pySelect your wireless interface

Choose a WiFi target from the scan

Choose an action:

    [1] Capture Handshake

    [2] Deauthentication Attack

    [3] Crack Captured Handshake

    [4] Exitthon3 WifiSnatch

🔐 Legal & Ethical Notice

This tool is for authorized penetration testing only. Always ensure you have documented permission before running any scans or attacks. Misuse may result in criminal charges.
