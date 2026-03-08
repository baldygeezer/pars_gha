import os

from lib.git2prov import run_git2prov
from pathlib import Path

from model import Repo

def git2prov(repo_slug, directory=None):
    if not Path(directory).exists():
        os.mkdir(directory)

    r = Repo(repo_slug)

    directory_path = r.directory(base=directory)

    dry_run = False
    run_git2prov(repo_slug, directory_path, dry_run)
