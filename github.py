import re

class GithubCommit:
    def __init__(self, url: str, sha: str, author: str, author_name: str, committer: str, committer_name: str, created_at: str, parents: str, message: str):
        self.url = url
        self.sha = sha
        self.author = author
        self.author_name = author_name
        self.committer = committer
        self.committer_name = committer_name
        self.created_at = created_at
        self.parents = parents if parents else []
        self.message = message

    def prov(self, doc, mapper):
        # TODO: shouldn't commit.url, commit.author and commit.committer be q-minted also?
        doc.activity(self.url, self.created_at, self.created_at, {
            'prov:type': mapper.qname('http://purl.org/github2prov/commit') 
        })

        # TODO: what do we do if commit.author or commit.committer is None?
        # In some cases commit.author_name appears valid, but commit.author is None
        if self.author and self.author != "https://api.github.com/users/web-flow":
            doc.agent(self.author, {'rdfs:label': self.author_name})
            doc.wasAssociatedWith(self.url, self.author, None, None, {'prov:role':'author'})
            doc.wasAssociatedWith(self.url, self.author)

        if self.committer and self.committer != "https://api.github.com/users/web-flow":
            doc.agent(self.committer, {'rdfs:label': self.committer_name})
            doc.wasAssociatedWith(self.url, self.committer, None, None, {'prov:role':'committer'})
            doc.wasAssociatedWith(self.url, self.committer)

        for parent in self.parents:
            doc.wasInformedBy(self.url, parent)

    @classmethod
    def parse(cls, data):
        url = data['url']
        sha = data['sha']

        # bernard changed this - the method was retireving athorship info from a top level filed that was used in the REST commit format
        # with graphql results there is no top leve filed and the data is nested at cinutt.author.user or commit,comitter.user
        # this means the author comitter info was alsways set to none so no assocation links were ever produced

        # Obtain authorship info if it exists
        author_el = data.get('commit', {}).get('author', {}).get('user') or {}
        # author_el = data.get('author', {})
        author = author_el.get('url', None) if author_el else None
        author_name = data.get('commit', {}).get('author', {}).get('name', None)

        # Obtain committer info it exists
        committer_el = data.get('commit', {}).get('committer', {}).get('user') or {}

        # committer_el = data.get('committer', {})
        committer = committer_el.get('url', None) if committer_el else None
        committer_name = data.get('commit', {}).get('committer', {}).get('name', None)


        # Created time used for both start and end PROV entries
        created_at = data.get('commit', {}).get('committer', {}).get('date', None)

        # Retrieve parent commits if they exist
        parents = [c['url'] for c in data.get('parents', [])]

        # Ensure commit message has newlines removed
        message = data.get('commit', {}).get('message', {})
        message = ' '.join(message.split())

        return GithubCommit(url, sha, author, author_name, committer, committer_name, created_at, parents, message)


class Issue:
    def __init__(self, url, author, created_at):
        self.url = url
        self.user = author
        self.created_at = created_at

    def __str__(self):
        return "GithubIssue(url=%s, author=%s, created_at=%s)"%(self.url, self.user, self.created_at)

    def prov(self, doc, mapper):
        #print(self)
        issue_url = mapper.qname(self.url)
        user_url = mapper.qname(self.user.url)
        create_event_url = mapper.qname(self.url + '#create')

        doc.agent(user_url)
        doc.entity(issue_url, {'prov:type': mapper.qname('http://purl.org/github2prov/issue')})
        #if self.pull_request:
        #    doc.entity(issue_url, {'prov:type': mapper.qname('http://purl.org/github2prov/pull')})

        doc.wasAttributedTo(issue_url, user_url)
        doc.activity(create_event_url, self.created_at, self.created_at, {'prov:type': mapper.qname('http://purl.org/github2prov/created')})
        doc.wasAssociatedWith(create_event_url, user_url)
        doc.wasGeneratedBy(issue_url, create_event_url)

    @classmethod
    def parse(cls, data):
        return Issue(data['url'], User.parse(data['author']), data['createdAt'])


class PullRequest(Issue):
    def __init__(self, url, user, created_at):
        self.url = url
        self.user = user
        self.created_at = created_at
    def __str__(self):
        return "GithubPullRequest(url=%s, user=%s, created_at=%s)"%(self.url, self.user, self.created_at)

    def prov(self, doc, mapper):
        super().prov(doc, mapper)

        #print(self.url)
        issue_url = mapper.qname(self.url)

        doc.entity(issue_url, {'prov:type': mapper.qname('http://purl.org/github2prov/pull')})

    @classmethod
    def parse(cls, data):
        return PullRequest(data['url'], User.parse(data['author']), data['createdAt'])

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

    @classmethod
    def parse(cls, data):
        return cls(name_with_owner=data['nameWithOwner'])

class Stargazer:
    def __init__(self,stargazers):
        self.stargazers = stargazers
    @classmethod
    def parse(cls, data):
        return Stargazer(data)
    def prov(self, repo_slug, doc, mapper):
        if self.stargazers is None:
            return
        repo = "https://github.com/"+repo_slug
        repo_url = mapper.qname(repo)
        starred = mapper.qname('http://purl.org/github2prov/starred')
        for s in self.stargazers:
            when = s['when']
            who = s['who']
            name = who.split("https://github.com/")[1]
            user = mapper.qname(who)
            activity = mapper.qname(repo + "/" + name)
            doc.agent(user)
            doc.activity(activity, when, when, {'prov:type': starred})
            doc.wasAssociatedWith(activity, user)
            doc.used(activity, repo_url)

