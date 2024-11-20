import logging
import typing

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

def qraphql_initial_query(num_issues=1, num_events=1):
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

def qraphql_ongoing_query(cursor, num_issues=1, num_events=1):
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

def graphql_follow_on(issue, num_issues=1, num_events=1):
    return f'''
      issue(number: {issue.issueId}) {{
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

def graphql_fill_query(issues, num_issues=1, num_events=1):
    issues_query = "\n".join([graphql_follow_on(i, num_issues=num_issues, num_events=num_events) for i in issues])
    return (graphql_fragment_issue_items + '''\
            query fill($owner: String!, $name: String!, $num_issues: Int!, $num_events: Int!) {
  repository(owner: $owner, name: $name) {
     ''' + issues_query + '''\
  }
}
''')

class BaseAction:
    def __init__(self):
        pass

class Initial:
    def __init__(self):
        pass
    def query(self, num_issues=1, num_events=1):
        return qraphql_initial_query(num_issues=2)

class IssuePage:
    def __init__(self, cursor):
        self.cursor = cursor
    def query(self, num_issues=1, num_events=1):
        return qraphql_initial_query(num_issues=num_issues, num_events=num_events)

class IssuesEventsPage:
    def __init__(self, issues):
        self.issues = issues
    def query(self, num_issues=1, num_events=1):
        return graphql_fill_query(self.issues, num_issues=1, num_events=1)

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

def fetch(repo: str):
    print(repo)
    r = Repo(repo)

    query = qraphql_initial_query(num_issues=2)
    next_query = Initial().query(num_issues=2)
    if query != next_query:
        print("not ok")
        return

    body = {
            'query': query,
            'variables': {
                'owner': r.owner,
                'name': r.name,
                'num_issues': 2,
                'num_events': 2
            }
    }
    headers = {'Content-type': 'application/json', 'Authorization': f'Bearer {graphql_token}'}
    resp = requests.post(graphql_endpoint, json=body, headers=headers)
    print(query)
    print(resp.status_code)
    print(resp.text)
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
    data = resp.json()
    if not validate(data):
        raise(Exception(f'failed to validate: {data["errors"]}'))

    issues = data['data']['repository']['issues']
    for issue in issues['nodes']:
        num = issue['number']
        print(num)
        r.add_issue(num)

        timeline = issue['timelineItems']
        events = map(lambda x: x['node'], timeline['edges'])
        r.issues[num].add_events(events)
        r.issues[num].complete(not timeline['pageInfo']['hasNextPage'])
        r.issues[num].cursor = timeline['pageInfo']['endCursor']
        print(r.issues[num])

    print(r.complete_issues(), r.incomplete_issues())
    for i in r.complete_issues():
        print(f'complete {i}')

    inc = r.incomplete_issues()
    if inc:
        print(f'not complete {len(inc)}')
        next_query = graphql_fill_query([r.issues[i] for i in inc])
        check_query = IssuesEventsPage([r.issues[i] for i in inc]).query()
        if next_query!=check_query:
            print(next_query)
        else:
            print("was ok")

    if issues['pageInfo']['hasNextPage']:
        print(f'would requery, with cursor: {issues["pageInfo"]["endCursor"]}')
        query = qraphql_ongoing_query(issues["pageInfo"]["endCursor"])
        body = {
            'query': query,
            'variables': {
                'owner': r.owner,
                'name': r.name,
                'num_issues': 2,
                'num_events': 2
            }
        }
        headers = {'Content-type': 'application/json', 'Authorization': f'Bearer {graphql_token}'}
        resp = requests.post(graphql_endpoint, json=body, headers=headers)
        print(query)
        print(resp.status_code)
        print(resp.text)
        # hasMoreIssues

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
