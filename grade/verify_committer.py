
import os
import subprocess
import sys
import json
import re
import datetime
import urllib.request

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

def _iso_to_epoch(iso):
    """Parse a GitHub ISO-8601 timestamp (e.g. 2026-06-29T12:00:00Z) to epoch."""
    dt = datetime.datetime.fromisoformat(iso.replace("Z", "+00:00"))
    return int(dt.timestamp())

def _api_json(url, token, data=None):
    """Minimal GitHub API call. Returns parsed JSON, or raises."""
    headers = {
        "Authorization": f"bearer {token}",
        "User-Agent": "xv6-ntu-mp-grader",
        "Accept": "application/vnd.github+json",
    }
    if data is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(data).encode()
    req = urllib.request.Request(url, data=data, headers=headers)
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.load(resp)

def get_pushed_at(sha):
    """Return (epoch, source) for the authoritative GitHub push time of `sha`.

    Commit-embedded timestamps are forgeable (git commit --date= /
    GIT_COMMITTER_DATE); only a server-stamped time can anchor lateness.
    source is one of: 'graphql', 'actions_runs', 'unavailable'.
    """
    token = os.environ.get("GITHUB_TOKEN")
    repo = os.environ.get("GITHUB_REPOSITORY", "")
    if not token or "/" not in repo:
        return None, "unavailable"
    owner, name = repo.split("/", 1)

    # Primary: GraphQL Commit.pushedDate — set when GitHub first received the
    # commit object via push, on any ref, independent of workflow triggers.
    try:
        query = ("query($o:String!,$n:String!,$oid:GitObjectID!){"
                 "repository(owner:$o,name:$n){object(oid:$oid){"
                 "...on Commit{pushedDate}}}}")
        payload = {"query": query,
                   "variables": {"o": owner, "n": name, "oid": sha}}
        data = _api_json("https://api.github.com/graphql", token, payload)
        obj = ((data.get("data") or {}).get("repository") or {}).get("object") or {}
        if obj.get("pushedDate"):
            return _iso_to_epoch(obj["pushedDate"]), "graphql"
    except Exception as e:
        print(f"pushedDate via GraphQL failed: {e}", file=sys.stderr)

    # Fallback: earliest workflow run observed for this head SHA.
    try:
        url = (f"https://api.github.com/repos/{owner}/{name}"
               f"/actions/runs?head_sha={sha}&per_page=100")
        data = _api_json(url, token)
        times = [_iso_to_epoch(r["created_at"])
                 for r in data.get("workflow_runs", []) if r.get("created_at")]
        if times:
            return min(times), "actions_runs"
    except Exception as e:
        print(f"pushedDate via Actions runs failed: {e}", file=sys.stderr)

    return None, "unavailable"

def main():
    try:
        ta_emails = load_config()
        print(f"Loaded TA Emails: {ta_emails}", file=sys.stderr)
        
        commits = get_commits()
        target = find_student_commit(commits, ta_emails)
        
        if target:
            print(f"Found Target Student Commit: {target['hash']} by {target['email']}")

            # Authoritative submission time (forgery-resistant). null when no
            # server evidence is available — the grader flags such cases.
            pushed_at, pushed_src = get_pushed_at(target['hash'])
            print(f"Push time: {pushed_at} (source: {pushed_src})")

            # Output for GitHub Actions
            if "GITHUB_OUTPUT" in os.environ:
                with open(os.environ["GITHUB_OUTPUT"], "a") as f:
                    f.write(f"target_sha={target['hash']}\n")
                    f.write(f"target_timestamp={target['timestamp']}\n")
                    f.write(f"target_author={target['email']}\n")
                    f.write(f"target_pushed_at={pushed_at if pushed_at else ''}\n")

            # Write to a JSON snippet for report inclusion
            with open("target_commit.json", "w") as f:
                json.dump({
                    "sha": target['hash'],
                    "author": target['email'],
                    "timestamp": target['timestamp'],      # committer time (forgeable; display only)
                    "pushed_at": pushed_at,                 # authoritative epoch, or null
                    "pushed_at_source": pushed_src
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