class Releases:
    def __init__(self,releases):
        self.releases = releases
    @classmethod
    def parse(cls, data):
        return Releases(data)
    def prov(self, repo_slug, doc, mapper):
        print(self.releases)
        repo = "https://github.com/"+repo_slug
        release = mapper.qname('http://purl.org/github2prov/release')
        released = mapper.qname('http://purl.org/github2prov/released')
        dc = mapper.qname('http://purl.org/github2prov/downloadCount')
        for s in self.releases:
            activity = mapper.qname(repo + '/released/' + s['id'])
            user = mapper.qname(s['author']['url'])
            when = s['createdAt']
            commit = mapper.qname(s['tagCommit']['commitUrl'])
            r = mapper.qname(s['url'])

            doc.agent(user)
            doc.activity(activity, when, when, {'prov:type': released})
            doc.entity(r, {'prov:type':release, 'prov:label':s['name'], dc:s['downloadCount']})
            doc.wasGeneratedBy(r, activity)
            doc.wasAssociatedWith(activity, user)
            doc.used(activity,commit)
            doc.wasDerivedFrom(r, commit)

class RepoInfo:
    def __init__(self, url, fork_count, stargazer_count, watchers_count):
        self.url = url
        self.fork_count = fork_count
        self.stargazer_count = stargazer_count
        self.watchers_count = watchers_count

    @classmethod
    def parse(cls, data):
        return RepoInfo(data['url'], data['fork_count'], data['stargazer_count'], data['watchers_count'])

    def prov(self, doc, mapper):
        repo_url = mapper.qname(self.url)

        doc.entity(repo_url, {'prov:type': mapper.qname('http://purl.org/github2prov/repository'),
                              'github2prov:forkCount': self.fork_count,
                              'github2prov:stargazerCount': self.stargazer_count,
                              'github2prov:watchersCount': self.watchers_count,
                              })
class User:
    def __init__(self, url: str, login: str, typename: str):
        self.url = url
        self.login = login
        self.__typename = typename

    def __repr__(self):
        return f"{rn(self)}(url={self.url}, login={self.login}, typename={self.__typename})"

    @classmethod
    def parse(cls, data):
        # in github, if a user has been deleted the api will return none. The frontend uses a dummy user
        if not data or 'url' not in data:
            return cls(url='https://github.com/ghost', login='ghost', typename='User')
        return cls(url=data['url'], login=data['login'], typename=data['__typename'])


class Commit:
    def __init__(self, commit_url: str, oid: str):
        self.commit_url = commit_url
        self.oid = oid

    def __repr__(self):
        return f"{rn(self)}(commit_url={self.commit_url}, oid={self.oid})"

    @classmethod
    def parse(cls, data):
        return cls(commit_url=data['commitUrl'], oid=data['oid'])


# Define the event classes with common properties and nested objects.
class Event:
    def __init__(self, id: str, created_at: str, actor: User):
        self.id = id
        self.created_at = created_at
        self.actor = actor
        self.number = -1
    def __repr__(self):
        return f"{rn(self)}(id={self.id}, created_at={self.created_at}, actor={self.actor})"

    @classmethod
    def fragment(cls):
        return f"... on {cls.__name__} {{ id createdAt actor {{ url login __typename }} }}"

    @classmethod
    def parse(cls, data):
        return cls(id=data['id'], created_at=data['createdAt'], actor=User.parse(data['actor']))

    def prov_sub_type(self):
        r'''
        grep -B 2 'type.*Event' schema.docs.graphql | awk '(/--/){print t, line}(/^type/){t=$2;next}(/"""/){next}(/.*/){line=$0}' | sed 's/Represents a\(n\)\? //;s/ event on .*//' | gawk '{t=$1;t=gensub(/Event/,"",1,t);t=gensub(/([A-Z])/, "_\\1", "g",t); sub(/^_/, "", t);t=tolower(t); w=gensub(/'"'"'/,"","g",$2) ; if (t!=w){print t,w}}'
cross_referenced mention
renamed_title renamed
        '''
        name = self.__class__.__name__
        if name.endswith("Event"):
            name = name[:-5]
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
        r = re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()
        if r == "renamed_title":
            return "renamed"
        if r == "cross_referenced":
            return "mention"
        if r == "issue_comment":
            return "comment"
        return r

    def prov(self, doc, mapper, issue_url):
        issue_version = mapper.qname(issue_url + '#' + str(self.number))
        # u = issue_url + "/events/" + self.id
        # event_url = mapper.qname(u)

        # bernard stwithch this to use self.url, like all the base classes. In some situations this was used to mint
        # subjects and or objects for triples which generated new nodes which the triples pointed at, thus spitting some
        # nodes and orphaning the originals
        event_url = mapper.qname(self.url)

        doc.activity(event_url, self.created_at, self.created_at, other_attributes={'prov:type': mapper.qname('http://purl.org/github2prov/' + self.prov_sub_type())})

        actor_url = mapper.qname(self.actor.url)
        doc.agent(actor_url)
        doc.wasAssociatedWith(event_url, actor_url, other_attributes={'prov:role': 'github2prov:actor'})
        doc.wasAssociatedWith(event_url, actor_url)

        doc.entity(issue_version, {'prov:type': mapper.qname('http://purl.org/github2prov/issue_version')})
        doc.specialization(issue_version, issue_url)

        postfix = "" if self.number < 2 else "#"+str(self.number-1)
        ip = mapper.qname(issue_url + postfix)

        doc.used(event_url, ip)
        doc.wasGeneratedBy(issue_version, event_url)


