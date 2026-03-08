# Introduction

This python tool will crawl a github repository and generate provenance. It generates
provenance based on the issues, pull requests and commits that have been made.

It uses GitHub's graphql api. In contrast to other crawlers, it attempts to minimise
the number of queries that have to be made so as not to run a foul of the rate limit.
It does this by:

* and initial query requesting issues using pagination and for each issue, a page
  of events
* any issue where the events returned were not all the events, will need further
  queries using the events pagination cursor
* these follow on queries are grouped together into batches
* the same is preformed for pull requests

With reasonable pagination limits for issues and events most issues are downloaded
in the first try and its only particularly long issues that need further querying.

The GitHub api considers the complexity of the query and so only a limited set
of information is requested from the API (references to other objects in the API
are considered expensive).

# Commands

## Find

Finds GitHub repositories that contain a specific search term in their `README.md`. It can be filtered by a repository creation date range using the `-s/--start` and `-e/--end` options (formatted as `YYYY-MM-DD`). Since the GitHub Search API is limited to 1000 results, the command automatically partitions the date range into smaller chunks to ensure all matching repositories are found.

```bash
python run.py find "search term" --start 2023-01-01 --end 2023-12-31
```

### JSON Output
The command outputs a JSON array of repository objects to `stdout`. Each object contains:
- `nameWithOwner`: The full repository name (e.g., `user/repo`).
- `createdAt`: The ISO 8601 creation timestamp.
- `readme`: An object containing the raw `text` of the repository's `README.md`.

Example:
```json
[
  {
    "nameWithOwner": "user/repo",
    "createdAt": "2023-05-24T10:00:00Z",
    "readme": {
      "text": "# README content..."
    }
  }
]
```

## Crawl

Crawls a GitHub repository and saves its metadata (Issues, Pull Requests, Commits, Releases, Stargazers, etc.) to JSON files in the specified output directory.

- `-i, --num_issues`: Number of issues/PRs per query (default: 50).
- `-e, --num_events`: Number of events per issue/PR query (default: 250).
- `-f, --file`: File containing a list of repositories (one `user/repo` per line).
- `-d, --directory`: Directory to write output to (default: `output`).
- `-r, --recrawl`: Resume crawling using existing data.

```bash
python run.py crawl user/repo
```

## Convert

Converts the JSON metadata collected by the `crawl` command into provenance (PROV) records in the turtle (.ttl) respresentation, with PROV-N being an option. The `merged.ttl` is generated in the output directory which is
constructued based on the output directory and the repo name. Its advised to use the compress option that with generate a `merged.ttl.gz` file.

- `-f, --file`: File containing a list of repositories to convert.
- `-d, --directory`: Directory containing the crawled JSON data (default: `output`).
- `-n, --provn`: Generate PROV-N records.
- `-z, --compress`: Write compressed output.

```bash
python run.py convert user/repo --provn
```

## Ratelimit

Checks the current status of the GitHub GraphQL API rate limit. It displays the total limit, remaining requests, used requests, and the time when the limit will reset.

```bash
python run.py ratelimit
```


# TODO

* Reactions on IssueComments?
* Are pull requests treated differently? are they missing
