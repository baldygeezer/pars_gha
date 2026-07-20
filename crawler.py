import time 
import os
import glob
from pathlib import Path

import requests
import json

from model import Repo, Issues, PullRequests, RepoInfo, Stargazer, Releases, Commits

import logging
logger = logging.getLogger(__name__)

def validate(resp):
    if "errors" in resp:
        return False
    if "data" not in resp:
        return False
    return True

class Poster():
    """
    Poster manages querying the Github graphql api.

    It will respond to rate limit response headers
    """
    def __init__(self, endpoint: str, token: str):
        """
        Args:
            endpoint (str): the url of the endpoint to use
            token (str): a bearer token to use with the Authorization header
        """
        self.remaining = -1
        self.reset_at = 0
        self.endpoint = endpoint
        self.token = token

    def _post(self, body, headers):
        backoff_factor = 2
        retry = True
        try_count = 0
        while retry:
            resp = requests.post(self.endpoint, json=body, headers=headers)
            try_count = try_count + 1
            if resp.status_code not in [429, 502]:
                resp.raise_for_status()
                return resp
            if try_count > 5:
                retry = False
                continue
            time.sleep(backoff_factor ** try_count)
        resp.raise_for_status()

    def post(self, body):
        if self.remaining < 2:
            delay = 1 + self.reset_at - time.time()
            if delay > 0:
                time.sleep(delay)

        headers = {'Content-type': 'application/json', 'Authorization': f'Bearer {self.token}'}
        resp = self._post(body, headers)
        self.remaining = int(resp.headers.get('x-ratelimit-remaining', -1))
        self.reset_at = int(resp.headers.get('x-ratelimit-reset', time.time()))

        if self.remaining < 4:
            logger.warn(f'rate limit: remaining: {self.remaining} reset: {self.reset_at}')
        else:
            logger.debug(f'rate limit: remaining: {self.remaining} reset: {self.reset_at}')

        return resp

def crawl(repo: str, endpoint: str, token: str, num_issues=50, num_events=250, num_per_page=100, directory=None, load=False):
    if not Path(directory).exists():
        os.mkdir(directory)

    logger.info("starting to crawl repo: "+repo)
    logger.info("crawling into directory: "+directory)
    start_time = time.time()
    r = Repo(repo)

    poster = Poster(endpoint=endpoint, token=token)

    tasks = []
    tasks.append(Issues())
    tasks.append(PullRequests())
    tasks.append(RepoInfo())
    tasks.append(Stargazer())
    tasks.append(Releases())
    tasks.append(Commits())

    if load:
        for t in tasks:
            if hasattr(t, "load") and callable(getattr(t, "load")):
                if hasattr(t, "filename"):
                    filename = f'{r.directory(base=directory)}/{t.filename}.json'
                    # bernard added a guard against file not found during recrawl
                    try:
                        with open(filename, 'r') as file:
                            data = json.load(file)
                            t.load(data)
                    except FileNotFoundError:
                        pass
                    # with open(filename, 'r') as file:
                    #     data = json.load(file)
                    #     t.load(data)

                elif hasattr(t, "glob"):
                    g = t.glob
                    d = r.directory(base=directory)
                    files = glob.glob(f'{d}/{g}*.json')
                    data = []
                    for filename in files:
                        with open(filename, 'r') as file:
                            data.append(json.load(file))
                    t.load(data)

    count = 0
    while(tasks):
        t = tasks.pop()
        query = t.query()
        data = None
        if query:
            body = {
                    'query': query,
                    'variables': {
                        'owner': r.owner,
                        'name': r.name,
                        'num_issues': num_issues,
                        'num_events': num_events,
                        'num_per_page': num_per_page,
                        'num_commits': 100,
                    }
            }
            resp = poster.post(body)

            count = count + 1
            logger.error(f'post response had error code {resp.status_code} {body}')

            data = resp.json()
            print("got", data)
            # bernard changed this - stopped raising an exception (which gets swallowed and fails silently)
            if not validate(data):
                logger.error(f'post response body failed to validate response for repo {repo}:\n{body}')
                logger.error(f'post response body failed to validate response for repo {repo}:\n{data}')
                errors = data["errors"]
                error_types = [e['type'] for e in errors]
                if "NOT_FOUND" in [e['type'] for e in errors]:
                    return
                if "RESOURCE_LIMITS_EXCEEDED" in error_types:
                    print(f'{repo} RESOURCE_LIMITS_EXCEEDED')
                    return        
                    print(f'{repo} VALIDATION_FAILED {error_types}')
                    return    

                # bernard changed this  
                # raise(Exception(f'failed to validate respose for repo {repo}: {data["errors"]}'))

        next_tasks = []
        if hasattr(t, "process") and callable(getattr(t, "process")):
           next_tasks = t.process(data, r)
        elif hasattr(t, "process_to_file") and callable(getattr(t, "process_to_file")):
            dump, next_tasks = t.process_to_file(data)
            if dump is not None:
                for key, data in dump.items():
                    filename = f'{r.directory(base=directory)}/{key}.json'
                    with open(filename, 'w') as file:
                        json.dump(data, file)

        if next_tasks:
            tasks.extend(next_tasks)

    end_time = time.time()
    logger.debug(f'crawl domplete, made { count } requests in {end_time - start_time} seconds')