class EventWithUser:
    def __init__(self, id: str, created_at: str, actor: User, user: User):
        super().__init__(id, created_at, actor)
        self.user = user

    def __repr__(self):
        return f"{rn(self)}(id={self.id}, created_at={self.created_at}, actor={self.actor}, user={self.user})"

    @classmethod
    def fragment(cls):
        return f"... on {cls.__name__} {{ id createdAt actor {{ url login __typename }} user {{ url login __typename }} }}"

    @classmethod
    def parse(cls, data):
        return cls(id=data['id'], created_at=data['createdAt'],
                   actor=User.parse(data['actor']),
                   user=User.parse(data['user']))

    def prov(self, doc, mapper, issue_url):
        super().prov(doc, mapper, issue_url)

        user_url = mapper.qname(self.user.url)
        event_url = mapper.qname(self.url)

        doc.agent(user_url)
        doc.wasAssociatedWith(event_url, user_url, other_attributes={'prov:role': 'github2prov:user'})

class EventWithReason(Event):
    def __init__(self, id: str, created_at: str, actor: User, state_reason: str):
        super().__init__(id, created_at, actor)
        self.state_reason = state_reason

    def __repr__(self):
        return f"{rn(self)}(id={self.id}, created_at={self.created_at}, state_reason={self.state_reason}, actor={self.actor})"

    @classmethod
    def fragment(cls):
        return f"... on {cls.__name__} {{ id createdAt actor {{ url login __typename }} stateReason }}"

    @classmethod
    def parse(cls, data):
        return cls(id=data['id'], created_at=data['createdAt'],
                   actor=User.parse(data['actor']),
                   state_reason=data['stateReason'])

    def prov(self, doc, mapper, issue_url):
        super().prov(doc, mapper, issue_url)

        event_url = mapper.qname(self.url)

        doc.activity(event_url, other_attributes={'github2prov:reason': self.state_reason})

class EventWithEnabler(Event):
    def __init__(self, id: str, created_at: str, actor: User, enabler: User):
        super().__init__(id, created_at, actor)
        self.enabler = enabler

    def __repr__(self):
        return f"{rn(self)}(id={self.id}, created_at={self.created_at}, actor={self.actor}, enabler={self.enabler})"

    @classmethod
    def fragment(cls):
        return f"... on {cls.__name__} {{ id createdAt actor {{ url login __typename }} enabler {{ url login __typename }} }}"

    @classmethod
    def parse(cls, data):
        return cls(id=data['id'], created_at=data['createdAt'],
                   actor=User.parse(data['actor']),
                   enabler=User.parse(data['enabler']))

    def prov(self, doc, mapper, issue_url):
        super().prov(doc, mapper, issue_url)

        enabler_url = mapper.qname(self.enabler.url)
        event_url = mapper.qname(self.url)

        doc.agent(enabler_url)
        doc.wasAssociatedWith(event_url, agent=enabler_url, other_attributes={'prov:role': 'github2prov:enabler'})


class AddedToProjectEvent(Event):
    # databaseId
    pass


class AssignedEvent(Event):
    def __init__(self, id: str, created_at: str, actor: User, assignee: User):
        super().__init__(id, created_at, actor)
        self.assignee = assignee

    def __repr__(self):
        return f"{rn(self)}(id={self.id}, created_at={self.created_at}, actor={self.actor}, assignee={self.assignee})"

    @classmethod
    def fragment(cls):
        return f"... on {cls.__name__} {{ id createdAt actor {{ url login __typename }} assignee {{ __typename ... on User {{ url login __typename }} }} }}"
    pass

    @classmethod
    def parse(cls, data):
        actor = User.parse(data['actor'])
        assignee = actor
        #TODO it might be a null assignee is because its not a user 
        if 'assignee' in data:
            assignee = User.parse(data['assignee'])
        return cls(id=data['id'], created_at=data['createdAt'], actor=actor, assignee=assignee)

    def prov(self, doc, mapper, issue_url):
        super().prov(doc, mapper, issue_url)

        assignee_url = mapper.qname(self.assignee.url)
        event_url = mapper.qname(self.url)

        doc.agent(assignee_url)
        doc.wasAssociatedWith(event_url, agent=assignee_url, other_attributes={'prov:role': 'github2prov:assignee'})


class ClosedEvent(EventWithReason):
    #url
    pass


class CommentDeletedEvent(Event):
    def __init__(self, id: str, created_at: str, actor: User, deleted_comment_author: User):
        super().__init__(id, created_at, actor)
        self.deleted_comment_author = deleted_comment_author

    def __repr__(self):
        return f"{rn(self)}(id={self.id}, created_at={self.created_at}, actor={self.actor}, deleted_comment_author={self.deleted_comment_author})"

    @classmethod
    def fragment(cls):
        return f"... on {cls.__name__} {{ id createdAt actor {{ url login __typename }} deletedCommentAuthor {{ url login __typename }} }}"

    @classmethod
    def parse(cls, data):
        return cls(id=data['id'], created_at=data['createdAt'],
                   actor=User.parse(data['actor']),
                   deleted_comment_author=User.parse(data['deletedCommentAuthor']))

    def prov(self, doc, mapper, issue_url):
        super().prov(doc, mapper, issue_url)

        dca_url = mapper.qname(self.deleted_comment_author.url)
        event_url = mapper.qname(self.url)

        doc.agent(dca_url)
        doc.wasAssociatedWith(event_url, agent=dca_url, other_attributes={'prov:role': 'github2prov:deletedCommentAuthor'})


