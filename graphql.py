from typing import List

from model import *
from github import *

fragment_common_items = "\n".join([x.fragment() for x in
[ AddedToProjectEvent, AssignedEvent, ClosedEvent, CommentDeletedEvent,
ConnectedEvent, ConvertedNoteToIssueEvent, ConvertedToDiscussionEvent,
CrossReferencedEvent, DemilestonedEvent, DisconnectedEvent, IssueComment,
LabeledEvent, LockedEvent, MarkedAsDuplicateEvent, MentionedEvent,
MilestonedEvent, MovedColumnsInProjectEvent, PinnedEvent,
ReferencedEvent, RemovedFromProjectEvent, RenamedTitleEvent,
ReopenedEvent, SubscribedEvent, TransferredEvent, UnassignedEvent,
UnlabeledEvent, UnlockedEvent, UnmarkedAsDuplicateEvent, UnpinnedEvent,
UnsubscribedEvent, UserBlockedEvent]])

fragment_issue_items = '''
fragment FragmentTimelineNode on IssueTimelineItems {
              __typename
              ... on UniformResourceLocatable { url }
              ... on Node { id }
''' + fragment_common_items + '''
}
'''

fragment_pull_request_specific_items = "\n".join([x.fragment() for x in [
AddedToMergeQueueEvent, AutoMergeDisabledEvent,
AutoMergeEnabledEvent, AutoRebaseEnabledEvent,
AutoSquashEnabledEvent, AutomaticBaseChangeFailedEvent,
AutomaticBaseChangeSucceededEvent, BaseRefChangedEvent,
BaseRefDeletedEvent, BaseRefForcePushedEvent, ConvertToDraftEvent,
DeployedEvent, DeploymentEnvironmentChangedEvent, HeadRefDeletedEvent,
HeadRefForcePushedEvent, HeadRefRestoredEvent, MergedEvent,
PullRequestCommit, PullRequestReview, PullRequestRevisionMarker,
ReadyForReviewEvent, RemovedFromMergeQueueEvent, RemovedFromProjectEvent,
ReviewDismissedEvent, ReviewRequestRemovedEvent, ReviewRequestedEvent]])

fragment_pull_request_items = '''
fragment FragmentPRTimelineNode on PullRequestTimelineItems {
              __typename
              ... on UniformResourceLocatable { url resourcePath }
              ... on Node { id }
''' + fragment_common_items + '''
''' + fragment_pull_request_specific_items + '''
}
'''
#...  on PullRequestCommitCommentThread
#...  on PullRequestReviewThread


fragment_issue_info = '''
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

fragment_pull_request_info = '''
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

