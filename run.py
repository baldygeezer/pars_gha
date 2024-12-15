import logging
import typing
import time
import sys
import json
from pathlib import Path

import click
from decouple import config

import requests

import graphql

logger = logging.getLogger(__name__)

graphql_endpoint = config('ENDPOINT', default='https://api.github.com/graphql')
graphql_token = config('TOKEN')

class BaseAction:
    def __init__(self):
        pass

issue_persist = [ '__typename', 'id', 'databaseId', 'number', 'title', 'author', 'body', 'createdAt', 'closed',
        'closedAt', 'updatedAt', 'state', 'stateReason', 'url' ]

class IssuesPage:
    def __init__(self, cursor):
        self.cursor = cursor
    def query(self):
        return graphql.issues_ongoing_query(self.cursor)
    def process(self, data, r):
        issues = data['data']['repository']['issues']
        for issue in issues['nodes']:
            num = issue['number']
            i = r.add_issue(num)
            persist = {k: v for k, v in issue.items() if k in issue_persist}
            i.add_info(persist)

            timeline = issue['timelineItems']
            events = map(lambda x: x['node'], timeline['edges'])
            i.add_events(events)
            i.complete(not timeline['pageInfo']['hasNextPage'])
            i.cursor = timeline['pageInfo']['endCursor']
        if issues['pageInfo']['hasNextPage']:
            return [IssuesPage(issues["pageInfo"]["endCursor"])]

        return []

pull_request_persist = [ '__typename', 'id', 'databaseId', 'number', 'title', 'author', 'body', 'createdAt', 'baseRefName', 'baseNameRepository', 'closed',
        'closedAt', 'updatedAt', 'state', 'stateReason', 'url', 'mergeCommit', 'merged', 'mergedAt', 'mergedBy']

class PullRequestsPage:
    def __init__(self, cursor):
        self.cursor = cursor
    def query(self):
        return graphql.pull_requests_ongoing_query(self.cursor)
    def process(self, data, r):
        prs = data['data']['repository']['pullRequests']
        for pr in prs['nodes']:
            num = pr['number']
            p = r.add_pull_request(num)
            persist = {k: v for k, v in pr.items() if k in pull_request_persist}
            p.add_info(persist)

            timeline = pr['timelineItems']
            events = map(lambda x: x['node'], timeline['edges'])
            p.add_events(events)
            p.complete(not timeline['pageInfo']['hasNextPage'])
            p.cursor = timeline['pageInfo']['endCursor']
        if prs['pageInfo']['hasNextPage']:
            return [PullRquestsPage(pr["pageInfo"]["endCursor"])]

        return []

class InitialIssues(IssuesPage):
    def __init__(self):
        pass
    def query(self):
        return graphql.issues_initial_query()

class InitialPullRequests(PullRequestsPage):
    def __init__(self):
        pass
    def query(self):
        return graphql.pull_requests_initial_query()

class IssuesEventsPage:
    def __init__(self, issues):
        self.issues = issues
    def query(self):
        return graphql.issues_fill_query(self.issues)
    def process(self, data, r):
        issues = data['data']['repository']
        for k, issue in issues.items():
            num = issue['number']
            timeline = issue['timelineItems']
            events = map(lambda x: x['node'], timeline['edges'])
            r.issues[num].add_events(events)
            r.issues[num].complete(not timeline['pageInfo']['hasNextPage'])
            r.issues[num].cursor = timeline['pageInfo']['endCursor']
        return []

class PullRequestsEventsPage:
    def __init__(self, prs):
        self.prs = prs
    def query(self):
        return graphql.pull_requests_fill_query(self.prs)
    def process(self, data, r):
        prs = data['data']['repository']
        for k, issue in prs.items():
            num = issue['number']
            timeline = issue['timelineItems']
            events = map(lambda x: x['node'], timeline['edges'])
            r.pull_requests[num].add_events(events)
            r.pull_requests[num].complete(not timeline['pageInfo']['hasNextPage'])
            r.pull_requests[num].cursor = timeline['pageInfo']['endCursor']
        return []


class Issue:
    def __init__(self, issueId):
        self.issueId = issueId
        self.events = []
        self._complete = False
        self.cursor = ""
        self.info = None

    def add_info(self, info):
        self.info = info
    def add_events(self, el):
        self.events.extend(el)

    def set_cursor(self, cursor):
        self.cursor = cursor

    def complete(self, b):
        self._complete = b

    def isComplete(self):
        return self._complete

class PullRequest(Issue):
    pass

