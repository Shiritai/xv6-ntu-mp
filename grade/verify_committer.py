
import os
import subprocess
import sys
import json
import re

def load_config():
    """Reads TA_EMAILS from conf/mp.conf"""
    config_path = os.path.join(os.path.dirname(__file__), '../mp.conf')
    ta_emails = set()
    
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            for line in f:
                if line.startswith('TA_EMAILS='):
                    # Extract content inside quotes
                    match = re.search(r'TA_EMAILS="(.*)"', line)
                    if match:
                        emails = match.group(1).split()
                        ta_emails.update(emails)
    return ta_emails

def get_commits():
    """Returns a list of commits with format: HASH|EMAIL|TIMESTAMP|PARENTS"""
    # %H: Commit hash
    # %ce: Committer email
    # %ct: Committer timestamp (Unix epoch)
    # %P: Parent hashes
    cmd = ["git", "log", "--format=%H|%ce|%ct|%P"]
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    commits = []
    for line in result.stdout.strip().split('\n'):
        if not line: continue
        parts = line.split('|')
        commits.append({
            'hash': parts[0],
            'email': parts[1],
            'timestamp': int(parts[2]),
            'parents': parts[3].split() if len(parts) > 3 else []
        })
    return commits

def find_student_commit(commits, ta_emails):
    """
    Finds the latest commit that is NOT from a TA.
    Simple strategy: Iterate from newest to oldest. 
    If a commit is by a TA, skip it.
    If a commit is a Merge Commit (2+ parents), check if it brings in student changes.
    (For simplicity in V0, we assume the Merge Commit itself is the target if authored by student,
     or we look for the first non-TA ancestor).
    """
    for commit in commits:
        if commit['email'] not in ta_emails and commit['parents']:
            return commit
    return None

def main():
    try:
        ta_emails = load_config()
        print(f"Loaded TA Emails: {ta_emails}", file=sys.stderr)
        
        commits = get_commits()
        target = find_student_commit(commits, ta_emails)
        
        if target:
            print(f"Found Target Student Commit: {target['hash']} by {target['email']}")
            # Output for GitHub Actions
            if "GITHUB_OUTPUT" in os.environ:
                with open(os.environ["GITHUB_OUTPUT"], "a") as f:
                    f.write(f"target_sha={target['hash']}\n")
                    f.write(f"target_timestamp={target['timestamp']}\n")
                    f.write(f"target_author={target['email']}\n")
            
            # Write to a JSON snippet for report inclusion
            with open("target_commit.json", "w") as f:
                json.dump({
                    "sha": target['hash'],
                    "author": target['email'],
                    "timestamp": target['timestamp']
                }, f)
                
            sys.exit(0)
        else:
            print("Error: No valid student commit found (All commits are from TA).")
            # In production, this might imply score 0 or failure
            sys.exit(1)
            
    except Exception as e:
        print(f"Verification Failed: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