class ConnectedEvent(Event):
    def __init__(self, id: str, created_at: str, actor: User, source: str, subject: str):
        super().__init__(id, created_at, actor)
        self.source = source
        self.subject = subject

    def __repr__(self):
        return f"{rn(self)}(id={self.id}, created_at={self.created_at}, actor={self.actor}, source={self.source}, subject={self.subject})"

    @classmethod
    def fragment(cls):
        return f"... on {cls.__name__} {{ id createdAt actor {{ url login __typename }} source {{ ... on UniformResourceLocatable {{ url }} }} subject {{ ... on UniformResourceLocatable {{ url }} }} }}"

    #TODO check on UniformResourceLocatable
    @classmethod
    def parse(cls, data):
        return cls(id=data['id'], created_at=data['createdAt'],
                   actor=User.parse(data['actor']),
                   source=data['source'], subject=data['subject'])

    def prov(self, doc, mapper, issue_url):
        super().prov(doc, mapper, issue_url)
        #TODO source, subject


class ConvertedNoteToIssueEvent(Event):
    # databaseId
    pass


class ConvertedToDiscussionEvent(Event):
    pass


class CrossReferencedEvent(Event):
    # url
    def __init__(self, id: str, created_at: str, actor: User, referenced_at: str, source: str, target: str):
        super().__init__(id, created_at, actor)
        self.source = source
        self.target = target
        self.referenced_at = referenced_at
    def __repr__(self):
        return f"{rn(self)}(id={self.id}, created_at={self.created_at}, actor={self.actor}, source={self.source}, target={self.target}, referenced_at={self.referenced_at}"

    @classmethod
    def fragment(cls):
        return f"... on {cls.__name__} {{ id createdAt actor {{ url login __typename }} referencedAt source {{ ... on UniformResourceLocatable {{ url }} }} target {{ ... on UniformResourceLocatable {{ url }} }} }}"

    @classmethod
    def parse(cls, data):
        return cls(id=data['id'], created_at=data['createdAt'],
                   actor=User.parse(data['actor']),
                   referenced_at=data['referencedAt'],
                   source=data['source'], target=data['target'])

    def prov(self, doc, mapper, issue_url):
        super().prov(doc, mapper, issue_url)
        #TODO referenced_at, source, target


class DemilestonedEvent(Event):
    pass


class DisconnectedEvent(ConnectedEvent):
    pass


class IssueComment(Event):
    # databaseId
    # url
    def __init__(self, id: str, created_at: str, actor: User, body: str,
            includes_created_edit: bool, is_minimized: bool, last_edited_at: str,
            minimized_reason: str, published_at: str, pull_request: str):
        super().__init__(id, created_at, actor)
        self.body = body
        self.includes_created_edit = includes_created_edit
        self.is_minimized = is_minimized
        self.last_edited_at = last_edited_at
        self.minimized_reason = minimized_reason
        self.published_at = published_at
        self.pull_request = pull_request

    def __repr__(self):
        return f"{rn(self)}(id={self.id}, created_at={self.created_at}, actor={self.actor}, body={self.body}, includes_created_edit={self.includes_created_edit} is_minimized={self.is_minimized}, last_edited_at={self.last_edited_at}, minimized_reason={self.minimized_reason}, published_at={self.published_at}, pull_request={self.pull_request})"

    @classmethod
    def fragment(cls):
        return f"... on {cls.__name__} {{ id createdAt author {{ url login __typename }} body includesCreatedEdit isMinimized lastEditedAt minimizedReason publishedAt pullRequest {{ url }} }}"

    @classmethod
    def parse(cls, data):
        pr_url = ""
        if data['pullRequest']:
            pr_url = data['pullRequest']['url']

        return cls(id=data['id'], created_at=data['createdAt'],
                   actor=User.parse(data['author']),
                   body=data['body'],
                   includes_created_edit=data['includesCreatedEdit'],
                   is_minimized=data['isMinimized'],
                   last_edited_at=data['lastEditedAt'],
                   minimized_reason=data['minimizedReason'],
                   published_at=data['publishedAt'],
                   pull_request=pr_url)

    def prov(self, doc, mapper, issue_url):
        super().prov(doc, mapper, issue_url)
        #TODO


class LabeledEvent(Event):
    def __init__(self, id: str, created_at: str, actor: User, label: str):
        super().__init__(id, created_at, actor)
        self.label = label

    def __repr__(self):
        return f"{rn(self)}(id={self.id}, created_at={self.created_at}, actor={self.actor}, label={self.label})"

    @classmethod
    def fragment(cls):
        return f"... on {cls.__name__} {{ id createdAt actor {{ url login __typename }} label {{ name }} }}"

    @classmethod
    def parse(cls, data):
        return cls(id=data['id'], created_at=data['createdAt'],
                   actor=User.parse(data['actor']),
                   label=data['label']['name'])

    def prov(self, doc, mapper, issue_url):
        super().prov(doc, mapper, issue_url)

        event_url = mapper.qname(self.url)
        doc.activity(event_url, other_attributes={'github2prov:label': self.label})


class LockedEvent(Event):
    def __init__(self, id: str, created_at: str, actor: User, lock_reason: str):
        super().__init__(id, created_at, actor)
        self.lock_reason = lock_reason

    def __repr__(self):
        return f"{rn(self)}(id={self.id}, created_at={self.created_at}, actor={self.actor}, lock_reason={self.state_reason})"

    @classmethod
    def fragment(cls):
        return f"... on {cls.__name__} {{ id createdAt actor {{ url login __typename }} lockReason }}"

    @classmethod
    def parse(cls, data):
        return cls(id=data['id'], created_at=data['createdAt'],
                   actor=User.parse(data['actor']),
                   lock_reason=data['lockReason'])

    def prov(self, doc, mapper, issue_url):
        super().prov(doc, mapper, issue_url)

        event_url = mapper.qname(self.url)
        doc.activity(event_url, other_attributes={'github2prov:reason': self.lock_reason})


