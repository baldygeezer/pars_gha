import logging
import typing
import time
import sys
import json
from pathlib import Path

import click
from decouple import config

import requests

logger = logging.getLogger(__name__)

graphql_endpoint = config('ENDPOINT', default='https://api.github.com/graphql')
graphql_token = config('TOKEN')

graphql_fragment_common_items = '''
... on AddedToProjectEvent
{ id createdAt actor { url login __typename } }
... on AssignedEvent
{ id createdAt actor { url login __typename } user { url login __typename } }
... on ClosedEvent
{ id createdAt stateReason actor { url login __typename } }
... on CommentDeletedEvent
{ id createdAt actor { url login __typename } deletedCommentAuthor { url login __typename } }
... on ConnectedEvent
{ id createdAt actor { url login __typename } source { ... on UniformResourceLocatable { url } } subject { ... on UniformResourceLocatable { url } } }
... on ConvertedNoteToIssueEvent
{ id createdAt actor { url login __typename} }
... on ConvertedToDiscussionEvent
{ id createdAt actor { url login __typename} }
... on CrossReferencedEvent
{ id createdAt actor { url login __typename} referencedAt source { ... on UniformResourceLocatable { url } } target { ... on UniformResourceLocatable { url } } }
... on DemilestonedEvent
{ id createdAt actor { url login __typename} }
... on DisconnectedEvent
{ id createdAt actor { url login __typename} source { ... on UniformResourceLocatable { url } } subject { ... on UniformResourceLocatable { url } } }
... on IssueComment
{ id createdAt author { url login __typename} body includesCreatedEdit isMinimized lastEditedAt minimizedReason publishedAt pullRequest { url } }
... on LabeledEvent
{ id createdAt actor { url login __typename} label { name } }
... on LockedEvent
{ id createdAt actor { url login __typename} lockReason }
... on MarkedAsDuplicateEvent
{ id createdAt actor { url login __typename} canonical { __typename ... on Issue {url} ... on PullRequest {url}} duplicate { __typename ... on Issue {url} ... on PullRequest {url}} isCrossRepository }
... on MentionedEvent
{ id databaseId createdAt actor { url login __typename } }
... on MilestonedEvent
{ id createdAt actor { url login __typename } milestoneTitle }
... on MovedColumnsInProjectEvent
{ id databaseId createdAt actor { url login __typename } }
... on PinnedEvent
{ id createdAt actor { url login __typename } }
... on ReferencedEvent
{ id createdAt actor { url login __typename } commit { commitUrl oid } commitRepository { nameWithOwner} isCrossRepository isDirectReference }
... on RemovedFromProjectEvent
{ id createdAt databaseId actor { url login __typename } }
... on RenamedTitleEvent
{ id createdAt actor { url login __typename } currentTitle previousTitle}
... on ReopenedEvent
{ id createdAt stateReason actor { url login __typename } }
... on SubscribedEvent
{ id createdAt actor { url login __typename } }
... on TransferredEvent
{ id createdAt actor { url login __typename } issue { url } fromRepository { nameWithOwner } }
... on UnassignedEvent
{ id createdAt actor { url login __typename } assignee { __typename ... on User { url login __typename } } }
... on UnlabeledEvent
{ id createdAt actor { url login __typename } label { name } }
... on UnlockedEvent
{ id createdAt actor { url login __typename} }
... on UnmarkedAsDuplicateEvent
{ id createdAt actor { url login __typename} canonical { __typename ... on Issue {url} ... on PullRequest {url}} duplicate { __typename ... on Issue {url} ... on PullRequest {url}} isCrossRepository }
... on UnpinnedEvent
{ id createdAt actor { url login __typename } }
... on UnsubscribedEvent
{ id createdAt actor { url login __typename } }
... on UserBlockedEvent
{ id createdAt actor { url login __typename } subject { url login __typename } }
'''

graphql_fragment_issue_items = '''
fragment FragmentTimelineNode on IssueTimelineItems {
              __typename
              ... on UniformResourceLocatable { url }
              ... on Node { id }
''' + graphql_fragment_common_items + '''
}
'''

