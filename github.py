
class Issue:
    def __init__(self, url, user, created_at):
        self.url = url
        self.user = user
        self.created_at = created_at

    def __str__(self):
        return "GithubIssue(url=%s, user=%s, created_at=%s)"%(self.url, self.user, self.created_at)

    def prov(self, repo, doc, mapper):
        issue_url = mapper.qname(self.url)
        user_url = mapper.qname(self.user)
        create_event_url = mapper.qname(self.url + '#create')

        doc.agent(user_url)
        doc.entity(issue_url, {'prov:type': mapper.qname('http://purl.org/github2prov/issue')})
        if self.pull_request:
            doc.entity(issue_url, {'prov:type': mapper.qname('http://purl.org/github2prov/pull')})

        doc.wasAttributedTo(issue_url, user_url)
        doc.activity(create_event_url, self.created_at, self.created_at, {'prov:type': mapper.qname('http://purl.org/github2prov/created')})
        doc.wasAssociatedWith(create_event_url, user_url)
        doc.wasGeneratedBy(issue_url, create_event_url)

class PullRequest(GithubIssue):
    def __init__(self, url, user, created_at):
        self.url = url
        self.user = user
        self.created_at = created_at
    def __str__(self):
        return "GithubPullRequest(url=%s, user=%s, created_at=%s)"%(self.url, self.user, self.created_at)

class IssueEvent:
    def __init__(self, url, issue, user, created_at, number, typ, commit=None):
        self.url = url
        self.issue = issue
        self.user = user
        self.created_at = created_at
        self.number = number
        self.typ = typ
        self.commit = commit

def rn(o):
    return o.__class__.__name__


class Repository:
    def __init__(self, name_with_owner: str):
        self.name_with_owner = name_with_owner


class User:
    def __init__(self, url: str, login: str, typename: str):
        self.url = url
        self.login = login
        self.__typename = typename

    def __repr__(self):
        return f"{rn(self)}(url={self.url}, login={self.login}, typename={self.__typename})"


class Commit:
    def __init__(self, commit_url: str, oid: str):
        self.commit_url = commit_url
        self.oid = oid

    def __repr__(self):
        return f"{rn(self)}(commit_url={self.commit_url}, oid={self.oid})"


# Define the event classes with common properties and nested objects.
class Event:
    def __init__(self, id: str, created_at: str, actor: User):
        self.id = id
        self.created_at = created_at
        self.actor = actor
    def __repr__(self):
        return f"{rn(self)}(id={self.id}, created_at={self.created_at}, actor={self.actor})"

class AddedToProjectEvent(Event):
    def __repr__(self):
        return f"{rn(self)}(id={self.id}, created_at={self.created_at}, actor={self.actor}, user={self.user})"

class AssignedEvent(Event):
    def __init__(self, id: str, created_at: str, actor: User, user: User):
        super().__init__(id, created_at, actor)
        self.user = user

    def __repr__(self):
        return f"{rn(self)}(id={self.id}, created_at={self.created_at}, actor={self.actor}, user={self.user})"

class ClosedEvent(Event):
    def __init__(self, id: str, created_at: str, actor: User, state_reason: str):
        super().__init__(id, created_at, actor)
        self.state_reason = state_reason

    def __repr__(self):
        return f"{rn(self)}(id={self.id}, created_at={self.created_at}, state_reason={self.state_reason}, actor={self.actor})"

class CommentDeletedEvent(Event):
    def __init__(self, id: str, created_at: str, actor: User, deleted_comment_author: User):
        super().__init__(id, created_at, actor)
        self.deleted_comment_author = deleted_comment_author

    def __repr__(self):
        return f"{rn(self)}(id={self.id}, created_at={self.created_at}, actor={self.actor}, deleted_comment_author={self.deleted_comment_author})"

class ConnectedEvent(Event):
   #TODO
    def __init__(self, id: str, created_at: str, actor: User, source: str, subject: str):
        super().__init__(id, created_at, actor)
        self.source = source
        self.subject = subject

    def __repr__(self):
        return f"{rn(self)}(id={self.id}, created_at={self.created_at}, actor={self.actor}, source={self.source}, subject={self.subject})"

