import os
import sys
import subprocess
from datetime import datetime

# Set console output encoding to utf-8
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

REPO_URL = "https://github.com/SayanndaraKH/HR.git"
PROJECT_DIR = os.path.abspath(os.path.dirname(__file__))
os.chdir(PROJECT_DIR)

# ANSI Color codes
GREEN = '\033[92m'
CYAN = '\033[96m'
YELLOW = '\033[93m'
RED = '\033[91m'
BOLD = '\033[1m'
RESET = '\033[0m'

def run_cmd(cmd, check=False, capture=False):
    """Run a shell command safely"""
    if capture:
        res = subprocess.run(cmd, shell=True, text=True, capture_output=True, encoding='utf-8', errors='replace')
        return res.returncode, res.stdout.strip(), res.stderr.strip()
    else:
        res = subprocess.run(cmd, shell=True)
        return res.returncode

def main():
    print(f"\n{CYAN}{BOLD}================================================================{RESET}")
    print(f"{CYAN}{BOLD}         ប្រព័ន្ធ HRMS - PUSH UPDATE TO GITHUB                {RESET}")
    print(f"{CYAN}{BOLD}================================================================{RESET}")
    print(f"Repository: {YELLOW}{REPO_URL}{RESET}\n")

    # 1. Check if git is installed
    code, out, _ = run_cmd("git --version", capture=True)
    if code != 0:
        print(f"{RED}[កំហុស / ERROR] រកមិនឃើញកម្មវិធី Git ក្នុងកុំព្យូទ័រនេះទេ!{RESET}")
        print("សូមដំឡើង Git ពី https://git-scm.com/downloads រួចសាកល្បងម្តងទៀត។\n")
        input("ចុច ENTER ដើម្បីចាកចេញ...")
        sys.exit(1)

    # 2. Check if .git exists
    if not os.path.exists(os.path.join(PROJECT_DIR, '.git')):
        print(f"[*] កំពុងចាប់ផ្តើម Git Repository (git init)...")
        run_cmd("git init -b main")

    # 3. Ensure remote origin is set
    code, remotes, _ = run_cmd("git remote", capture=True)
    if 'origin' not in remotes.split():
        print(f"[*] កំពុងភ្ជាប់ Remote Origin ({REPO_URL})...")
        run_cmd(f'git remote add origin "{REPO_URL}"')
    else:
        run_cmd(f'git remote set-url origin "{REPO_URL}"')

    # Ensure branch is main
    run_cmd("git branch -M main")

    # 4. Show changed files
    print(f"{CYAN}----------------------------------------------------------------{RESET}")
    print(f"{BOLD}បញ្ជីឯកសារដែលមានការផ្លាស់ប្តូរ (Changed Files):{RESET}")
    print(f"{CYAN}----------------------------------------------------------------{RESET}")
    code, status_out, _ = run_cmd("git status -s", capture=True)
    if not status_out:
        print(f"{YELLOW}គ្មានការកែប្រែថ្មីទេ (Working tree clean).{RESET}")
        print(f"{CYAN}----------------------------------------------------------------{RESET}\n")
        repush = input("តើលោកអ្នកចង់ Push ឯកសារចុងក្រោយទៅ GitHub ម្តងទៀតទេ? (y/n) [n]: ").strip().lower()
        if repush != 'y':
            print(f"\n{GREEN}រួចរាល់! មិនមានអ្វីត្រូវ Push ទេ។{RESET}\n")
            input("ចុច ENTER ដើម្បីបញ្ចប់...")
            sys.exit(0)
    else:
        print(status_out)
        print(f"{CYAN}----------------------------------------------------------------{RESET}\n")

    # 5. Prompt for commit message
    default_msg = f"Update HRMS System - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    print(f"សារលំនាំដើម៖ {CYAN}{default_msg}{RESET}")
    try:
        user_msg = input("សូមបញ្ចូលសារពិពណ៌នា (Commit Message) [ចុច ENTER យកស្វ័យប្រវត្តិ]: ").strip()
    except (EOFError, KeyboardInterrupt):
        user_msg = ""
    commit_msg = user_msg if user_msg else default_msg

    # 6. Stage & Commit
    print(f"\n[*] កំពុងរៀបចំឯកសារ (git add .)...")
    run_cmd("git add .")

    print(f"[*] កំពុងកត់ត្រាការផ្លាស់ប្តូរ (git commit)...")
    run_cmd(f'git commit -m "{commit_msg}"')

    # 7. Push
    print(f"\n[*] កំពុង Push ទៅកាន់ GitHub ({REPO_URL})...")
    code = run_cmd("git push origin main")
    if code != 0:
        print(f"\n{YELLOW}[!] កំពុងទាញយកទិន្នន័យពី Remote មកបញ្ចូលគ្នា (git pull --rebase)...{RESET}")
        run_cmd("git pull --rebase origin main")
        print(f"[*] កំពុង Push ម្តងទៀត...")
        code = run_cmd("git push origin main")

    if code == 0:
        print(f"\n{GREEN}{BOLD}================================================================{RESET}")
        print(f"{GREEN}{BOLD}   [ជោគជ័យ / SUCCESS] ទិន្នន័យត្រូវបាន Push ទៅ GitHub រួចរាល់! {RESET}")
        print(f"{GREEN}   ចូលមើលកូដ៖ https://github.com/SayanndaraKH/HR{RESET}")
        print(f"{GREEN}{BOLD}================================================================{RESET}\n")
    else:
        print(f"\n{RED}{BOLD}================================================================{RESET}")
        print(f"{RED}{BOLD}   [បរាជ័យ / FAILED] មិនអាច Push បានទេ!                       {RESET}")
        print(f"{RED}   សូមពិនិត្យមើលសិទ្ធិ (GitHub Login / Authentication) របស់លោកអ្នក។ {RESET}")
        print(f"{RED}{BOLD}================================================================{RESET}\n")

    input("ចុច ENTER ដើម្បីបញ្ចប់...")

if __name__ == '__main__':
    main()
