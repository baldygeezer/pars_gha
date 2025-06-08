
import json
from pathlib import Path

import re

import logging
logger = logging.getLogger(__name__)

from model import Repo

from lib.github_prov import setup_repo, output_prov
from lib.github_tools import QNameMinter

supported_types = {
    'Issue': 'http://purl.org/github2prov/issue',
    'PullRequest': 'http://purl.org/github2prov/pull'
}

import github

class GithubIssue:
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

class GithubPullRequest(GithubIssue):
    def __init__(self, url, user, created_at):
        self.url = url
        self.user = user
        self.created_at = created_at
    def __str__(self):
        return "GithubPullRequest(url=%s, user=%s, created_at=%s)"%(self.url, self.user, self.created_at)

class GithubIssueEvent:
    def __init__(self, url, issue, user, created_at, number, typ, commit=None):
        self.url = url
        self.issue = issue
        self.user = user
        self.created_at = created_at
        self.number = number
        self.typ = typ
        self.commit = commit

def add_prov_for_commit(repo, doc, mapper, data):
    # grep '{' repo.responses | jq '.[]' | jq -c | jq -s 'sort_by(.commit.author.date)' -c > repo/commits.json
    try:
        c = github.GithubCommit.parse(data)
        c.prov(doc, mapper)
    except Exception as exp:
        logger.exception("parse issue failed")
        logger.error(data)
        raise(exp)

def add_prov_for_issue_or_pull_request(repo, doc, mapper, data):
    i = None
    try:
        if data['info']['__typename'] == "Issue":
            i = github.Issue.parse(data['info'])
            i.prov(doc, mapper)
        elif data['info']['__typename'] == "PullRequest":
            i = github.PullRequest.parse(data['info'])
            i.prov(doc, mapper)
        else:
            raise(Exception("unknown type"))
    except Exception as exp:
        logger.exception("parse issue failed")
        logger.error(data['info'])
        raise(exp)
    events = []
    for ed in data['events']:
        try:
            e = parse_event(ed, i.url)
            # Mentioned and subscribed events seem to be automatically created
            # and may not imply any contribution to the issue
            # Another way would be to limit them to one per user per issue
            if e and e.__class__.__name__ not in ['MentionedEvent', 'SubscribedEvent']:
                events.append(e)
        except Exception as exp:
            logger.exception("parse event failed")
            logger.error(ed)
            raise(exp)

    sorted(events, key=lambda x: getattr(x, 'created_at'))
    count = 1
    for event in events:
        event.number = count
        count += 1

    for event in events:
        event.prov(doc, mapper, i.url)

def parse_event(event_data, issue_url):
    """Parse a single event from the data."""
    event_type = event_data['__typename']
    if event_type == "PullRequestCommit":
        return None
    ec = github.allEvents.get(event_type, None)
    if not ec:
        return None
    e = ec.parse(event_data)
    if 'url' in event_data:
        u = event_data['url']
        e.url = u.replace('#event-', '/events/')
    else:
        # prov python library is correctly output provn with qnames with the
        # follow characters:
        # "=" | "'" | "(" | ")" | "," | "-" | ":" | ";" | "[" | "]" | "."
        i = re.sub(r'[=\'(),-:;\[\]]', '', e.id)
        u = issue_url + '/events/' + i
        e.url  = u
    return e

def add_prov_for_stargazers(repo_slug, doc, mapper, data):
    s = github.Stargazer.parse(data)
    s.prov(repo_slug, doc, mapper)

def add_prov_for_repo_info(repo_slug, doc, mapper, data):
    r = github.RepoInfo.parse(data)
    r.prov(doc, mapper)

def convert(repo_slug, directory=None, provn=True):
    if not Path(directory).exists():
        os.mkdir(directory)

    r = Repo(repo_slug)
    _, doc, qm = setup_repo(repo_slug)

    directory_path = r.directory(base=directory)
    for file_path in directory_path.glob('*.json'):
        try:
            with open(file_path, 'r') as file:
                logger.debug(f"processing {file_path.name}")
                data = json.load(file)  # Load the JSON content
                if str(file_path).endswith("commits.json"):
                    for x in data:
                        add_prov_for_commit(repo_slug, doc, qm, x)
                elif str(file_path).endswith("repo_info.json"):
                    add_prov_for_repo_info(repo_slug, doc, qm, data)
                elif str(file_path).endswith("stargazers.json"):
                    add_prov_for_stargazers(repo_slug, doc, qm, data)
                else:
                    add_prov_for_issue_or_pull_request(repo_slug, doc, qm, data)
        except Exception as e:
            logger.error(f"processing {file_path.name} failed: {e}")
            logger.exception("exception")
    print("outputing", directory_path)
    output_prov(directory_path, doc, 'merged', provn)
