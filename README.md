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

# TODO

* Reactions on IssueComments?
* Are pull requests treated differently? are they missing