class ConvertedNoteToIssueEvent(Event):
    pass


class ConvertedToDiscussionEvent(Event):
    pass


class CrossReferencedEvent(Event):
    #TODO
    def __init__(self, id: str, created_at: str, actor: User, referenced_at: str, source, target):
        super().__init__(id, created_at, actor)
        self.source = source
        self.target = target
        self.referenced_at = referenced_at
    def __repr__(self):
        return f"{rn(self)}(id={self.id}, created_at={self.created_at}, actor={self.actor}, source={self.source}, target={self.target}, referenced_at={self.referenced_at}"

class DemilestonedEvent(Event):
    pass


class DisconnectedEvent(Event):
    def __init__(self, id: str, created_at: str, actor: User, source: str, subject: str):
        super().__init__(id, created_at, actor)
        self.source = source
        self.subject = subject

    def __repr__(self):
        return f"{rn(self)}(id={self.id}, created_at={self.created_at}, actor={self.actor}, source={self.source}, subject={self.subject})"


class IssueComment(Event):
    #TODO
    def __init__(self, id: str, created_at: str, actor: User, body: str, includes_created_edit: bool, is_minimized: bool, source: str, subject: str):
        super().__init__(id, created_at, actor)
        self.source = source
        self.subject = subject

    def __repr__(self):
        return f"{rn(self)}(id={self.id}, created_at={self.created_at}, actor={self.actor}, source={self.source}, subject={self.subject})"


class LabeledEvent(Event):
    def __init__(self, id: str, created_at: str, actor: User, label: str):
        super().__init__(id, created_at, actor)
        self.label = label

    def __repr__(self):
        return f"{rn(self)}(id={self.id}, created_at={self.created_at}, actor={self.actor}, label={self.label})"

class LockedEvent(Event):
    def __init__(self, id: str, created_at: str, actor: User, lock_reason: str):
        super().__init__(id, created_at, actor)
        self.lock_reason = lock_reason

    def __repr__(self):
        return f"{rn(self)}(id={self.id}, created_at={self.created_at}, lock_reason={self.state_reason}, actor={self.actor})"

class MarkedAsDuplicateEvent(Event):
    pass
    #TODO


class MentionedEvent(Event):
    pass

class MilestonedEvent(Event):
    def __init__(self, id: str, created_at: str, actor: User, milestone_title: str):
        super().__init__(id, created_at, actor)
        self.milestone_title = milestone_title

    def __repr__(self):
        return f"{rn(self)}(id={self.id}, created_at={self.created_at}, milestone_title={self.milestone_title})"


class MovedColumnsInProjectEvent(Event):
    pass


class PinnedEvent(Event):
    pass


class ReferencedEvent(Event):
    def __init__(self, id: str, created_at: str, actor: User, commit: Commit, commit_repository: str, is_cross_repository: bool, is_direct_reference: bool):
        super().__init__(id, created_at, actor)
        self.commit = commit
        self.commit_repository = commit_repository
        self.is_cross_repository = is_cross_repository
        self.is_direct_reference = is_direct_reference

    def __repr__(self):
        return (f"{rn(self)}(id={self.id}, created_at={self.created_at}, actor={self.actor}, "
                f"commit={self.commit}, commit_repository={self.commit_repository}, "
                f"is_cross_repository={self.is_cross_repository}, is_direct_reference={self.is_direct_reference})")


class RemovedFromProjectEvent:
    pass


class RenamedTitleEvent:
    def __init__(self, id: str, created_at: str, actor: User, current_title: str, previous_title: str):
        super().__init__(id, created_at, actor)
        self.current_title = current_title
        self.previous_title = previous_title

    def __repr__(self):
        return f"{rn(self)}(id={self.id}, created_at={self.created_at}, state_reason={self.state_reason}, actor={self.actor})"


class ReopenedEvent:
    def __init__(self, id: str, created_at: str, actor: User, state_reason: str):
        super().__init__(id, created_at, actor)
        self.state_reason = state_reason

    def __repr__(self):
        return f"{rn(self)}(id={self.id}, created_at={self.created_at}, state_reason={self.state_reason}, actor={self.actor})"