graphql_fragment_pr_items = '''
fragment FragmentPRTimelineNode on PullRequestTimelineItems {
              __typename
              ... on UniformResourceLocatable { url }
              ... on Node { id }
''' + graphql_fragment_common_items + '''
...  on AddedToMergeQueueEvent 
{ id createdAt actor { url login __typename } enqueuer { url login __typename } }
...  on AutoMergeDisabledEvent
{ id createdAt actor { url login __typename } reason reasonCode }
...  on AutoMergeEnabledEvent
{ id createdAt actor { url login __typename } enabler { url login __typename } }
...  on AutoRebaseEnabledEvent
{ id createdAt actor { url login __typename } enabler { url login __typename } }
...  on AutoSquashEnabledEvent
{ id createdAt actor { url login __typename } enabler { url login __typename } }
...  on AutomaticBaseChangeFailedEvent
{ id createdAt actor { url login __typename } newBase oldBase }
...  on AutomaticBaseChangeSucceededEvent
{ id createdAt actor { url login __typename } newBase oldBase }
...  on BaseRefChangedEvent
{ id createdAt actor { url login __typename } currentRefName previousRefName }
...  on BaseRefDeletedEvent
{ id createdAt actor { url login __typename } baseRefName }
...  on BaseRefForcePushedEvent
{ id createdAt actor { url login __typename } afterCommit { commitUrl oid } beforeCommit { commitUrl oid } }
...  on ConvertToDraftEvent
{ id createdAt actor { url login __typename } }
...  on DeployedEvent
{ id createdAt actor { url login __typename } }
...  on DeploymentEnvironmentChangedEvent
{ id createdAt actor { url login __typename } }
...  on HeadRefDeletedEvent
{ id createdAt actor { url login __typename } }
...  on HeadRefForcePushedEvent
{ id createdAt actor { url login __typename } }
...  on HeadRefRestoredEvent
{ id createdAt actor { url login __typename } }
...  on MergedEvent
{ id createdAt actor { url login __typename } commit { commitUrl oid } }
...  on PullRequestCommit
{ id commit { commitUrl oid } }
...  on PullRequestReview
{ id createdAt author { url login __typename } body commit { commitUrl oid } }
...  on PullRequestRevisionMarker
{ createdAt }
...  on ReadyForReviewEvent
{ id createdAt actor { url login __typename } resourcePath}
...  on RemovedFromMergeQueueEvent
{ id createdAt actor { url login __typename } reason beforeCommit { commitUrl oid } }
...  on RemovedFromProjectEvent
{ id createdAt actor { url login __typename } }
...  on ReviewDismissedEvent
{ id createdAt actor { url login __typename } }
...  on ReviewRequestRemovedEvent
{ id createdAt actor { url login __typename } }
...  on ReviewRequestedEvent
{ id createdAt actor { url login __typename } }
}
'''
#...  on PullRequestCommitCommentThread
#...  on PullRequestReviewThread

graphql_fragment_issue_info = '''
fragment FragmentIssueInfo on Issue {
        __typename
        id
        databaseId
        number
        title
        author { url login __typename }
        body
        createdAt

        closed
        closedAt
        updatedAt
        state
        stateReason
        url
}
'''
issue_persist = [ '__typename', 'id', 'databaseId', 'number', 'title', 'author', 'body', 'createdAt', 'closed',
        'closedAt', 'updatedAt', 'state', 'stateReason', 'url' ]

graphql_fragment_pr_info = '''
fragment FragmentPullRequestInfo on PullRequest {
        __typename
        id
        databaseId
        number
        title
        author { url login __typename }
        body
        createdAt
        baseRefName
        baseRepository { nameWithOwner url } 

        closed
        closedAt
        updatedAt
        state
        url
        mergeCommit { commitUrl oid }
        merged
        mergedAt
        mergedBy { url login __typename }
}
'''

pull_request_persist = [ '__typename', 'id', 'databaseId', 'number', 'title', 'author', 'body', 'createdAt', 'baseRefName', 'baseNameRepository', 'closed',
        'closedAt', 'updatedAt', 'state', 'stateReason', 'url', 'mergeCommit', 'merged', 'mergedAt', 'mergedBy']

def qraphql_initial_issues_query():
    return f'''{graphql_fragment_issue_info}
{graphql_fragment_issue_items}
query initial_issues($owner: String!, $name: String!, $num_issues: Int!, $num_events: Int!) {{
  repository(owner: $owner, name: $name) {{
    issues(first: $num_issues) {{
      nodes {{
        ...FragmentIssueInfo
        timelineItems(first: $num_events) {{
          totalCount
          edges {{
            node {{
              ...FragmentTimelineNode
            }}
          }}
          pageInfo {{
            endCursor
            hasNextPage
          }}
        }}
      }}
      totalCount
      pageInfo {{
        endCursor
        hasNextPage
      }}
    }}
  }}
}}
'''

def qraphql_initial_pull_requests_query():
    return f'''{graphql_fragment_pr_info}
{graphql_fragment_pr_items}
query initial_pull_requests($owner: String!, $name: String!, $num_issues: Int!, $num_events: Int!) {{
  repository(owner: $owner, name: $name) {{
    pullRequests(first: $num_issues) {{
      nodes {{
        ...FragmentPullRequestInfo
        timelineItems(first: $num_events) {{
          totalCount
          edges {{
            node {{
              ...FragmentPRTimelineNode
            }}
          }}
          pageInfo {{
            endCursor
            hasNextPage
          }}
        }}
      }}
      totalCount
      pageInfo {{
        endCursor
        hasNextPage
      }}
    }}
  }}
}}
'''

