from pathlib import Path

import logging

import graphql

issue_persist = [ '__typename', 'id', 'databaseId', 'number', 'title', 'author', 'body', 'createdAt', 'closed',
        'closedAt', 'updatedAt', 'state', 'stateReason', 'url', 'resourcePath' ]

logger = logging.getLogger(__name__)

# Bernard added a helper to guard against missing values (None)
def extract_events(edges):
    return [e['node'] for e in edges if e is not None and e.get('node') is not None]

class IssuesEventsPage:
    def __init__(self, repo, issues):
        self.issues = issues
        self.repo = repo
    def query(self):
        return graphql.issues_fill_query(self.issues)
    def process(self, data, r):
        issues = data['data']['repository']
        for k, issue in issues.items():
            # Bernard added this to stop a crash on encountering deleted (None) issues
            if issue is None:
                logger.warning(f'null node for key {k} in fill response for {self.repo.repo_name}, skipping')
                print(f'null node skipped: {self.repo.repo_name} {k}')
                continue
            num = issue['number']
            timeline = issue['timelineItems']
            # bernard added a guard against missing nodes (None)
            # events = map(lambda x: x['node'], timeline['edges'])
            events = extract_events(timeline['edges'])

            self.repo.issues[num].add_events(events)
            self.repo.issues[num].complete(not timeline['pageInfo']['hasNextPage'])
            self.repo.issues[num].cursor = timeline['pageInfo']['endCursor']
        # bernard added    
        still_incomplete = [i for i in self.issues if not i.isComplete()]
        if still_incomplete:
            return [IssuesEventsPage(self.repo, still_incomplete)]

        return []

class Issues:
    glob = 'issue'
    def __init__(self):
        self.cursor = None
        self.repo = Repo("doesnot/matter")
        self.main_page = True
    def load(self, data):
        for d in data:
            number = d["info"]["number"]
            self.repo.add_issue(number)
            i = self.repo.issues[number]
            i.existing = True
            i.add_info(d["info"])
            i.add_events(d["events"])
    def query(self):
        if self.main_page:
            return graphql.issues_query(self.cursor)
        return None
    def process_to_file(self, data):
        overlap_with_existing = False
        if data:
            issues = data['data']['repository']['issues']
            for issue in issues['nodes']:
                num = issue['number']
                if self.repo.has_issue(num):
                    i = self.repo.add_issue(num)
                    if i.existing:
                        overlap_with_existing = True
                        continue
                i = self.repo.add_issue(num)
                persist = {k: v for k, v in issue.items() if k in issue_persist}
                i.add_info(persist)

                timeline = issue['timelineItems']
                # Bernard added a guard against None nodes
                # events = map(lambda x: x['node'],  timeline['edges'])
                events = extract_events(timeline['edges'])
                i.add_events(events)
                i.complete(not timeline['pageInfo']['hasNextPage'])
                i.cursor = timeline['pageInfo']['endCursor']

        tasks = []

        completed = dict()
        for i in self.repo.complete_issues():
            logger.debug(f'complete issue {i}')
            issue = self.repo.issues[i]
            if issue.existing:
                continue
            filename = f'issue{i:06d}'
            completed[filename] = dict(info=issue.info, events=issue.events)
            self.repo.remove_issue(i)

        if data and issues["pageInfo"]["hasNextPage"] and not overlap_with_existing:
            self.cursor = issues["pageInfo"]["endCursor"]
            tasks.append(self)
        else:
            self.cursor = None
            self.main_page = False

        inc = self.repo.incomplete_issues()
        inc = [i for i in inc if not self.repo.issues[i].existing]

        if len(inc) > 0 and (len(inc) > 10 or len(tasks)==0):
            logger.debug(f'not complete {len(inc)} issues')
            fill = IssuesEventsPage(self.repo, [self.repo.issues[i] for i in inc])
            tasks.append(fill)

            # bernard changed this to kill the infinite loop 
            if not self.main_page and data is not None:
                tasks.append(self)

        if not completed:
            completed = None

        return completed, tasks

pull_request_persist = [ '__typename', 'id', 'databaseId', 'number', 'title', 'author', 'body', 'createdAt', 'baseRefName', 'baseNameRepository', 'closed',
        'closedAt', 'updatedAt', 'state', 'stateReason', 'url', 'resourcePath', 'mergeCommit', 'merged', 'mergedAt', 'mergedBy']

