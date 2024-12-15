fragment_common_items = '''
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

def issues_initial_query():
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

def pull_requests_initial_query():
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

def pull_requests_ongoing_query(cursor):
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


def issues_ongoing_query(cursor):
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

def issues_follow_on(issue):
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

def pull_requests_follow_on(pr):
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

def issues_fill_query(issues):
    issues_query = "\n".join([issues_follow_on(i) for i in issues])
    return (fragment_issue_items + '''\
            query fill($owner: String!, $name: String!, $num_events: Int!) {
  repository(owner: $owner, name: $name) {
     ''' + issues_query + '''\
  }
}
''')

def pull_request_fill_query(prs):
    prs_query = "\n".join([pull_requests_follow_on(i) for i in prs])
    return (fragment_pull_request_items + '''\
            query fill($owner: String!, $name: String!, $num_events: Int!) {
  repository(owner: $owner, name: $name) {
     ''' + prs_query + '''\
  }
}
''')

