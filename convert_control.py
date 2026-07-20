"""
convert_control.py

Loops the `run.py convert` command over a list of repos, converting each
repo's crawled data into a merged, gzipped RDF (Turtle) file.

Mirrors the structure of crawl_control.py:
- Reads repo names from repos.txt (one 'owner/repo' per line)
- Skips repos that already have a converted output file
- Writes per-repo stdout/stderr logs to convert_logs/
- Logs failures and continues to the next repo, rather than aborting the run

Usage:
    python convert_control.py
"""

import subprocess
from pathlib import Path

CRAWL_DIR = "long_repos"
CONVERT_LOGS_DIR = Path("convert_logs")
REPOS_FILE = "crawl_lists/lr_list1.txt"

CONVERT_OUTPUT_FILENAME = "merged.ttl.gz"


def repo_folder_name(repo: str) -> str:
    """Convert 'owner/repo' into the crawl data folder name 'owner_repo'."""
    return repo.replace("/", "_")


def output_path(repo: str) -> Path:
    """Path to the expected merged RDF output for a repo."""
    return Path(CRAWL_DIR) / repo_folder_name(repo) / CONVERT_OUTPUT_FILENAME


def log_paths(repo: str):
    """Return (output_log, error_log) paths for a repo's conversion attempt."""
    stem = repo_folder_name(repo)
    CONVERT_LOGS_DIR.mkdir(exist_ok=True)
    output_log = CONVERT_LOGS_DIR / f"{stem}_convert_output.log"
    error_log = CONVERT_LOGS_DIR / f"{stem}_convert_errlog.log"
    return output_log, error_log


def is_converted(repo: str) -> bool:
    """A repo is considered converted if its merged.ttl.gz already exists."""
    return output_path(repo).exists()


def run_convert(repo: str):
    """Run the convert command for a single repo, capturing stdout/stderr."""
    output_log, error_log = log_paths(repo)
    cmd = ["python", "run.py", "convert", repo, "-d", CRAWL_DIR, "-z"]
    print(f"  Converting: {repo}")
    with open(output_log, "w") as out, open(error_log, "w") as err:
        result = subprocess.run(cmd, stdout=out, stderr=err)
    return result.returncode, output_log, error_log


def load_repos():
    with open(REPOS_FILE) as f:
        return [line.strip() for line in f if line.strip()]


def main():
    repos = load_repos()
    total = len(repos)
    converted = 0
    skipped = 0
    failed = []

    for i, repo in enumerate(repos, start=1):
        print(f"[{i}/{total}] {repo}")

        if is_converted(repo):
            print(f"  Already converted, skipping: {output_path(repo)}")
            skipped += 1
            continue

        returncode, output_log, error_log = run_convert(repo)

        if returncode == 0 and is_converted(repo):
            print(f"  Done: {output_path(repo)}")
            converted += 1
        else:
            print(f"  FAILED (exit code {returncode}). See {output_log} / {error_log}")
            failed.append(repo)

    print()
    print("=== Conversion run complete ===")
    print(f"  Converted: {converted}")
    print(f"  Skipped (already done): {skipped}")
    print(f"  Failed: {len(failed)}")
    if failed:
        print("  Failed repos:")
        for r in failed:
            print(f"    - {r}")


if __name__ == "__main__":
    main()