class PullRequestsEventsPage:
    def __init__(self, repo, prs):
        self.repo = repo
        self.prs = prs
    def query(self):
        return graphql.pull_requests_fill_query(self.prs)
    def process(self, data, r):
        prs = data['data']['repository']
        for k, issue in prs.items():
            # Bernard added this to stop a crash on encountering deleted issues
            if issue is None:
                logger.warning(f'null node for key {k} in fill response for {self.repo.repo_name}, skipping')
                print(f'null node skipped: {self.repo.repo_name} {k}')
                continue
            num = issue['number']
            timeline = issue['timelineItems']
            # Bernard added a guard against None nodes
            # events = map(lambda x: x['node'], timeline['edges'])
            events = extract_events(timeline['edges'])
            self.repo.pull_requests[num].add_events(events)
            self.repo.pull_requests[num].complete(not timeline['pageInfo']['hasNextPage'])
            self.repo.pull_requests[num].cursor = timeline['pageInfo']['endCursor']
        
        # bernard added    
        still_incomplete = [i for i in self.prs if not i.isComplete()]
        if still_incomplete:
            return [PullRequestsEventsPage(self.repo, still_incomplete)]


        return []

class PullRequests:
    glob = 'pull_request'
    def __init__(self):
        self.cursor = None
        self.repo = Repo("doesnot/matter")
        self.main_page = True
    def load(self, data):
        for d in data:
            number = d["info"]["number"]
            self.repo.add_pull_request(number)
            i = self.repo.pull_requests[number]
            i.existing = True
            i.add_info(d["info"])
            i.add_events(d["events"])
    def query(self):
        if self.main_page:
            return graphql.pull_requests_query(self.cursor)
        return None
    def process_to_file(self, data):
        overlap_with_existing = False
        if data:
            prs = data['data']['repository']['pullRequests']
            for pr in prs['nodes']:
                num = pr['number']
                if self.repo.has_pull_request(num):
                    p = self.repo.add_pull_request(num)
                    if p.existing:
                        print("repo had pull_request", num, p)
                        overlap_with_existing = True
                        continue
                p = self.repo.add_pull_request(num)
                persist = {k: v for k, v in pr.items() if k in pull_request_persist}
                p.add_info(persist)

                timeline = pr['timelineItems']
                # Bernard added a guard agianst None nodes
                # events = map(lambda x: x['node'],  timeline['edges'])
                events = extract_events(timeline['edges'])

                p.add_events(events)
                p.complete(not timeline['pageInfo']['hasNextPage'])
                p.cursor = timeline['pageInfo']['endCursor']

        tasks = []

        completed = dict()
        for i in self.repo.complete_pull_requests():
            logger.debug(f'complete pull request {i}')
            pr = self.repo.pull_requests[i]
            if pr.existing:
                continue
            filename = f'pull_request{i:06d}'
            completed[filename] = dict(info=pr.info, events=pr.events)
            self.repo.remove_pull_request(i)

        print("working out next step")
        if data and prs["pageInfo"]["hasNextPage"] and not overlap_with_existing:
            self.cursor = prs["pageInfo"]["endCursor"]
            tasks.append(self)
            print("working out next step: page")
        else:
            self.cursor = None
            self.main_page = False
            
            # Bernard's change: add guard to stop a crash when data is None so prs not assigned
            # print("working out next step: no page", prs["pageInfo"], overlap_with_existing)
            print("working out next step: no page", prs["pageInfo"] if data else None, overlap_with_existing)

        inc = self.repo.incomplete_pull_requests()
        inc = [i for i in inc if not self.repo.pull_requests[i].existing]

        if len(inc) > 0 and (len(inc) > 10 or len(tasks)==0):
            logger.debug(f'not complete {len(inc)} pull_requests')
            fill = PullRequestsEventsPage(self.repo, [self.repo.pull_requests[i] for i in inc])
            tasks.append(fill)

            # Bernard made an infinite loop and fixed it here!
            if not self.main_page and data is not None:
                tasks.append(self)

            # if not self.main_page:
            #     tasks.append(self)

        if not completed:
            completed = None

        print("returning", tasks)
        return completed, tasks

class Commits:
    filename = "commits"
    def __init__(self):
        self.cursor = None
        self.accumulate = []
        self.already_found = None
        self.existing = []
    def load(self, data):
        if len(data) > 0:
            self.existing = data
            self.already_found = max([f.get("sha") for f in self.existing])
    def query(self):
        return graphql.commits_query(self.cursor)
    def process_to_file(self, data):
        history = data['data']['repository']['defaultBranchRef']
        page = history['target']['history']
        entries = []
        for t in page['edges']:
            c = t['node']
           
            # Bernard's changes below to fix broken linkage between Agents and Commits
            # userinfo was fetched by the graphql but not added to the commits.json
            commit = {
                "url": c['commitUrl'],
                "sha": c['oid'],
                "commit": {
                    "author": {
                        "name": c['author']['name'],
                        "email": c['author']['email'],
                        "date": c['authoredDate'],
                        # get a userid (.get() cos it can be none if the commit was via browser ui)
                        "user":c['author'].get('user')

                    },
                    "committer": {
                        "name": c['committer']['name'],
                        "email": c['committer']['email'],
                        "date": c['committedDate'],
                        # get a userid (.get() cos it can be none if the commit was via browser ui)
                        "user":c['committer'].get('user')
                    },
                    "message": c['message']
                }
            }
            entries.append(commit)

        abort = False
        if self.already_found:
            before = len(entries)
            print(before)
            entries = [e for e in entries if e.get("sha") > self.already_found]
            print(len(entries))
            if len(entries) < before:
                abort = True

        self.accumulate.extend(entries)

        if not abort and page['pageInfo']['hasNextPage']:
            self.cursor = page['pageInfo']['endCursor']
            return None, [self]
        return {self.filename:self.accumulate + self.existing}, []

