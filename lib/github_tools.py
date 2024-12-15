import pprint


def user_url(user):
  return 'https://api.github.com/users/' + str(user)


def repo_url(repo):
  return 'https://api.github.com/repos/' + str(repo)


def issue_url(repo, issue):
  return repo_url(repo) + '/issues/' + str(issue)


def commits_url(repo, commit):
  return repo_url(repo) + '/commits/' + str(commit)


def rindex(mylist, myvalue):
    return len(mylist) - mylist[::-1].index(myvalue) - 1


class QNameMinter():
    def __init__(self, doc):
        self._doc = doc
        self._count = 0

    def qname(self, uri):
        doc = self._doc
        candidate = ""
        candidate_ns = None

        for ns in doc.get_registered_namespaces():
            if uri.startswith(ns.uri):
                if len(ns.uri)>len(candidate):
                    candidate_ns = ns
                    candidate = ns.uri

        if not candidate_ns:
            part = uri[:rindex(uri, "/")]
            prefix = "ns{}".format(self._count)
            candidate_ns = self._doc.add_namespace(prefix, part+"/")

        return candidate_ns.qname(uri)


def ppprint(ob):
    pp = pprint.PrettyPrinter(indent=4)
    pp.pprint(ob)
