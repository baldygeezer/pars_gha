from pathlib import Path

import graphql

issue_persist = [ '__typename', 'id', 'databaseId', 'number', 'title', 'author', 'body', 'createdAt', 'closed',
        'closedAt', 'updatedAt', 'state', 'stateReason', 'url', 'resourcePath' ]

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
        'closedAt', 'updatedAt', 'state', 'stateReason', 'url', 'resourcePath', 'mergeCommit', 'merged', 'mergedAt', 'mergedBy']

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
            return [PullRequestsPage(prs["pageInfo"]["endCursor"])]

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

class Stargazer:
    filename = "stargazers"
    def __init__(self):
        self.cursor = None
        self.accumulate = []
        pass
    def query(self):
        return graphql.stargazers_query(self.cursor)
    def process_to_file(self, data):
        output = None
        follow_on_tasks = []
        stargazers = data['data']['repository']['stargazers']
        self.accumulate.extend(
            [dict(who=s['node']['url'], when=s['starredAt']) for s in stargazers['edges']])

        if stargazers['pageInfo']['hasNextPage']:
            self.cursor = stargazers['pageInfo']['endCursor']
            follow_on_tasks.append(self)
        else:
            output = self.accumulate
        return output, follow_on_tasks

class Releases:
    filename = "releases"
    def __init__(self):
        self.cursor = None
        self.accumulate = []
        pass
    def query(self):
        return graphql.releases_query(self.cursor)
    def process_to_file(self, data):
        output = None
        follow_on_tasks = []
        releases = data['data']['repository']['releases']
        for r in releases['edges']:
            r = r['node']
            d = {k: r[k] for k in ['id', 'name', 'createdAt', 'author', 'url', 'tagCommit']}
            dc = 0
            for rr in r['releaseAssets']['edges']:
                dc = dc + rr['node']['downloadCount']
            d['downloadCount'] = dc
            self.accumulate.append(d)

        if releases['pageInfo']['hasNextPage']:
            self.cursor = releases['pageInfo']['endCursor']
            follow_on_tasks.append(self)
        else:
            output = self.accumulate
        return output, follow_on_tasks

class RepoInfo:
    filename = "repo_info"
    def __init__(self):
        pass
    def query(self):
        return graphql.repo_query()
    def process_to_file(self, data):
        follow_on_tasks = []
        return dict(
            url = data['data']['repository']['url'],
            fork_count = data['data']['repository']['forkCount'],
            stargazer_count = data['data']['repository']['stargazerCount'],
            watchers_count = data['data']['repository']['watchers']['totalCount']), follow_on_tasks


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

    def directory(self, base=None):
        d = self.repo_name.replace("/","_")
        p = Path()
        if base:
            p = Path(base)
        p = p / d
        p.mkdir(exist_ok=True)
        return p.absolute()