class Stargazer:
    filename = "stargazers"
    def __init__(self):
        self.cursor = None
        self.accumulate = []
        self.already_found = None
        self.existing = []
    def load(self, data):
        if len(data) > 0:
            self.existing = data
            self.already_found = max([f.get("when") for f in self.existing])
    def query(self):
        return graphql.stargazers_query(self.cursor)
    def process_to_file(self, data):
        stargazers = data['data']['repository']['stargazers']
        entries = [dict(who=s['node']['url'], when=s['starredAt']) for s in stargazers['edges']]
        abort = False
        if self.already_found:
            before = len(entries)
            entries = [e for e in entries if e.get("when") > self.already_found]
            if len(entries) < before:
                abort = True

        self.accumulate.extend(entries)

        if not abort and stargazers['pageInfo']['hasNextPage']:
            cursor = stargazers['pageInfo']['endCursor']
            self.cursor = cursor
            return None, [self]

        return {self.filename:self.accumulate + self.existing}, []

class Releases:
    filename = "releases"
    def __init__(self):
        self.cursor = None
        self.accumulate = []
        self.already_found = None
        self.existing = []
    def load(self, data):
        if len(data) > 0:
            self.existing = data
            self.already_found = set([f.get("id") for f in self.existing])
    def query(self):
        return graphql.releases_query(self.cursor)
    def process_to_file(self, data):
        releases = data['data']['repository']['releases']

        entries = []
        for r in releases['edges']:
            r = r['node']
            d = {k: r[k] for k in ['id', 'name', 'createdAt', 'author', 'url', 'tagCommit']}
            dc = 0
            for rr in r['releaseAssets']['edges']:
                dc = dc + rr['node']['downloadCount']
            
            # bernard changed this. The release fragment is now capped at 20 releases per page to avoid hitting quotas, so...
            # if there are more pages in the result we have more pages to go. we might hit the cap at this point
            if r['releaseAssets']['pageInfo']['hasNextPage']:
                # so we track the download count as a 'more-than' value because we havent seen every page and
                 # don't know the actual value. If we hit the cap there will be more pages, so this is the final result
                d['downloadCount'] = f"{dc}+"
            
            else:
                # if we get here we saw all the pages and know what the real number is so use that
                d['downloadCount'] = dc

            entries.append(d)

        abort = False
        if self.already_found:
            before = len(entries)
            entries = [e for e in entries if e.get("id") not in self.already_found]
            if len(entries) < before:
                abort = True

        self.accumulate.extend(entries)

        if not abort and releases['pageInfo']['hasNextPage']:
            self.cursor = releases['pageInfo']['endCursor']
            return None, [self]

        return {self.filename:self.accumulate + self.existing}, []

class RepoInfo:
    filename = "repo_info"
    def __init__(self):
        pass
    def query(self):
        return graphql.repo_query()
    def process_to_file(self, data):
        follow_on_tasks = []
        output = dict(
            url = data['data']['repository']['url'],
            fork_count = data['data']['repository']['forkCount'],
            stargazer_count = data['data']['repository']['stargazerCount'],
            watchers_count = data['data']['repository']['watchers']['totalCount'])
        return {self.filename: output}, follow_on_tasks

class Repo:
    def __init__(self, repo_name):
        self.repo_name = repo_name
        owner, name = repo_name.split('/')
        self.owner = owner
        self.name = name
        self.issues = dict()
        self.pull_requests = dict()
        self.commits = dict()
        self.info = None

    def has_issue(self, issueId):
        return issueId in self.issues
    def has_pull_request(self, pr):
        return pr in self.pull_requests
    def add_issue(self, issueId, existing=False):
        if issueId not in self.issues:
            i = Issue(issueId)
            i.existing = existing
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

    def add_pull_request(self, issueId, existing=False):
        if issueId not in self.pull_requests:
            i = PullRequest(issueId)
            i.existing = existing
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

class Issue:
    def __init__(self, issueId):
        self.issueId = issueId
        self.events = []
        self._complete = False
        self.cursor = ""
        self.info = None
        self.existing = False

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

