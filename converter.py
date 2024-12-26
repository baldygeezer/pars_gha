
import json
from pathlib import Path

import logging
logger = logging.getLogger(__name__)

from model import Repo

from lib.github_prov import setup_repo, output_prov
from lib.github_tools import QNameMinter

supported_types = {
    'Issue': 'http://purl.org/github2prov/issue',
    'PullRequest': 'http://purl.org/github2prov/pull'
}

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

def add_prov_for_issue_or_pull_request(repo, doc, mapper, data):
    i = make_issue_from_api(data)
    i.prov(repo, doc, mapper)

def make_issue_from_api(json):
    info = json['info']
    typ = info['__typename']
    if typ not in supported_types:
        raise Exception(f'unknown type {typ}')

    issue_url = mapper.qname(info['url'])
    user_url = mapper.qname(info['author']['url'])
    created_at = info['createdAt']

    return GithubIssue(issue_url, user_url, created_at, pull_request, typ) 

def make_event_from_api(json):
    pass

def add_prov_for_issue_or_pull_request_event(repo, doc, mapper, event):
    issue_version = mapper.qname(event.issue + '#' + str(event.number))
    event_url = mapper.qname(event.url)

    doc.activity(event_url, event.created_at, event.created_at, {'prov:type': mapper.qname('http://purl.org/github2prov/' + event.typ)})

    if event.user:
        actor_url = mapper.qname(event.user)
        doc.agent(actor_url)
        doc.wasAssociatedWith(event_url, actor_url)

    doc.entity(issue_version, {'prov:type': mapper.qname('http://purl.org/github2prov/issue_version')})
    doc.specializationOf(issue_version, event.issue)

    # Following event.number being populated
    postfix = "" if event.number < 2 else "#" + str(event.number - 1)
    ip = mapper.qname(event.url + postfix)

    doc.used(event_url, ip)
    doc.wasGeneratedBy(issue_version, event_url)

    if event.commit:
        commit_url = mapper.qname(event.commit)
        doc.wasInformedBy(event_url, commit_url)
        doc.activity(commit_url)


def convert(repo_slug):
    r = Repo(repo_slug)
    _, doc, qm = setup_repo(repo_slug)

    directory_path = r.directory()
    for file_path in directory_path.glob('*.json'):
        try:
            with open(file_path, 'r') as file:
                logger.debug(f"processing {file_path.name}")
                data = json.load(file)  # Load the JSON content
                add_prov_for_issue_or_pull_request(repo_slug, doc, qm, data)
        except Exception as e:
            logger.error(f"processing {file_path.name} failed: {e}")
    output_prov(directory_path, doc, 'merged', True)