class SubscribedEvent:
    pass


class TransferredEvent:
    #TODO
    pass


class UnassignedEvent:
    def __init__(self, id: str, created_at: str, actor: User, user: User):
        super().__init__(id, created_at, actor)
        self.user = user

    def __repr__(self):
        return f"{rn(self)}(id={self.id}, created_at={self.created_at}, actor={self.actor}, user={self.user})"


class UnlabeledEvent:
    def __init__(self, id: str, created_at: str, actor: User, label: str):
        super().__init__(id, created_at, actor)
        self.label = label

    def __repr__(self):
        return f"{rn(self)}(id={self.id}, created_at={self.created_at}, actor={self.actor}, label={self.label})"


class UnlockedEvent:
    pass


class UnmarkedAsDuplicateEvent:
    #TODO
    pass


class UnpinnedEvent:
    pass


class UnsubscribedEvent:
    pass


class UserBlockedEvent:
    def __init__(self, id: str, created_at: str, actor: User, subject: User):
        super().__init__(id, created_at, actor)
        self.subject = subject

    def __repr__(self):
        return (f"{rn(self)}(id={self.id}, created_at={self.created_at}, actor={self.actor}, "
                f"subject={self.subject})")
    pass


class PullRequest:
    def __init__(self, url):
        self.url = url

    def __repr__(self):
        return f"{rn(self)}(url={self.url})"


class ReviewEvent(Event):
    #TODO is this needed?
    def __init__(self, id: str, created_at: str, actor: User, author: User, body: str, commit: Commit):
        super().__init__(id, created_at, actor)
        self.author = author
        self.body = body
        self.commit = commit

    def __repr__(self):
        return (f"{rn(self)}(id={self.id}, created_at={self.created_at}, actor={self.actor}, "
                f"author={self.author}, body={self.body}, commit={self.commit})")


class AddedToMergeQueueEvent(Event):
    def __init__(self, id: str, created_at: str, actor: User, enqueuer: User):
        super().__init__(id, created_at, actor)
        self.enqueuer = enqueuer

    def __repr__(self):
        return f"{rn(self)}(id={self.id}, created_at={self.created_at}, actor={self.actor}, enqueuer={self.enqueuer})"


class AutoMergeDisabledEvent(Event):
    def __init__(self, id: str, created_at: str, actor: User, reason: str, reason_code: int):
        super().__init__(id, created_at, actor)
        self.reason = reason
        self.reason_code = reason_code

    def __repr__(self):
        return f"{rn(self)}(id={self.id}, created_at={self.created_at}, actor={self.actor}, reason={self.reason}, reason_code={self.reason_code})"


class AutoMergeEnabledEvent(Event):
    def __init__(self, id: str, created_at: str, actor: User, enabler: User):
        super().__init__(id, created_at, actor)
        self.enabler = enabler

    def __repr__(self):
        return f"{rn(self)}(id={self.id}, created_at={self.created_at}, actor={self.actor}, enabler={self.enabler})"


class AutoRebaseEnabledEvent(Event):
    def __init__(self, id: str, created_at: str, actor: User, enabler: User):
        super().__init__(id, created_at, actor)
        self.enabler = enabler

    def __repr__(self):
        return f"{rn(self)}(id={self.id}, created_at={self.created_at}, actor={self.actor}, enabler={self.enabler})"


class AutoSquashEnabledEvent(Event):
    def __init__(self, id: str, created_at: str, actor: User, enabler: User):
        super().__init__(id, created_at, actor)
        self.enabler = enabler

    def __repr__(self):
        return f"{rn(self)}(id={self.id}, created_at={self.created_at}, actor={self.actor}, enabler={self.enabler})"


class AutomaticBaseChangeFailedEvent(Event):
    def __init__(self, id: str, created_at: str, actor: User, new_base, old_base):
        super().__init__(id, created_at, actor)
        self.new_base = new_base
        self.old_base = old_base

    def __repr__(self):
        return f"{rn(self)}(id={self.id}, created_at={self.created_at}, actor={self.actor}, new_base={self.new_base}, old_base={self.old_base})"


