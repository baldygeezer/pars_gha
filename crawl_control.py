import subprocess
from pathlib import Path
from time import sleep

REPOS_FILE = "crawl_lists/lr_list8.txt"
CRAWL_DIR = "long_repos"
LOG_DIR = Path("crawl_logs")
MAX_ATTEMPTS = 10
PERMANENT_FAILURES = ("RESOURCE_LIMITS_EXCEEDED", "VALIDATION_FAILED", "NOT_FOUND")

def load_repos(filepath):
    with open(filepath) as f:
        return [line.strip() for line in f if line.strip()]

def repo_to_stem(repo):
    return repo.replace("/", "_")

def log_paths(repo, attempt):
    stem = repo_to_stem(repo)
    suffix = "" if attempt == 0 else str(attempt)
    return (
        LOG_DIR / f"{stem}_output{suffix}.log",
        LOG_DIR / f"{stem}_errlog{suffix}.log",
    )

def is_complete(output_log):
    """
    crawl succeeded if last stdout line starts with 'got '.
    crawl failed if last line is '{repo} {SomeException}'.
    empty output means something crashed
    """
    try:
        text = output_log.read_text().strip()
        if not text:
            return False

        last = text.splitlines()[-1]
        # fro some errors we want to stop completely and investigate rather than keep hammering the endpoint
        if any(marker in last for marker in PERMANENT_FAILURES):
            raise RuntimeError(f"Permanent failure in {output_log.name}: {last}")
        return last.startswith("got ")
    
    except FileNotFoundError:
        return False

def last_attempted(repo):
    """
    Returns (attemp:int, complete:bool) for a repo using the names of 
    existing log files, which have an incremental suffix.
    attempt = -1 means never crawled.
    """
    stem = repo_to_stem(repo)
    attempt = -1
    for i in range(MAX_ATTEMPTS + 1):
        suffix = "" if i == 0 else str(i)
        log = LOG_DIR / f"{stem}_output{suffix}.log"
        # check for a file with that suffix...
        if log.exists():
            #update the attempt number if there is a log with that suffix
            attempt = i
        else:
            #stop if there isn't
            break
    # if there was no update then ti hasn't been crawled yet        
    if attempt == -1:
        return -1, False
    #generate the name of the last log file so we can check that that attempt was complete
    suffix = "" if attempt == 0 else str(attempt)
    log = LOG_DIR / f"{stem}_output{suffix}.log"
    return attempt, is_complete(log)



def run_crawl(repo, recrawl=False, attempt=0):
    output_log, error_log = log_paths(repo, attempt)
    cmd = ["python", "run.py", "crawl", repo, "-d", CRAWL_DIR]
    if recrawl:
        cmd.append("-r")
        sleep(attempt)

    label = f"{'Recrawl' if recrawl else 'Crawl'} attempt {attempt}"
    print(f"  {label}: {repo}")

    with open(output_log, "w") as out, open(error_log, "w") as err:
        subprocess.run(cmd, stdout=out, stderr=err)

    return output_log



def main():
    LOG_DIR.mkdir(exist_ok=True)
    repos = load_repos(REPOS_FILE)
    print(f"Loaded {len(repos)} repos\n")

    # check the logs to see what state the repos are in...
    first_timers = []
    recrawl_list = []

    for repo in repos:

        attempt, complete = last_attempted(repo)
        
        if complete:
            print(f"we already did this one: {repo}")

        elif attempt == -1:
            print( f" Not tried to do {repo} yet")
            first_timers.append(repo)

        else:
            print(f"we tried {repo} {attempt} times so far, and it's still incomplete, so let's have another go!.")
            recrawl_list.append((repo, attempt))




    # Initial crawl

    if first_timers:
        print(f"***frist crawl for {len(first_timers)} repos ***")
    
    for repo in first_timers:

        output_log = run_crawl(repo, recrawl=False, attempt=0)
        
        if is_complete(output_log):
            print(f"    complete")
        else:
            print(f"    INCOMPLETE — queued for recrawl")

            recrawl_list.append((repo,0))

    # Recrawl loop

    while recrawl_list:
        print(f"\n=== Recrawl pass {attempt}: {len(recrawl_list)} repos ===")
        still_incomplete = []

        for repo, last_try in recrawl_list:
            next_try = last_try + 1

            if next_try > MAX_ATTEMPTS:
                print(f"{repo} was tried {last_try} times.  We are giving up now")
                continue

            output_log = run_crawl(repo, recrawl=True, attempt=next_try)

            if is_complete(output_log):
                print(f"    complete")
            else:
                print(f"    still incomplete")
                still_incomplete.append((repo, next_try))
        recrawl_list = still_incomplete
        
    print("\nDone")

    

if __name__ == "__main__":
    main()