class MarkedAsDuplicateEvent(Event):
    def __init__(self, id: str, created_at: str, actor: User, canonical: str, duplicate: str, is_cross_repository: bool):
        super().__init__(id, created_at, actor)
        self.canonical = canonical
        self.duplicate = duplicate
        self.is_cross_repository = is_cross_repository

    def __repr__(self):
        return f"{rn(self)}(id={self.id}, created_at={self.created_at}, actor={self.actor}, canonical={self.canonical}, duplicate={self.duplicate}, is_cross_respository={self.is_cross_repository})"

    @classmethod
    def fragment(cls):
        return f"... on {cls.__name__} {{ id createdAt actor {{ url login __typename }} canonical {{ __typename ... on Issue {{ url }} ... on PullRequest {{ url }} }} duplicate {{ __typename ... on Issue {{ url }} ... on PullRequest {{ url }} }} isCrossRepository }}"

    #TODO check canonical/duplicate
    @classmethod
    def parse(cls, data):
        return cls(id=data['id'], created_at=data['createdAt'],
                   actor=User.parse(data['actor']),
                   canonical=data['canonical']['url'],
                   duplicate=data['duplicate']['url'],
                   is_cross_repository=data['isCrossRepository'])

    def prov(self, doc, mapper, issue_url):
        super().prov(doc, mapper, issue_url)
        #TODO

class MentionedEvent(Event):
    # databaseId
    pass

class MilestonedEvent(Event):
    def __init__(self, id: str, created_at: str, actor: User, milestone_title: str):
        super().__init__(id, created_at, actor)
        self.milestone_title = milestone_title

    def __repr__(self):
        return f"{rn(self)}(id={self.id}, created_at={self.created_at}, milestone_title={self.milestone_title})"

    @classmethod
    def fragment(cls):
        return f"... on {cls.__name__} {{ id createdAt actor {{ url login __typename }} milestoneTitle }}"

    @classmethod
    def parse(cls, data):
        return cls(id=data['id'], created_at=data['createdAt'],
                   actor=User.parse(data['actor']),
                   milestone_title=data['milestoneTitle'])

    def prov(self, doc, mapper, issue_url):
        super().prov(doc, mapper, issue_url)

        event_url = mapper.qname(self.url)
        doc.activity(event_url, other_attributes={'github2prov:milestoneTitle': self.milestone_title})


class MovedColumnsInProjectEvent(Event):
    # databaseId
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

    @classmethod
    def fragment(cls):
        return f"... on {cls.__name__} {{ id createdAt actor {{ url login __typename }} commit {{ commitUrl committedDate oid }} commitRepository {{ nameWithOwner }} isCrossRepository isDirectReference }}"

    @classmethod
    def parse(cls, data):
        return cls(id=data['id'], created_at=data['createdAt'],
                   actor=User.parse(data['actor']),
                   commit=Commit.parse(data['commit']),
                   commit_repository=Repository.parse(data['commitRepository']),
                   is_cross_repository=data['isCrossRepository'],
                   is_direct_reference=data['isDirectReference'])

    def prov(self, doc, mapper, issue_url):
        super().prov(doc, mapper, issue_url)
        #TODO


class RemovedFromProjectEvent(Event):
    # databaseId
    pass


class RenamedTitleEvent(Event):
    def __init__(self, id: str, created_at: str, actor: User, current_title: str, previous_title: str):
        super().__init__(id, created_at, actor)
        self.current_title = current_title
        self.previous_title = previous_title

    def __repr__(self):
        return f"{rn(self)}(id={self.id}, created_at={self.created_at}, actor={self.actor}, current_title={self.current_title}, previous_title={self.previous_title})"

    @classmethod
    def fragment(cls):
        return f"... on {cls.__name__} {{ id createdAt actor {{ url login __typename }} currentTitle previousTitle }}"

    @classmethod
    def parse(cls, data):
        return cls(id=data['id'], created_at=data['createdAt'],
                   actor=User.parse(data['actor']),
                   current_title=data['currentTitle'],
                   previous_title=data['previousTitle'])

    def prov(self, doc, mapper, issue_url):
        super().prov(doc, mapper, issue_url)

        event_url = mapper.qname(self.url)
        doc.activity(event_url, other_attributes={'github2prov:currentTitle': self.current_title, 'github2prov:previousTitle': self.previous_title})

class ReopenedEvent(EventWithReason):
    pass


class SubscribedEvent(Event):
    pass


class TransferredEvent(Event):
    def __init__(self, id: str, created_at: str, actor: User, issue: str, from_repository: str):
        super().__init__(id, created_at, actor)
        self.issue = issue
        self.from_repository = from_repository

    def __repr__(self):
        return f"{rn(self)}(id={self.id}, created_at={self.created_at}, actor={self.actor}, issue={self.issue}, from_repository={self.from_repository})"

    @classmethod
    def fragment(cls):
        return f"... on {cls.__name__} {{ id createdAt actor {{ url login __typename }} issue {{ url }} fromRepository {{ nameWithOwner }} }}"

    @classmethod
    def parse(cls, data):
        if 'fromRepository' not in data:
            return None
        return cls(id=data['id'], created_at=data['createdAt'],
                   actor=User.parse(data['actor']),
                   issue=data['issue']['url'],
                   from_repository=data['fromRepository']['nameWithOwner'])

    def prov(self, doc, mapper, issue_url):
        super().prov(doc, mapper, issue_url)
        #TODO


