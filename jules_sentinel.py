
import subprocess
import time


def notify_architect(msg):
    # Windows Toast Notification via PowerShell
    powershell_cmd = f'[num.Reflection.Assembly]::LoadWithPartialName("System.Windows.Forms"); [System.Windows.Forms.MessageBox]::Show("{msg}", "Jules Sentinel")'
    subprocess.run(["powershell", "-Command", powershell_cmd], capture_output=True)

def check_jules():
    try:
        result = subprocess.run(["jules", "remote", "list", "--session"], capture_output=True, text=True)
        output = result.stdout
        # Logic: If we see "In Progress", "Planning", or "Awaiting User", Jules is not done.
        # But specifically look for the sessions we know are active.
        active_keywords = ["In Progress", "Planning", "Awaiting User"]
        is_active = any(kw in output for kw in active_keywords)
        return not is_active, output
    except Exception as e:
        return False, str(e)

def main():
    print("SENTINEL: Resonance Bridge Established. Monitoring Jules...")
    while True:
        is_done, raw_output = check_jules()
        if is_done:
            print("\n" + "="*60)
            print("!!! JULES HAS COMPLETED THE TESTING BLITZ !!!")
            print("="*60 + "\n")

            # Create physical marker
            with open("JULES_READY.txt", "w") as f:
                f.write(f"Jules completed all sessions at {time.ctime()}\n")
                f.write(raw_output)

            # Desktop Notification
            notify_architect("Jules has finished the Testing Blitz! Resonance is 100%.")
            break

        time.sleep(60) # Peer through the telescope every minute

if __name__ == "__main__":
    main()
