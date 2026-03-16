import os
import prov
import gzip

from prov.model import ProvDocument

from lib.github_tools import QNameMinter


def setup_repo(repo):
    # urls for namespaces
    user_url = 'https://api.github.com/users/'
    github_url = "https://github.com/"
    project_url = "https://api.github.com/repos/" + repo + "/"
    github_project_url = github_url + repo + "/"
    issues_url = project_url + "issues/"
    comments_url = issues_url + "comments/"
    pulls_api_url = project_url + 'pulls/'
    tree_api_url = project_url + 'tree/'
    pulls_uri = github_project_url + 'pull/'
    commits_url = github_project_url + "commits/"

    d1 = ProvDocument()

    # add bespoke namespaces
    d1.add_namespace('fullResult', "&serialization=PROV-O#")
    d1.add_namespace('result', "http://localhost/#")
    d1.add_namespace('rdfs', "http://www.w3.org/2000/01/rdf-schema#")

    #add namespaces
    d1.add_namespace('repos', "https://api.github.com/repos/")
    d1.add_namespace('users', user_url)
    d1.add_namespace('github', github_url)
    d1.add_namespace('events', issues_url + 'events/')
    d1.add_namespace('issues', issues_url)
    d1.add_namespace('pulls_api', pulls_api_url)
    d1.add_namespace('tree_api', tree_api_url)
    d1.add_namespace('pulls_uri', pulls_uri)
    d1.add_namespace('comments', comments_url)
    d1.add_namespace('repo', github_project_url)
    d1.add_namespace('commits', commits_url)
    d1.add_namespace('localhost', 'http://localhost/')
    d1.add_namespace('github2prov', 'http://purl.org/github2prov/')

    # full name of project
    project_entity = None
    #project_entity = d1.entity(repo.full_name.replace("/", "_") + ":")
    return project_entity, d1, QNameMinter(d1)


def output_prov(repodir_path: str, prov_doc: prov.model.ProvDocument, info_type: str, provn: bool, compress: bool):
    def open_file(filename, compress):
        if compress:
            return gzip.open(filename+".gz", 'wt', encoding='utf-8')
        else:
            return open(filename, 'w', encoding='utf-8')

    provo_output_filepath = os.path.join(repodir_path, info_type + '.ttl');
    with open_file(provo_output_filepath, compress) as text_file:
        text_file.write(prov_doc.serialize(format='rdf', rdf_format='ttl'))

    if provn:
        provn_output_filepath = os.path.join(repodir_path, info_type + '.provn');
        with open_file(provo_output_filepath, compress) as text_file:
            text_file.write(prov_doc.get_provn())