class UnassignedEvent(AssignedEvent):
    pass


class UnlabeledEvent(LabeledEvent):
    pass


class UnlockedEvent(Event):
    pass


class UnmarkedAsDuplicateEvent(MarkedAsDuplicateEvent):
    pass


class UnpinnedEvent(PinnedEvent):
    pass


class UnsubscribedEvent(SubscribedEvent):
    pass


class UserBlockedEvent(Event):
    def __init__(self, id: str, created_at: str, actor: User, subject: User):
        super().__init__(id, created_at, actor)
        self.subject = subject

    def __repr__(self):
        return (f"{rn(self)}(id={self.id}, created_at={self.created_at}, actor={self.actor}, "
                f"subject={self.subject})")

    @classmethod
    def fragment(cls):
        return f"... on {cls.__name__} {{ id createdAt actor {{ url login __typename }} subject {{ url login __typename }} }}"

    @classmethod
    def parse(cls, data):
        return cls(id=data['id'], created_at=data['createdAt'],
                   actor=User.parse(data['actor']),
                   subject=User.parse(data['subject']))

    def prov(self, doc, mapper, issue_url):
        super().prov(doc, mapper, issue_url)

        subject_url = mapper.qname(self.subject.url)
        event_url = mapper.qname(self.url)

        doc.agent(subject_url)
        doc.wasAssociatedWith(event_url, agent=subject_url, other_attributes={'prov:role': 'github2prov:subject'})



class AddedToMergeQueueEvent(Event):
    def __init__(self, id: str, created_at: str, actor: User, enqueuer: User):
        super().__init__(id, created_at, actor)
        self.enqueuer = enqueuer

    def __repr__(self):
        return f"{rn(self)}(id={self.id}, created_at={self.created_at}, actor={self.actor}, enqueuer={self.enqueuer})"

    @classmethod
    def fragment(cls):
        return f"... on {cls.__name__} {{ id createdAt actor {{ url login __typename }} enqueuer {{ url login __typename }} }}"

    @classmethod
    def parse(cls, data):
        return cls(id=data['id'], created_at=data['createdAt'],
                   actor=User.parse(data['actor']),
                   enqueuer=User.parse(data['enqueuer']))

    def prov(self, doc, mapper, issue_url):
        super().prov(doc, mapper, issue_url)

        enqueuer_url = mapper.qname(self.enqueuer.url)
        event_url = mapper.qname(self.url)

        doc.agent(enqueuer_url)
        doc.wasAssociatedWith(event_url, agent=enqueuer_url, other_attributes={'prov:role': 'github2prov:enqueuer'})

class AutoMergeDisabledEvent(Event):
    def __init__(self, id: str, created_at: str, actor: User, reason: str, reason_code: int):
        super().__init__(id, created_at, actor)
        self.reason = reason
        self.reason_code = reason_code

    def __repr__(self):
        return f"{rn(self)}(id={self.id}, created_at={self.created_at}, actor={self.actor}, reason={self.reason}, reason_code={self.reason_code})"

    @classmethod
    def fragment(cls):
        return f"... on {cls.__name__} {{ id createdAt actor {{ url login __typename }} reason reasonCode }}"

    @classmethod
    def parse(cls, data):
        return cls(id=data['id'], created_at=data['createdAt'],
                   actor=User.parse(data['actor']),
                   reason=data['reason'],
                   reason_code=data['reason_code'])

    def prov(self, doc, mapper, issue_url):
        super().prov(doc, mapper, issue_url)

        event_url = mapper.qname(self.url)
        doc.activity(event_url, other_attributes={'github2prov:reason': self.reason, 'github2prov:reasonCode': self.reasonCode})


class AutoMergeEnabledEvent(EventWithEnabler):
    pass

class AutoRebaseEnabledEvent(EventWithEnabler):
    pass


class AutoSquashEnabledEvent(EventWithEnabler):
    pass


class AutomaticBaseChangeFailedEvent(Event):
    def __init__(self, id: str, created_at: str, actor: User, new_base, old_base):
        super().__init__(id, created_at, actor)
        self.new_base = new_base
        self.old_base = old_base

    def __repr__(self):
        return f"{rn(self)}(id={self.id}, created_at={self.created_at}, actor={self.actor}, new_base={self.new_base}, old_base={self.old_base})"

    @classmethod
    def fragment(cls):
        return f"... on {cls.__name__} {{ id createdAt actor {{ url login __typename }} newBase oldBase }}"

    @classmethod
    def parse(cls, data):
        return cls(id=data['id'], created_at=data['createdAt'],
                   actor=User.parse(data['actor']),
                   new_base=data['newBase'],
                   old_base=data['oldBase'])

    def prov(self, doc, mapper, issue_url):
        super().prov(doc, mapper, issue_url)
        #TODO