class Repo:
    def __init__(self, repo_name):
        self.repo_name = repo_name
        owner, name = repo_name.split('/')
        self.owner = owner
        self.name = name
        self.issues = dict()
        self.pull_requests = dict()
        self.info = None

    def add_issue(self, issueId):
        if issueId not in self.issues:
            i = Issue(issueId)
            self.issues[issueId] = i
        return self.issues[issueId]
    def add_info(self, info):
        self.info = info
    def incomplete_issues(self):
        return [i for i in self.issues.keys() if not self.issues[i].isComplete()]
    def complete_issues(self):
        return [i for i in self.issues.keys() if self.issues[i].isComplete()]
    def remove_issue(self, issueId):
        self.issues.pop(issueId)

    def add_pull_request(self, issueId):
        if issueId not in self.pull_requests:
            i = PullRequest(issueId)
            self.pull_requests[issueId] = i
        return self.pull_requests[issueId]
    def incomplete_pull_requests(self):
        return [i for i in self.pull_requests.keys() if not self.pull_requests[i].isComplete()]
    def complete_pull_requests(self):
        return [i for i in self.pull_requests.keys() if self.pull_requests[i].isComplete()]
    def remove_pull_request(self, prId):
        self.pull_requests.pop(prId)

    def directory(self):
        d = self.repo_name.replace("/","_")
        p = Path(d)
        p.mkdir( exist_ok=True)
        return p.absolute()

@click.group()
def cli():
    logging.basicConfig(level=config('LOG_LEVEL', default='INFO'))

def validate(resp):
    if "errors" in resp:
        return False
    if "data" not in resp:
        return False
    return True

class Poster():
    def __init__(self, *args, **kwargs):
        self.remaining = -1
        self.reset_at = 0
        pass
    def post(self, body):
        if self.remaining == 0:
            time.sleep(self.reset_at, time.time())

        headers = {'Content-type': 'application/json', 'Authorization': f'Bearer {graphql_token}'}
        resp = requests.post(graphql_endpoint, json=body, headers=headers)
        self.remaining = int(resp.headers.get('x-ratelimit-remaining', -1))
        self.reset_at = int(resp.headers.get('x-ratelimit-reset', time.time()))
        if resp.status_code == 429:
            return self.post(body)
        else:
            resp.raise_for_status()
        print(f'rate limit: remaining: {self.remaining} reset: {self.reset_at}', file=sys.stderr)

        return resp

def crawl(repo: str):
    print(repo)
    r = Repo(repo)

    poster = Poster()

    queryIssues = InitialIssues()
    queryPRs = InitialPullRequests()

    crawling = True
    tasks = [queryIssues, queryPRs]

    count = 0
    while(tasks):
        t = tasks.pop()
        query = t.query()
        body = {
                'query': query,
                'variables': {
                    'owner': r.owner,
                    'name': r.name,
                    'num_issues': 100,
                    'num_events': 250
                }
        }
        resp = poster.post(body)

        count = count + 1
        print(resp.status_code)

        data = resp.json()
        if not validate(data):
            print(body)
            raise(Exception(f'failed to validate: {data["errors"]}'))

        next_tasks = t.process(data, r)

        print(r.complete_issues(), r.incomplete_issues())

        if next_tasks:
            tasks.extend(next_tasks)

        for i in r.complete_issues():
            print(f'complete {i}')
            issue = r.issues[i]
            filename = f'{r.directory()}/issue{i:06d}.json'
            print(f'filename {filename}')
            with open(filename, 'w') as file:
                dump = dict(info=issue.info, events=issue.events)
                json.dump(dump, file)
            r.remove_issue(i)

        for i in r.complete_pull_requests():
            print(f'complete pr {i}')
            pr = r.pull_requests[i]
            filename = f'{r.directory()}/pull_request{i:06d}.json'
            print(f'filename {filename}')
            with open(filename, 'w') as file:
                dump = dict(info=pr.info, events=pr.events)
                json.dump(dump, file)
            r.remove_pull_request(i)

        inc = r.incomplete_issues()
        if len(inc) > 0 and (len(inc) > 10 or len(tasks)==0):
            print(f'not complete {len(inc)}')
            fill = IssuesEventsPage([r.issues[i] for i in inc])
            tasks.append(fill)

        inc = r.incomplete_pull_requests()
        if len(inc) > 0 and (len(inc) > 10 or len(tasks)==0):
            print(f'not complete {len(inc)}')
            fill = PullRequestEventsPage([r.pull_requests[i] for i in inc])
            tasks.append(fill)

def convert(repo):
    pass

@cli.command(name='crawl')
@click.argument('repo') # '-r', '--repo', 'repos', required=True, help='repo to crawl')
def cmd_crawl(
    repo
):
    repos = [repo]
    for r in repos:
        #try:
           crawl(r)
        #except Exception as e:
        #   print(e)

@cli.command(name='convert')
@click.argument('repo') # '-r', '--repo', 'repos', required=True, help='repo to crawl')
def cmd_convert(
    repo
):
    repos = [repo]
    for r in repos:
        #try:
           convert(r)
        #except Exception as e:
        #   print(e)

if __name__ == '__main__':
    cli()
