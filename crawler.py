import time 
import logging
import os
from pathlib import Path

import requests
import json

from model import *

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

    def post(self, body):
        if self.remaining == 0:
            time.sleep(self.reset_at-time.time())

        headers = {'Content-type': 'application/json', 'Authorization': f'Bearer {self.token}'}
        resp = requests.post(self.endpoint, json=body, headers=headers)
        self.remaining = int(resp.headers.get('x-ratelimit-remaining', -1))
        self.reset_at = int(resp.headers.get('x-ratelimit-reset', time.time()))
        if resp.status_code == 429:
            return self.post(body)
        else:
            resp.raise_for_status()
        if self.remaining == 0:
            logger.warn(f'rate limit: remaining: {self.remaining} reset: {self.reset_at}')
        else:
            logger.debug(f'rate limit: remaining: {self.remaining} reset: {self.reset_at}')

        return resp

def crawl(repo: str, endpoint: str, token: str, num_issues=50, num_events=250, num_per_page=100, directory=None):
    if not Path(directory).exists():
        os.mkdir(directory)

    logger.info("starting to crawl repo: "+repo)
    logger.info("crawling into directory: "+directory)
    start_time = time.time()
    r = Repo(repo)

    poster = Poster(endpoint=endpoint, token=token)

    tasks = []
    tasks.append(InitialIssues())
    tasks.append(InitialPullRequests())
    tasks.append(RepoInfo())
    tasks.append(Stargazer())
    tasks.append(Releases())

    crawling = True

    count = 0
    while(tasks):
        t = tasks.pop()
        query = t.query()
        body = {
                'query': query,
                'variables': {
                    'owner': r.owner,
                    'name': r.name,
                    'num_issues': num_issues,
                    'num_events': num_events,
                    'num_per_page': num_per_page,
                }
        }
        resp = poster.post(body)

        count = count + 1
        logger.error(f'post response had error code {resp.status_code}')

        data = resp.json()
        if not validate(data):
            logger.error(f'post response body failed to validate:\n{body}')
            errors = data["errors"]
            if "NOT_FOUND" in [e['type'] for e in errors]:
                return
            raise(Exception(f'failed to validate: {data["errors"]}'))

        next_tasks = []
        if hasattr(t, "process") and callable(getattr(t, "process")):
           next_tasks = t.process(data, r)
        elif hasattr(t, "process_to_file") and callable(getattr(t, "process_to_file")):
            output = t.process_to_file(data)
            filename = f'{r.directory(base=directory)}/{t.filename}.json'
            with open(filename, 'w') as file:
                dump, tasks = t.process_to_file(data)
                json.dump(dump, file)
                tasks.extend(next_tasks)

        completed_issues = ",".join([str(x) for x in r.complete_issues()])
        if completed_issues:
            logger.info(f'post found complete issues: { completed_issues }')
        incomplete_issues = ",".join([str(x) for x in r.incomplete_issues()])
        if incomplete_issues:
            logger.info(f'post found incomplete issues: { incomplete_issues }')

        completed_pull_requests = ",".join([str(x) for x in r.complete_pull_requests()])
        if completed_pull_requests:
            logger.info(f'post found complete pull_requests: { completed_pull_requests }')
        incomplete_pull_requests = ",".join([str(x) for x in r.incomplete_pull_requests()])
        if incomplete_pull_requests:
            logger.info(f'post found incomplete pull_requests: { incomplete_pull_requests }')

        if next_tasks:
            tasks.extend(next_tasks)

        for i in r.complete_issues():
            logger.debug(f'complete issue {i}')
            issue = r.issues[i]
            filename = f'{r.directory(base=directory)}/issue{i:06d}.json'
            logger.debug(f'writing to filename {filename}')
            with open(filename, 'w') as file:
                dump = dict(info=issue.info, events=issue.events)
                json.dump(dump, file)
            r.remove_issue(i)

        for i in r.complete_pull_requests():
            logger.debug(f'complete pull request {i}')
            pr = r.pull_requests[i]
            filename = f'{r.directory(base=directory)}/pull_request{i:06d}.json'
            logger.debug(f'filename {filename}')
            with open(filename, 'w') as file:
                dump = dict(info=pr.info, events=pr.events)
                json.dump(dump, file)
            r.remove_pull_request(i)

        inc = r.incomplete_issues()
        if len(inc) > 0 and (len(inc) > 10 or len(tasks)==0):
            logger.debug(f'not complete {len(inc)} issues')
            fill = IssuesEventsPage([r.issues[i] for i in inc])
            tasks.append(fill)

        inc = r.incomplete_pull_requests()
        if len(inc) > 0 and (len(inc) > 10 or len(tasks)==0):
            logger.debug(f'not complete {len(inc)} pull_requests')
            fill = PullRequestsEventsPage([r.pull_requests[i] for i in inc])
            tasks.append(fill)

    end_time = time.time()
    logger.debug(f'crawl domplete, made { count } requests in {end_time - start_time} seconds')

