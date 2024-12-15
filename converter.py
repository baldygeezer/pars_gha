
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

def add_prov_for_issue_or_pull_request(repo, doc, mapper, json):
    info = json['info']
    typ = info['__typename']
    if typ not in supported_types:
        raise Exception(f'unknown type {typ}')

    issue_url = mapper.qname(info['url'])
    user_url = mapper.qname(info['author']['url'])
    create_event_url = mapper.qname(info['url'] + '#create')
    doc.agent(user_url)
    doc.entity(issue_url, {'prov:type': mapper.qname(supported_types[typ])})
    doc.wasAttributedTo(issue_url, user_url)
    doc.activity(create_event_url,
        info['createdAt'],
        info['createdAt'],
        {'prov:type': mapper.qname('http://purl.org/github2prov/created')})
    doc.wasAssociatedWith(create_event_url, user_url)
    doc.wasGeneratedBy(issue_url, create_event_url)

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