class AutomaticBaseChangeSucceededEvent(Event):
    def __init__(self, id: str, created_at: str, actor: User, new_base, old_base):
        super().__init__(id, created_at, actor)
        self.new_base = new_base
        self.old_base = old_base

    def __repr__(self):
        return f"{rn(self)}(id={self.id}, created_at={self.created_at}, actor={self.actor}, new_base={self.new_base}, old_base={self.old_base})"

    @classmethod
    def fragment(cls):
        return f"... on {cls.__name__} {{ id createdAt actor {{ url login __typename }} newBase oldBase }}"

    @classmethod
    def parse(cls, data):
        return cls(id=data['id'], created_at=data['createdAt'],
                   actor=User.parse(data['actor']),
                   new_base=data['newBase'],
                   old_base=data['oldBase'])

    def prov(self, doc, mapper, issue_url):
        super().prov(doc, mapper, issue_url)
        #TODO

class BaseRefChangedEvent(Event):
    # databaseId
    def __init__(self, id: str, created_at: str, actor: User, current_ref_name: str, previous_ref_name: str):
        super().__init__(id, created_at, actor)
        self.current_ref_name = current_ref_name
        self.previous_ref_name = previous_ref_name

    def __repr__(self):
        return f"{rn(self)}(id={self.id}, created_at={self.created_at}, actor={self.actor}, current_ref_name={self.current_ref_name}, previous_ref_name={self.previous_ref_name})"

    @classmethod
    def fragment(cls):
        return f"... on {cls.__name__} {{ id createdAt actor {{ url login __typename }} currentRefName previousRefName }}"

    @classmethod
    def parse(cls, data):
        return cls(id=data['id'], created_at=data['createdAt'],
                   actor=User.parse(data['actor']),
                   current_ref_name=data['currentRefName'],
                   previous_ref_name=data['previousRefName'])

    def prov(self, doc, mapper, issue_url):
        super().prov(doc, mapper, issue_url)
        #TODO


class BaseRefDeletedEvent(Event):
    def __init__(self, id: str, created_at: str, actor: User, base_ref_name: str):
        super().__init__(id, created_at, actor)
        self.base_ref_name = base_ref_name

    def __repr__(self):
        return f"{rn(self)}(id={self.id}, created_at={self.created_at}, actor={self.actor}, base_ref_name={self.base_ref_name})"

    @classmethod
    def fragment(cls):
        return f"... on {cls.__name__} {{ id createdAt actor {{ url login __typename }} baseRefName }}"

    @classmethod
    def parse(cls, data):
        return cls(id=data['id'], created_at=data['createdAt'],
                   actor=User.parse(data['actor']),
                   base_ref_name=data['baseRefName'])

    def prov(self, doc, mapper, issue_url):
        super().prov(doc, mapper, issue_url)
        #TODO


class BaseRefForcePushedEvent(Event):
    def __init__(self, id: str, created_at: str, actor:User, after_commit: Commit, before_commit: Commit):
        super().__init__(id, created_at, actor)
        self.after_commit = after_commit
        self.before_commit = before_commit

    def __repr__(self):
        return f"{rn(self)}(id={self.id}, created_at={self.created_at}, actor={self.actor}, after_commit={self.after_commit}, before_commit={self.before_commit})"

    @classmethod
    def fragment(cls):
        return f"... on {cls.__name__} {{ id createdAt actor {{ url login __typename }} afterCommit {{ commitUrl committedDate oid }} beforeCommit {{ commitUrl oid }} }}"

    @classmethod
    def parse(cls, data):
        return cls(id=data['id'], created_at=data['createdAt'],
                   actor=User.parse(data['actor']),
                   after_commit=Commit.parse(data['afterCommit']),
                   before_commit=Commit.parse(data['beforeCommit']))

    def prov(self, doc, mapper, issue_url):
        super().prov(doc, mapper, issue_url)
        #TODO


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
    # url

    def __init__(self, id: str, created_at: str, actor: User, commit: Commit):
        super().__init__(id, created_at, actor)
        self.commit = commit

    def __repr__(self):
        return f"{rn(self)}(id={self.id}, created_at={self.created_at}, actor={self.actor}, commit={self.commit})"

    @classmethod
    def fragment(cls):
        return f"... on {cls.__name__} {{ id createdAt actor {{ url login __typename }} commit {{ commitUrl committedDate oid }} }}"

    @classmethod
    def parse(cls, data):
        return cls(id=data['id'], created_at=data['createdAt'],
                   actor=User.parse(data['actor']),
                   commit=Commit.parse(data['commit']))

    def prov(self, doc, mapper, issue_url):
        super().prov(doc, mapper, issue_url)

        commit_url = mapper.qname(self.commit.commit_url)
        event_url = mapper.qname(self.url)
        doc.activity(commit_url)
        doc.wasInformedBy(event_url, commit_url)


class PullRequestCommit:
    # url
    # Bernard added parse and prov methods and has registered this class so 
    # that the converter.py can associate commits with PRs
    def __init__(self, id: str, commit: Commit, created_at: str):
        self.id = id
        self.commit = commit
        # Bernard added this to stop a crash in converter.py which accesses a created_at for sorting
        # it used to skip this class
        self.created_at=created_at
    def __repr__(self):
        return f"{rn(self)}(id={self.id}, commit={self.commit})"

    @classmethod
    def fragment(cls):
        return f"... on {cls.__name__} {{ id commit {{ commitUrl committedDate oid }} }} "

    # Bernard added    
    @classmethod
    def parse(cls, data):
        return cls(id=data['id'], commit=Commit.parse(data['commit']),
                   created_at=data['commit']['committedDate'])  
    # Bernard added     
    def prov(self, doc, mapper, issue_url):
        # create a wasInfluencedBy from pr to commit
        pr_url = mapper.qname(issue_url)
        commit_url = mapper.qname(self.commit.commit_url)
        doc.activity(commit_url)# just in case there isn't one
        doc.wasInfluencedBy(pr_url, commit_url)






