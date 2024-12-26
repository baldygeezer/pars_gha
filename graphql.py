from typing import List

from model import Issue, PullRequest

fragment_common_items = '''
... on AddedToProjectEvent
{ id createdAt actor { url login __typename } }
... on AssignedEvent
{ id createdAt actor { url login __typename } user { url login __typename } }
... on ClosedEvent
{ id createdAt actor { url login __typename } stateReason }
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
{ id createdAt actor { url login __typename } }
... on PinnedEvent
{ id createdAt actor { url login __typename } }
... on ReferencedEvent
{ id createdAt actor { url login __typename } commit { commitUrl oid } commitRepository { nameWithOwner} isCrossRepository isDirectReference }
... on RemovedFromProjectEvent
{ id createdAt actor { url login __typename } }
... on RenamedTitleEvent
{ id createdAt actor { url login __typename } currentTitle previousTitle}
... on ReopenedEvent
{ id createdAt actor { url login __typename } stateReason}
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

fragment_issue_items = '''
fragment FragmentTimelineNode on IssueTimelineItems {
              __typename
              ... on UniformResourceLocatable { url }
              ... on Node { id }
''' + fragment_common_items + '''
}
'''

fragment_pull_request_items = '''
fragment FragmentPRTimelineNode on PullRequestTimelineItems {
              __typename
              ... on UniformResourceLocatable { url }
              ... on Node { id }
''' + fragment_common_items + '''
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

def issues_initial_query() -> str:
    """
    This constructs the first query for issues on a repository

    Returns:
        A graphql query string that expects
            owner - the repo owner
            name - the repo name
            num_issues - number of issues to request
            num_events - number of events per issue to request
    """
    return f'''{fragment_issue_info}
{fragment_issue_items}
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

def pull_requests_initial_query() -> str:
    """
    This constructs the first query for pull requests on a repository

    Returns:
        A graphql query string that expects
            owner - the repo owner
            name - the repo name
            num_issues - number of pull requests to request
            num_events - number of events per pull requests to request
    """
    return f'''{fragment_pull_request_info}
{fragment_pull_request_items}
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

def pull_requests_ongoing_query(cursor: str) -> str:
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
    return f'''{fragment_pull_request_info}
{fragment_pull_request_items}
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


def issues_ongoing_query(cursor: str) -> str:
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
    return f'''{fragment_issue_info}
{fragment_issue_items}
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
        oid=commit_data['oid']
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

    # Parse the common fields
    id = event_data['id']
    created_at = event_data['createdAt']
    actor = parse_actor(event_data['actor'])

    # Handle each event type
    if event_type == "AddedToProjectEvent":
        return AddedToProjectEvent(id=id, created_at=created_at, actor=actor)

    elif event_type == "AssignedEvent":
        user = parse_user(event_data['user'])
        return AssignedEvent(id=id, created_at=created_at, actor=actor, user=user)

    elif event_type == "ClosedEvent":
        state_reason = event_data.get('stateReason')
        return ClosedEvent(id=id, created_at=created_at, state_reason=state_reason, actor=actor)

    elif event_type == "CommentDeletedEvent":
        deleted_comment_author = parse_actor(event_data['deletedCommentAuthor'])
        return CommentDeletedEvent(id=id, created_at=created_at, actor=actor, deleted_comment_author=deleted_comment_author)

    elif event_type == "ConnectedEvent":
        source = parse_uniform_resource_locatable(event_data['source'])
        subject = parse_uniform_resource_locatable(event_data['subject'])
        return ConnectedEvent(id=id, created_at=created_at, actor=actor, source=source, subject=subject)

    elif event_type == "ConvertedNoteToIssueEvent":
        return ConvertedNoteToIssueEvent(id=id, created_at=created_at, actor=actor)

    elif event_type == "ConvertedToDiscussionEvent":
        return ConvertedToDiscussionEvent(id=id, created_at=created_at, actor=actor)

    elif event_type == "CrossReferencedEvent":
        source = parse_uniform_resource_locatable(event_data['source'])
        target = parse_uniform_resource_locatable(event_data['target'])
        return CrossReferencedEvent(id=id, created_at=created_at, actor=actor, source=source, target=target)

    elif event_type == "DemilestonedEvent":
        return DemilestonedEvent(id=id, created_at=created_at, actor=actor)

    elif event_type == "DisconnectedEvent":
        source = parse_uniform_resource_locatable(event_data['source'])
        subject = parse_uniform_resource_locatable(event_data['subject'])
        return DisconnectedEvent(id=id, created_at=created_at, actor=actor, source=source, subject=subject)

    elif event_type == "IssueComment":
        author = parse_actor(event_data['author'])
        body = event_data['body']
        includes_created_edit = event_data['includesCreatedEdit']
        is_minimized = event_data['isMinimized']
        last_edited_at = event_data['lastEditedAt']
        minimized_reason = event_data['minimizedReason']
        published_at = event_data['publishedAt']
        pull_request = parse_uniform_resource_locatable(event_data['pullRequest']) if 'pullRequest' in event_data else None
        return IssueComment(
            id=id, created_at=created_at, author=author, body=body,
            includes_created_edit=includes_created_edit, is_minimized=is_minimized,
            last_edited_at=last_edited_at, minimized_reason=minimized_reason, 
            published_at=published_at, pull_request=pull_request
        )

    elif event_type == "LabeledEvent":
        label = event_data['label']['name']
        return LabeledEvent(id=id, created_at=created_at, actor=actor, label=label)

    elif event_type == "LockedEvent":
        lock_reason = event_data.get('lockReason')
        return LockedEvent(id=id, created_at=created_at, actor=actor, lock_reason=lock_reason)

    elif event_type == "MarkedAsDuplicateEvent":
        canonical = event_data['canonical']
        duplicate = event_data['duplicate']
        is_cross_repository = event_data['isCrossRepository']
        return MarkedAsDuplicateEvent(id=id, created_at=created_at, actor=actor,
                                      canonical=canonical, duplicate=duplicate, is_cross_repository=is_cross_repository)

    elif event_type == "MentionedEvent":
        return MentionedEvent(id=id, created_at=created_at, actor=actor)

    elif event_type == "MilestonedEvent":
        milestone_title = event_data['milestoneTitle']
        return MilestonedEvent(id=id, created_at=created_at, actor=actor, milestone_title=milestone_title)

    elif event_type == "MovedColumnsInProjectEvent":
        return MovedColumnsInProjectEvent(id=id, created_at=created_at, actor=actor)

    elif event_type == "PinnedEvent":
        return PinnedEvent(id=id, created_at=created_at, actor=actor)

    elif event_type == "ReferencedEvent":
        commit = parse_commit(event_data['commit'])
        commit_repository = parse_repository(event_data['commitRepository'])
        is_cross_repository = event_data.get('isCrossRepository', False)
        is_direct_reference = event_data.get('isDirectReference', False)
        return ReferencedEvent(
            id=id, created_at=created_at, actor=actor,
            commit=commit, commit_repository=commit_repository,
            is_cross_repository=is_cross_repository,
            is_direct_reference=is_direct_reference
        )

    elif event_type == "RemovedFromProjectEvent":
        return RemovedFromProjectEvent(id=id, created_at=created_at, actor=actor)

    elif event_type == "RenamedTitleEvent":
        current_title = event_data['currentTitle']
        previous_title = event_data['previousTitle']
        return RenamedTitleEvent(id=id, created_at=created_at, actor=actor, current_title=current_title, previous_title=previous_title)

    elif event_type == "ReopenedEvent":
        state_reason = event_data.get('stateReason')
        return ReopenedEvent(id=id, created_at=created_at, state_reason=state_reason, actor=actor)

    elif event_type == "SubscribedEvent":
        return SubscribedEvent(id=id, created_at=created_at, actor=actor)

    elif event_type == "TransferredEvent":
        issue = parse_uniform_resource_locatable(event_data['issue'])
        from_repository = parse_repository(event_data['fromRepository'])
        return TransferredEvent(id=id, created_at=created_at, actor=actor, issue=issue, from_repository=from_repository)

    elif event_type == "UnassignedEvent":
        assignee = parse_user(event_data['assignee'])
        return UnassignedEvent(id=id, created_at=created_at, actor=actor, assignee=assignee)

    elif event_type == "UnlabeledEvent":
        label = event_data['label']['name']
        return UnlabeledEvent(id=id, created_at=created_at, actor=actor, label=label)

    elif event_type == "UnlockedEvent":
        return UnlockedEvent(id=id, created_at=created_at, actor=actor)

    elif event_type == "UnmarkedAsDuplicateEvent":
        canonical = event_data['canonical']
        duplicate = event_data['duplicate']
        is_cross_repository = event_data['isCrossRepository']
        return UnmarkedAsDuplicateEvent(id=id, created_at=created_at, actor=actor,
                                        canonical=canonical, duplicate=duplicate, is_cross_repository=is_cross_repository)

    elif event_type == "UnpinnedEvent":
        return UnpinnedEvent(id=id, created_at=created_at, actor=actor)

    elif event_type == "UnsubscribedEvent":
        return UnsubscribedEvent(id=id, created_at=created_at, actor=actor)

    elif event_type == "UserBlockedEvent":
        subject = parse_actor(event_data['subject'])
        return UserBlockedEvent(id=id, created_at=created_at, actor=actor, subject=subject)

    return None  # Return None for unhandled event types
