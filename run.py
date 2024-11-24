import logging
import typing
import time
import sys

import click
from decouple import config

import requests

logger = logging.getLogger(__name__)

graphql_endpoint = config('ENDPOINT', default='https://api.github.com/graphql')
graphql_token = config('TOKEN')

graphql_fragment_issue_items = '''
fragment FragmentTimelineNode on IssueTimelineItems {
              __typename
              ... on UniformResourceLocatable { url }
              ... on Node { id }
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
{ id createdAt actor { url login __typename} }
... on DemilestonedEvent
{ id createdAt actor { url login __typename} }
... on DisconnectedEvent
{ id createdAt actor { url login __typename} }
... on IssueComment
{ id createdAt author { url login __typename} }
... on LabeledEvent
{ id createdAt actor { url login __typename} label { name } }
... on LockedEvent
{ id createdAt actor { url login __typename} lockReason }
... on MarkedAsDuplicateEvent
{ id createdAt actor { url login __typename} canonical { __typename ... on Issue {url} ... on PullRequest {url}} duplicate { __typename ... on Issue {url} ... on PullRequest {url}} }
... on MentionedEvent
{ id databaseId createdAt actor { url login __typename } }
... on MilestonedEvent
{ id createdAt actor { url login __typename } }
... on MovedColumnsInProjectEvent
{ id databaseId createdAt actor { url login __typename } }
... on PinnedEvent
{ id createdAt actor { url login __typename } }
... on ReferencedEvent
{ id createdAt actor { url login __typename } }
... on RemovedFromProjectEvent
{ id createdAt databaseId actor { url login __typename } }
... on RenamedTitleEvent
{ id createdAt actor { url login __typename } }
... on ReopenedEvent
{ id createdAt stateReason actor { url login __typename } }
... on SubscribedEvent
{ id createdAt actor { url login __typename } }
... on TransferredEvent
{ id createdAt actor { url login __typename } issue { url } }
... on UnassignedEvent
{ id createdAt actor { url login __typename } assignee { __typename ... on User { url login __typename } } }
... on UnlabeledEvent
{ id createdAt actor { url login __typename } label { name } }
... on UnlockedEvent
{ id createdAt actor { url login __typename} }
... on UnmarkedAsDuplicateEvent
{ id createdAt actor { url login __typename} canonical { __typename ... on Issue {url} ... on PullRequest {url}} duplicate { __typename ... on Issue {url} ... on PullRequest {url}} }
... on UnpinnedEvent
{ id createdAt actor { url login __typename } }
... on UnsubscribedEvent
{ id createdAt actor { url login __typename } }
... on UserBlockedEvent
{ id createdAt actor { url login __typename } }
}
'''

graphql_fragment_issue_info = '''
fragment FragmentIssueInfo on Issue {
        id
        databaseId
        number
        author { url login __typename }
        closed
        closedAt
        state
        stateReason
        url
}
'''