class PullRequestReview(Event):
    # databaseId
    # url
    def __init__(self, id: str, created_at: str, actor: User, body: str, commit: Commit):
        super().__init__(id, created_at, actor)
        self.body = body
        self.commit = commit

    def __repr__(self):
        return f"{rn(self)}(id={self.id}, created_at={self.created_at}, actor={self.actor}, body={self.body}, commit={self.commit})"

    @classmethod
    def fragment(cls):
        return f"... on {cls.__name__} {{ id createdAt author {{ url login __typename }} body commit {{ commitUrl committedDate oid }} }}"

    @classmethod
    def parse(cls, data):
        return cls(id=data['id'], created_at=data['createdAt'],
                   actor=User.parse(data['author']),
                   body=data['body'],
                   commit=Commit.parse(data['commit']))

    def prov(self, doc, mapper, issue_url):
        super().prov(doc, mapper, issue_url)

        commit_url = mapper.qname(self.commit.commit_url)
        event_url = mapper.qname(self.url)
        doc.activity(commit_url)
        doc.wasInformedBy(event_url, commit_url)
        doc.activity(event_url, other_attributes={'github2prov:body': self.body})


class PullRequestRevisionMarker:
    def __init__(self, created_at: str):
        self.created_at = created_at
        self.number = -1

    def __repr__(self):
        return f"{rn(self)}(created_at={self.created_at})"

    @classmethod
    def fragment(cls):
        return f"... on {cls.__name__} {{ createdAt }}"

    @classmethod
    def parse(cls, data):
        return cls(created_at=data['createdAt'])

    def prov(self, doc, mapper, issue_url):
        super().prov(doc, mapper, issue_url)
        #TODO


class ReadyForReviewEvent(Event):
    # url
    def __init__(self, id: str, created_at: str, actor: User, resource_path):
        super().__init__(id, created_at, actor)
        self.resource_path = resource_path

    def __repr__(self):
        return f"{rn(self)}(id={self.id}, created_at={self.created_at}, actor={self.actor}, resource_path={self.resource_path})"

    @classmethod
    def fragment(cls):
        return f"... on {cls.__name__} {{ id createdAt actor {{ url login __typename }} resourcePath }}"

    @classmethod
    def parse(cls, data):
        return cls(id=data['id'], created_at=data['createdAt'],
                   actor=User.parse(data['actor']),
                   resource_path=data['resourcePath'])

    def prov(self, doc, mapper, issue_url):
        super().prov(doc, mapper, issue_url)
        #TODO


class RemovedFromMergeQueueEvent(Event):
    def __init__(self, id: str, created_at: str, actor: User, reason: str, before_commit: Commit):
        super().__init__(id, created_at, actor)
        self.reason = reason
        self.before_commit = before_commit

    def __repr__(self):
        return f"{rn(self)}(id={self.id}, created_at={self.created_at}, actor={self.actor}, reason={self.reason}, before_commit={self.before_commit})"

    @classmethod
    def fragment(cls):
        return f"... on {cls.__name__} {{ id createdAt actor {{ url login __typename }} reason beforeCommit {{ commitUrl committedDate oid }} }}"

    @classmethod
    def parse(cls, data):
        return cls(id=data['id'], created_at=data['createdAt'],
                   actor=User.parse(data['actor']),
                   reason=data['reason'],
                   before_commit=Commit.parse(data['beforeCommit']))

    def prov(self, doc, mapper, issue_url):
        super().prov(doc, mapper, issue_url)
        #TODO


class ReviewDismissedEvent(Event):
    # databaseId
    # url
    pass


class ReviewRequestRemovedEvent(Event):
    pass


class ReviewRequestedEvent(Event):
    pass

_allEvents = [
AddedToProjectEvent, AssignedEvent, ClosedEvent, CommentDeletedEvent,
ConnectedEvent, ConvertedNoteToIssueEvent, ConvertedToDiscussionEvent,
CrossReferencedEvent, DemilestonedEvent, DisconnectedEvent, IssueComment,
LabeledEvent, LockedEvent, MarkedAsDuplicateEvent, MentionedEvent,
MilestonedEvent, MovedColumnsInProjectEvent, PinnedEvent, ReferencedEvent,
RemovedFromProjectEvent, RenamedTitleEvent, ReopenedEvent,
SubscribedEvent, TransferredEvent, UnassignedEvent, UnlabeledEvent,
UnlockedEvent, UnmarkedAsDuplicateEvent, UnpinnedEvent, UnsubscribedEvent,
UserBlockedEvent, AddedToMergeQueueEvent, AutoMergeDisabledEvent,
AutoMergeEnabledEvent, AutoRebaseEnabledEvent, AutoSquashEnabledEvent,
AutomaticBaseChangeFailedEvent, AutomaticBaseChangeSucceededEvent,
BaseRefChangedEvent, BaseRefDeletedEvent, BaseRefForcePushedEvent,
ConvertToDraftEvent, DeployedEvent, DeploymentEnvironmentChangedEvent,
HeadRefDeletedEvent, HeadRefForcePushedEvent, HeadRefRestoredEvent,
MergedEvent, PullRequestReview, PullRequestRevisionMarker,
ReadyForReviewEvent, RemovedFromMergeQueueEvent, RemovedFromProjectEvent,
ReviewDismissedEvent, ReviewRequestRemovedEvent, ReviewRequestedEvent,
PullRequestCommit, # bernard added ths so converter/py can recognise it
]
allEvents = { c.__name__: c for c in _allEvents }
