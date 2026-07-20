"""
reprocess_commits.py

One-off orchestration script to roll out the commit author/committer fix and
the PullRequestCommit -> wasInfluencedBy fix across every repo.

For each repo in repos.txt, this:
  1. Deletes the existing commits.json (so the recrawl fetches it, rather than trusting stale is_complete()/already_found state)
  2. Deletes the existing merged.ttl.gz (so convert_control.py-style skip-if-exists logic won't skip a repo that was already converted under the old code)
  3. Runs python run.py crawl <repo> -d long_repos -r` directly (bypassing crawl_control.py's is_complete() check entirely, since we specifically want to force this regardless of what the old logs say)
  4. Runs `python run.py convert <repo> -d long_repos -z`

Each step's stdout/stderr is captured to its own log file under reprocess_logs/, so a crash in any one repo/step is easy to trace without
stopping the rest of the run. Failures are logged and the script moves on to the next repo (log-and-continue, matching crawl_control.py /
convert_control.py).

Usage:
    python reprocess_commits.py
"""

import subprocess
from pathlib import Path

CRAWL_DIR = "long_repos"
LOGS_DIR = Path("reprocess_logs")
REPOS_FILE = "crawl_lists/lr_list.txt"


def repo_folder_name(repo: str) -> str:
    return repo.replace("/", "_")


def repo_dir(repo: str) -> Path:
    return Path(CRAWL_DIR) / repo_folder_name(repo)


def run_step(repo: str, step_name: str, cmd: list[str]):
    """Run a subprocess step, capturing stdout/stderr to per-repo/per-step logs."""
    LOGS_DIR.mkdir(exist_ok=True)
    stem = repo_folder_name(repo)
    output_log = LOGS_DIR / f"{stem}_{step_name}_output.log"
    error_log = LOGS_DIR / f"{stem}_{step_name}_errlog.log"
    with open(output_log, "w") as out, open(error_log, "w") as err:
        result = subprocess.run(cmd, stdout=out, stderr=err)
    return result.returncode, output_log, error_log


def reprocess_repo(repo: str):
    rdir = repo_dir(repo)
    commits_file = rdir / "commits.json"
    merged_file = rdir / "merged.ttl.gz"
    # check for a commits.json and delete it if we find it
    if commits_file.exists():
        commits_file.unlink()
        print(f"  Deleted {commits_file}")
    else:
        print(f"  No existing {commits_file} (already missing, skipping delete)")
    # check for an old results file and delete it
    if merged_file.exists():
        merged_file.unlink()
        print(f"  Deleted {merged_file}")

    print(f"  Recrawling (forcing -r regardless of prior completion state)...")
    #  build the recrawl command
    crawl_cmd = ["python", "run.py", "crawl", repo, "-d", CRAWL_DIR, "-r"]
    # Run the recrawl
    rc, out_log, err_log = run_step(repo, "crawl", crawl_cmd)
    # if we have a non-zero exit code or no commits file was created then something went wrong so we bail...
    if rc != 0 or not commits_file.exists():
        print(f"  CRAWL FAILED (exit {rc}). See {out_log} / {err_log}")
        return False
    # if we' still here that everything's prbably OK so build and run the convert
    print(f"  Converting...")
    convert_cmd = ["python", "run.py", "convert", repo, "-d", CRAWL_DIR, "-z"]
    rc, out_log, err_log = run_step(repo, "convert", convert_cmd)
    # If ther's a non-zero exit, or no reult file then we bail...
    if rc != 0 or not merged_file.exists():
        print(f"  CONVERT FAILED (exit {rc}). See {out_log} / {err_log}")
        return False

    print(f"  Done: {merged_file}")
    return True


def load_repos():
    with open(REPOS_FILE) as f:
        return [line.strip() for line in f if line.strip()]


def main():
    repos = load_repos()
    total = len(repos)
    succeeded = []
    failed = []

    for i, repo in enumerate(repos, start=1):
        print(f"[{i}/{total}] {repo}")
        try:
            ok = reprocess_repo(repo)
        except Exception as e:
            print(f"  UNEXPECTED ERROR: {e}")
            ok = False
        if ok:
            succeeded.append(repo)
        else:
            failed.append(repo)

    print()
    print("=== Reprocessing run complete ===")
    print(f"  Succeeded: {len(succeeded)}")
    print(f"  Failed: {len(failed)}")
    if failed:
        print("  Failed repos:")
        for r in failed:
            print(f"    - {r}")


if __name__ == "__main__":
    main()