def pull_requests_query(cursor: str | None = None) -> str:
    """
    This constructs the follow on query for pull requests on a repository

    Args:
        cursor (str): the cursor to use

    Returns:
        A graphql query string that expects
            owner - the repo owner
            name - the repo name
            num_issues - number of pull requests to request
            num_events - number of events per pull requests to request

    """
    after = ""
    if cursor:
       after = 'after: "' + cursor + '",'

    return f'''{fragment_pull_request_info}
{fragment_pull_request_items}
query ongoing($owner: String!, $name: String!, $num_issues: Int!, $num_events: Int!) {{
  repository(owner: $owner, name: $name) {{
    pullRequests(first: $num_issues, {after} orderBy: {{field: CREATED_AT, direction: DESC}}) {{
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


def issues_query(cursor: str| None = None) -> str:
    """
    This constructs the follow on query for issues on a repository

    Args:
        cursor (str): the cursor to use

    Returns:
        A graphql query string that expects
            owner - the repo owner
            name - the repo name
            num_issues - number of issues to request
            num_events - number of events per issues to request
    """
    after = ""
    if cursor:
       after = 'after: "' + cursor + '",'
    return f'''{fragment_issue_info}
{fragment_issue_items}
query ongoing($owner: String!, $name: String!, $num_issues: Int!, $num_events: Int!) {{
  repository(owner: $owner, name: $name) {{
    issues(first: $num_issues, {after} orderBy: {{field: CREATED_AT, direction: DESC}}) {{
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

def issues_follow_on(issue: Issue) -> str:
    """
    This constructs a query for events on an issue using a cursor as the starting point.
    It the form issue1234 is generated in the output

    Args:
        issue (Issue): the issue to find events for

    Returns:
        A graphql query str that expects
            num_issues - number of issues to request
            num_events - number of events per issues to request
    """
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

def pull_requests_follow_on(pr: PullRequest) -> str:
    """
    This constructs a query for events on a pull request using a cursor as the starting point.
    It the form pull_request1234 is generated in the output

    Args:
        pr (PullRequest): the issue to find events for

    Returns:
        A graphql query string that expects
            num_issues - number of issues to request
            num_events - number of events per issues to request
    """
    return f'''
      pull_request{pr.issueId}: pullRequest(number: {pr.issueId}) {{
        number
        timelineItems(first: $num_events, after: "{pr.cursor}") {{
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
'''

def issues_fill_query(issues: List[Issue]) -> str:
    """
    This constructs a query for events on a number of issues.
    Each issue is expected to have a cursor.
    The final query will query each of the issues for more events

    Args:
        issues (List[Issue]): the issue to find events for

    Returns:
        A graphql query string that expects
            num_events - number of events per issues to request
    """
    issues_query = "\n".join([issues_follow_on(i) for i in issues])
    return (fragment_issue_items + '''\
            query fill($owner: String!, $name: String!, $num_events: Int!) {
  repository(owner: $owner, name: $name) {
     ''' + issues_query + '''\
  }
}
''')

def pull_requests_fill_query(prs: List[PullRequest]) -> str:
    """
    This constructs a query for events on a number of pull requests.
    Each pull requests is expected to have a cursor.
    The final query will query each of the pull requests for more events

    Args:
        prs (List[PullRequest]): the pull request to find events for

    Returns:
        A graphql query string that expects
            num_events - number of events per pull request to request
    """
    prs_query = "\n".join([pull_requests_follow_on(i) for i in prs])
    return (fragment_pull_request_items + '''\
            query fill($owner: String!, $name: String!, $num_events: Int!) {
  repository(owner: $owner, name: $name) {
     ''' + prs_query + '''\
  }
}
''')


def parse_actor(actor_data):
    """Helper function to parse an actor."""
    return Actor(
        url=actor_data['url'],
        login=actor_data['login'],
        typename=actor_data['__typename']
    )

def parse_user(user_data):
    """Helper function to parse a user."""
    return User(
        url=user_data['url'],
        login=user_data['login'],
        typename=user_data['__typename']
    )

def parse_uniform_resource_locatable(data):
    """Helper function to parse UniformResourceLocatable."""
    return UniformResourceLocatable(url=data['url'])

def parse_commit(commit_data):
    """Helper function to parse a commit."""
    return Commit(
        commit_url=commit_data['commitUrl'],
        oid=commit_data['oid'],
        date=commit_data['committedDate'],
        author=author
    )
def parse_issue(issue_data):
    return Issue()

def parse_pull_request(pull_request_data):
    return PullRequest

def parse_repository(repository_data):
    """Helper function to parse a repository."""
    return Repository(name_with_owner=repository_data['nameWithOwner'])

def parse_event(event_data):
    """Parse a single event from the data."""
    event_type = event_data['__typename']
    ec = allEvents.get(event_type, None)
    if not ec:
        return None
    return ec.parse(event_data)

def commits_query(cursor: str | None = None) -> str:
    after = ""
    if cursor:
       after = 'after: "' + cursor + '",'
    return f'''
query get_commits($owner: String!, $name: String!, $num_commits: Int!) {{
  repository(owner: $owner, name: $name) {{
    defaultBranchRef {{
      target {{
        ... on Commit {{
          history(first: $num_commits {after}) {{
            edges {{
              node {{
                oid
                commitUrl
                message
                committedDate
                authoredDate
                author {{
                  name
                  email
                  user {{ url login __typename }}
                }}
                committer {{
                  name
                  email
                  user {{ url login __typename }}
                }}
              }}
            }}
            pageInfo {{
              endCursor
              hasNextPage
            }}
          }}
        }}
      }}
    }}
  }}
}}
'''

def stargazers_query(cursor: str | None = None) -> str:
    after = ""
    if cursor:
       after = 'after: "' + cursor + '",'
    """
    This constructs a query to grab stargazers

    Returns:
        A graphql query string tha expects
            owner - the repo owner
            name - the repo name
            ref - the reference (qualifiedName) to use
            num_per_page - number of items per page
    """
    return f'''
query repository_stargazers($owner: String!, $name: String!, $num_per_page: Int!) {{
  repository(owner: $owner, name: $name) {{
    stargazers(first: $num_per_page, {after} orderBy: {{field: STARRED_AT, direction: DESC}}) {{ edges {{
        starredAt
        node {{
          url
        }}
      }}
      pageInfo {{
        hasNextPage
        endCursor
      }}
    }}
  }}
}}
'''

def releases_query(cursor: str | None = None) -> str:
    after = ""
    if cursor:
       after = 'after: "' + cursor + '",'
    """
    This constructs a query to grab releases

    Returns:
        A graphql query string tha expects
            owner - the repo owner
            name - the repo name
            num_per_page - number of items per page
    """
    return f'''
query repository_releases($owner: String!, $name: String!) {{
  repository(owner: $owner, name: $name) {{
    releases(first: 20, {after} orderBy: {{field: CREATED_AT, direction: DESC}}) {{ edges {{
        node {{
          id
          name
          createdAt
          author {{ url login __typename }}
          url
          tagCommit {{ commitUrl oid }}
          releaseAssets(first: 20) {{
            edges {{
              node {{
                downloadCount
              }}
            }}
            pageInfo {{
                hasNextPage
            }}
          }}
        }}
      }}
      pageInfo {{
        hasNextPage
        endCursor
      }}
    }}
  }}
}}
'''

def repo_query() -> str:
    """
    This constructs a query to grab basic information about a repo

    Returns:
        A graphql query string tha expects
            owner - the repo owner
            name - the repo name
    """
    return f'''
query repository_info($owner: String!, $name: String!) {{
  repository(owner: $owner, name: $name) {{
    url
    forkCount
    stargazerCount
    watchers {{
      totalCount
    }}
  }}
}}
'''

'''
doi: in:readme 2026-01-01..2026-01-31 sort:created
'''
def search_repos(cursor: str | None = None, include_readme: bool = False) -> str:
    after = ""
    if cursor:
       after = 'after: "' + cursor + '",'
    
    readme_field = ""
    if include_readme:
        readme_field = '''
          readme: object(expression:"HEAD:README.md") {
            ... on Blob {
              text
            }
          }
        '''

    return f'''
query search($term: String!, $num_per_page: Int!) {{
  search(query: $term, type: REPOSITORY, {after} first: $num_per_page) {{
    edges {{
      node {{
        ... on Repository {{
          nameWithOwner
          createdAt
          {readme_field}
        }}
      }}
    }}
    repositoryCount
    pageInfo {{
      hasNextPage
      endCursor
    }}
  }}
}}
'''

