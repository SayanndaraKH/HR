import os
import sys
import subprocess

if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

PROJECT_DIR = os.path.abspath(os.path.dirname(__file__))
os.chdir(PROJECT_DIR)

GREEN = '\033[92m'
CYAN = '\033[96m'
YELLOW = '\033[93m'
RED = '\033[91m'
BOLD = '\033[1m'
RESET = '\033[0m'

def run_cmd(cmd):
    return subprocess.run(cmd, shell=True).returncode

def main():
    print(f"\n{CYAN}{BOLD}================================================================{RESET}")
    print(f"{CYAN}{BOLD}       ប្រព័ន្ធ HRMS - UPDATE / DEPLOY FROM GITHUB             {RESET}")
    print(f"{CYAN}{BOLD}================================================================{RESET}\n")

    print("[*] កំពុងទាញយកកូដចុងក្រោយបង្អស់ពី GitHub (git pull)...")
    code = run_cmd("git pull origin main")
    if code != 0:
        print(f"\n{RED}[កំហុស] មិនអាចទាញយកទិន្នន័យពី GitHub បានទេ!{RESET}\n")
        input("ចុច ENTER ដើម្បីចាកចេញ...")
        sys.exit(1)

    print("\n[*] កំពុងពិនិត្យ និងដំឡើងកញ្ចប់ Libraries (pip install)...")
    run_cmd(f'"{sys.executable}" -m pip install -r requirements.txt --quiet')

    print("\n[*] កំពុងបិទ Process ចាស់...")
    run_cmd("cmd /c stop.bat >nul 2>&1")

    print("\n[*] កំពុងដំណើរការប្រព័ន្ធឡើងវិញ...")
    run_cmd("cmd /c run.bat")

    print(f"\n{GREEN}{BOLD}================================================================{RESET}")
    print(f"{GREEN}{BOLD}   [ជោគជ័យ] ប្រព័ន្ធ HRMS ត្រូវបានធ្វើបច្ចុប្បន្នភាពរួចរាល់!      {RESET}")
    print(f"{GREEN}{BOLD}================================================================{RESET}\n")

    input("ចុច ENTER ដើម្បីបញ្ចប់...")

if __name__ == '__main__':
    main()