def qraphql_initial_query():
    return f'''{graphql_fragment_issue_info}
{graphql_fragment_issue_items}
query initial($owner: String!, $name: String!, $num_issues: Int!, $num_events: Int!) {{
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

def graphql_fill_query(issues):
    issues_query = "\n".join([graphql_follow_on(i) for i in issues])
    return (graphql_fragment_issue_items + '''\
            query fill($owner: String!, $name: String!, $num_events: Int!) {
  repository(owner: $owner, name: $name) {
     ''' + issues_query + '''\
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
            r.add_issue(num)

            timeline = issue['timelineItems']
            events = map(lambda x: x['node'], timeline['edges'])
            r.issues[num].add_events(events)
            r.issues[num].complete(not timeline['pageInfo']['hasNextPage'])
            r.issues[num].cursor = timeline['pageInfo']['endCursor']
        if issues['pageInfo']['hasNextPage']:
            return [IssuesPage(issues["pageInfo"]["endCursor"])]

        return []

class Initial(IssuesPage):
    def __init__(self):
        pass
    def query(self):
        return qraphql_initial_query()

class IssuesEventsPage:
    def __init__(self, issues):
        self.issues = issues
    def query(self):
        return graphql_fill_query(self.issues)
    def process(self, data, r):
        issues = data['data']['repository']
        print(f'not sure what todo here: {data}')
        for k, issue in issues.items():
            num = issue['number']
            timeline = issue['timelineItems']
            events = map(lambda x: x['node'], timeline['edges'])
            r.issues[num].add_events(events)
            r.issues[num].complete(not timeline['pageInfo']['hasNextPage'])
            r.issues[num].cursor = timeline['pageInfo']['endCursor']
        return []

class Issue:
    def __init__(self, issueId):
        self.issueId = issueId
        self.events = []
        self._complete = False
        self.cursor = ""

    def add_events(self, el):
        self.events.extend(el)

    def set_cursor(self, cursor):
        self.cursor = cursor

    def complete(self, b):
        self._complete = b

    def isComplete(self):
        return self._complete

class Repo:
    def __init__(self, repo_name):
        self.repo_name = repo_name
        owner, name = repo_name.split('/')
        self.owner = owner
        self.name = name
        self.issues = dict()

    def add_issue(self, issueId):
        if issueId not in self.issues:
            i = Issue(issueId)
            self.issues[issueId] = i
    def incomplete_issues(self):
        return [i for i in self.issues.keys() if not self.issues[i].isComplete()]
    def complete_issues(self):
        return [i for i in self.issues.keys() if self.issues[i].isComplete()]

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
        print(f'rate limit: remaining: {self.remaining} reset: {self.reset_at}', file=sys.stderr)

        return resp

def fetch(repo: str):
    print(repo)
    r = Repo(repo)

    poster = Poster()

    query = Initial()

    crawling = True
    tasks = [query]

    count = 0
    while(tasks and count<20):
        t = tasks.pop()
        query = t.query()
        body = {
                'query': query,
                'variables': {
                    'owner': r.owner,
                    'name': r.name,
                    'num_issues': 10,
                    'num_events': 2
                }
        }
        resp = poster.post(body)
        count = count + 1
        print(resp.status_code)

        data = resp.json()
        if not validate(data):
            raise(Exception(f'failed to validate: {data["errors"]}'))
        next_tasks = t.process(data, r)

        print(r.complete_issues(), r.incomplete_issues())

        if next_tasks:
            tasks.extend(next_tasks)

        for i in r.complete_issues():
            print(f'complete {i}')

        inc = r.incomplete_issues()
        if len(inc) > 0 and (len(inc) > 10 or len(tasks)==0):
            print(f'not complete {len(inc)}')
            fill = IssuesEventsPage([r.issues[i] for i in inc])
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

    '''
{
  "data": {
    "repository": {
      "issues": {
        "nodes": [
          {
            "id": "MDU6SXNzdWU4NjMwOTU=",
            "databaseId": 863095,
            "number": 1,
            "author": {
              "url": "https://github.com/ahankinson",
              "login": "ahankinson",
              "__typename": "User"
            },
            "closed": true,
            "closedAt": "2011-08-28T13:06:10Z",
            "state": "CLOSED",
            "stateReason": "COMPLETED",
            "url": "https://github.com/libvips/libvips/issues/1"
          }
        ],
        "totalCount": 2346,
        "pageInfo": {
          "endCursor": "Y3Vyc29yOnYyOpK5MjAxMS0wNS0wN1QyMDoxMjoyMyswMTowMM4ADSt3",
          "hasNextPage": true
        }
      }
    }
  }
}
    '''
    '''
    body = {
            'query': query,
            'variables': {
                'owner': r.owner,
                'name': r.name,
                'num_issues': 2,
                'num_events': 2
            }
    }
    resp = poster.post(body)
    print(query)
    print(resp.status_code)
    print(resp.text)
    data = resp.json()
    if not validate(data):
        raise(Exception(f'failed to validate: {data["errors"]}'))

    '''