def qraphql_ongoing_pull_request_query(cursor):
    return f'''{graphql_fragment_pr_info}
{graphql_fragment_pr_items}
query ongoing($owner: String!, $name: String!, $num_issues: Int!, $num_events: Int!) {{
  repository(owner: $owner, name: $name) {{
    pullRequests(first: $num_issues, after: "{cursor}") {{
      nodes {{
        ...FragmentPullRequestInfo
        timelineItems(first: $num_events) {{
          totalCount
          edges {{
            node {{
              ...FragmentPRTimelineNode
            }}
          }}
          pageInfo {{
            endCursor
            hasNextPage
          }}
        }}
      }}
      totalCount
      pageInfo {{
        endCursor
        hasNextPage
      }}
    }}
  }}
}}
'''


def qraphql_ongoing_query(cursor):
    return f'''{graphql_fragment_issue_info}
{graphql_fragment_issue_items}
query ongoing($owner: String!, $name: String!, $num_issues: Int!, $num_events: Int!) {{
  repository(owner: $owner, name: $name) {{
    issues(first: $num_issues, after: "{cursor}") {{
      nodes {{
        ...FragmentIssueInfo
        timelineItems(first: $num_events) {{
          totalCount
          edges {{
            node {{
              ...FragmentTimelineNode
            }}
          }}
          pageInfo {{
            endCursor
            hasNextPage
          }}
        }}
      }}
      totalCount
      pageInfo {{
        endCursor
        hasNextPage
      }}
    }}
  }}
}}
'''

def graphql_follow_on(issue):
    return f'''
      issue{issue.issueId}: issue(number: {issue.issueId}) {{
        number
        timelineItems(first: $num_events, after: "{issue.cursor}") {{
          totalCount
          edges {{
            node {{
              ...FragmentTimelineNode
            }}
          }}
          pageInfo {{
            endCursor
            hasNextPage
          }}
        }}
      }}
'''

def graphql_pull_requests_follow_on(pr):
    return f'''
      pull_request{pr.issueId}: issue(number: {pr.issueId}) {{
        number
        timelineItems(first: $num_events, after: "{pr.cursor}") {{
          totalCount
          edges {{
            node {{
              ...FragmentPullRequestInfo
            }}
          }}
          pageInfo {{
            endCursor
            hasNextPage
          }}
        }}
      }}
'''

def graphql_fill_query(issues):
    issues_query = "\n".join([graphql_follow_on(i) for i in issues])
    return (graphql_fragment_issue_items + '''\
            query fill($owner: String!, $name: String!, $num_events: Int!) {
  repository(owner: $owner, name: $name) {
     ''' + issues_query + '''\
  }
}
''')

def graphql_pr_fill_query(prs):
    prs_query = "\n".join([graphql_pull_requests_follow_on(i) for i in prs])
    return (graphql_fragment_pr_items + '''\
            query fill($owner: String!, $name: String!, $num_events: Int!) {
  repository(owner: $owner, name: $name) {
     ''' + prs_query + '''\
  }
}
''')

class BaseAction:
    def __init__(self):
        pass

class IssuesPage:
    def __init__(self, cursor):
        self.cursor = cursor
    def query(self):
        return qraphql_ongoing_query(self.cursor)
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

class PullRequestsPage:
    def __init__(self, cursor):
        self.cursor = cursor
    def query(self):
        return qraphql_ongoing_pull_request_query(self.cursor)
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
        return qraphql_initial_issues_query()

class InitialPullRequests(PullRequestsPage):
    def __init__(self):
        pass
    def query(self):
        return qraphql_initial_pull_requests_query()

class IssuesEventsPage:
    def __init__(self, issues):
        self.issues = issues
    def query(self):
        return graphql_fill_query(self.issues)
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
        return graphql_fill_query(self.prs)
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

def fetch(repo: str):
    print(repo)
    r = Repo(repo)

    poster = Poster()

    queryIssues = InitialIssues()
    queryPRs = InitialPullRequests()

    crawling = True
    tasks = [queryIssues, queryPRs]
    tasks = [queryPRs]

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

@cli.command(name='crawl')
@click.argument('repo') # '-r', '--repo', 'repos', required=True, help='repo to crawl')
def crawl(
    repo
):
    repos = [repo]
    for r in repos:
        #try:
           fetch(r)
        #except Exception as e:
        #   print(e)

if __name__ == '__main__':
    cli()