class AutomaticBaseChangeSucceededEvent(Event):
    def __init__(self, id: str, created_at: str, actor: User, new_base, old_base):
        super().__init__(id, created_at, actor)
        self.new_base = new_base
        self.old_base = old_base

    def __repr__(self):
        return f"{rn(self)}(id={self.id}, created_at={self.created_at}, actor={self.actor}, new_base={self.new_base}, old_base={self.old_base})"


class BaseRefChangedEvent(Event):
    def __init__(self, id: str, created_at: str, actor: User, current_ref_name: str, previous_ref_name: str):
        super().__init__(id, created_at, actor)
        self.current_ref_name = current_ref_name
        self.previous_ref_name = previous_ref_name

    def __repr__(self):
        return f"{rn(self)}(id={self.id}, created_at={self.created_at}, actor={self.actor}, current_ref_name={self.current_ref_name}, previous_ref_name={self.previous_ref_name})"


class BaseRefDeletedEvent(Event):
    def __init__(self, id: str, created_at: str, actor: User, base_ref_name: str):
        super().__init__(id, created_at, actor)
        self.base_ref_name = base_ref_name

    def __repr__(self):
        return f"{rn(self)}(id={self.id}, created_at={self.created_at}, actor={self.actor}, base_ref_name={self.base_ref_name})"


class BaseRefForcePushedEvent(Event):
    def __init__(self, id: str, created_at: str, actor:User, after_commit: Commit, before_commit: Commit):
        super().__init__(id, created_at, actor)
        self.after_commit = after_commit
        self.before_commit = before_commit

    def __repr__(self):
        return f"{rn(self)}(id={self.id}, created_at={self.created_at}, actor={self.actor}, after_commit={self.after_commit}, before_commit={self.before_commit})"


class ConvertToDraftEvent(Event):
    pass


class DeployedEvent(Event):
    pass


class DeploymentEnvironmentChangedEvent(Event):
    pass


class HeadRefDeletedEvent(Event):
    pass


class HeadRefForcePushedEvent(Event):
    pass


class HeadRefRestoredEvent(Event):
    pass


class MergedEvent(Event):
    def __init__(self, id: str, created_at: str, actor: User, commit: Commit):
        super().__init__(id, created_at, actor)
        self.commit = commit

    def __repr__(self):
        return f"{rn(self)}(id={self.id}, created_at={self.created_at}, actor={self.actor}, commit={self.commit})"


class PullRequestCommit:
    def __init__(self, id: str, commit: Commit):
        self.id = id
        self.commit = commit

    def __repr__(self):
        return f"{rn(self)}(id={self.id}, commit={self.commit})"


class PullRequestReview(Event):
    def __init__(self, id: str, created_at: str, author: User, body: str, commit: Commit):
        super().__init__(id, created_at, actor)
        self.body = body
        self.commit = commit

    def __repr__(self):
        return f"{rn(self)}(id={self.id}, created_at={self.created_at}, author={self.author}, body={self.body}, commit={self.commit})"


class PullRequestRevisionMarker:
    def __init__(self, created_at: str):
        self.created_at = created_at

    def __repr__(self):
        return f"{rn(self)}(created_at={self.created_at})"


class ReadyForReviewEvent(Event):
    #TODO
    def __init__(self, id: str, created_at: str, actor: User, resource_path):
        super().__init__(id, created_at, actor)
        self.resource_path = resource_path

    def __repr__(self):
        return f"{rn(self)}(id={self.id}, created_at={self.created_at}, actor={self.actor}, resource_path={self.resource_path})"


class RemovedFromMergeQueueEvent(Event):
    def __init__(self, id: str, created_at: str, actor: User, reason: str, before_commit: Commit):
        super().__init__(id, created_at, actor)
        self.reason = reason
        self.before_commit = before_commit

    def __repr__(self):
        return f"{rn(self)}(id={self.id}, created_at={self.created_at}, actor={self.actor}, reason={self.reason}, before_commit={self.before_commit})"


class RemovedFromProjectEvent(Event):
    pass


class ReviewDismissedEvent(Event):
    pass


class ReviewRequestRemovedEvent(Event):
    pass


class ReviewRequestedEvent(Event):
    pass
