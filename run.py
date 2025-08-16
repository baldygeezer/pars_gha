import itertools
import logging
import time
import typing

import click
from decouple import config

import graphql

from model import *
from crawler import crawl,Poster
from converter import convert
from git2prov import git2prov

logger = logging.getLogger(__name__)

graphql_endpoint = config('ENDPOINT', default='https://api.github.com/graphql')
graphql_token = config('TOKEN')

@click.group()
def cli():
    logging.basicConfig(level=config('LOG_LEVEL', default='INFO'))

@cli.command(name='crawl')
@click.option('-i', '--num_issues', 'num_issues', required=False, type=click.INT, default=50, help='Specify number of issues/prs per query')
@click.option('-e', '--num_events', 'num_events', required=False, type=click.INT, default=250, help='Specify events per issues/prs query')
@click.argument('repo', nargs=-1)
@click.option('-f', '--file', 'repos_file', required=False, type=click.File('r'), help='File with one GitHub repo per line in <user>/<repo_name> format.')
@click.option('-d', '--directory', 'working_dir', required=False, type=click.Path(file_okay=False, dir_okay=True, readable=True), default='output', help='Directory to write output to')
def cmd_crawl(
    repo,
    num_issues: int,
    num_events: int,
    repos_file: typing.Optional[click.File],
    working_dir: typing.Optional[click.Path]
):
    repos = []
    if repos_file is not None:
        repos = list(itertools.chain(repos, map(str.strip, repos_file)))
    elif repo is not None:
        repos = list(repo)

    for r in repos:
        try:
            crawl(r, graphql_endpoint, graphql_token, num_issues=num_issues, num_events=num_events, directory=working_dir)
            time.sleep(0.5)
        except Exception as e:
           print(r, e)

@cli.command(name='convert')
@click.argument('repo', nargs=-1)
@click.option('-f', '--file', 'repos_file', required=False, type=click.File('r'), help='File with one GitHub repo per line in <user>/<repo_name> format.')
@click.option('-d', '--directory', 'working_dir', required=False, type=click.Path(file_okay=False, dir_okay=True, readable=True), default='output', help='Directory to write output to')
@click.option('-n', '--provn', 'provn', required=False, is_flag=True, default=False, help='Whether to generate PROV-N records.')
@click.option('-z', '--compress', 'compress', required=False, is_flag=True, default=False, help='Whether to write compressed output.')
def cmd_convert(
    repo,
    repos_file: typing.Optional[click.File],
    working_dir: typing.Optional[click.Path],
    provn: bool,
    compress: bool
):
    repos = []
    if repos_file is not None:
        repos = list(itertools.chain(repos, map(str.strip, repos_file)))
    elif repo is not None:
        repos = list(repo)

    for r in repos:
        #try:
           convert(r, directory=working_dir, provn=provn, compress=compress)
        #except Exception as e:
        #   print(e)

@cli.command(name='git2prov')
@click.argument('repo', nargs=-1)
@click.option('-f', '--file', 'repos_file', required=False, type=click.File('r'), help='File with one GitHub repo per line in <user>/<repo_name> format.')
@click.option('-d', '--directory', 'working_dir', required=False, type=click.Path(file_okay=False, dir_okay=True, readable=True), default='output', help='Directory to write output to')
def cmd_git2prov(
    repo,
    repos_file: typing.Optional[click.File],
    working_dir: typing.Optional[click.Path]
):
    repos = []
    if repos_file is not None:
        repos = list(itertools.chain(repos, map(str.strip, repos_file)))
    elif repo is not None:
        repos = list(repo)

    for r in repos:
        #try:
           git2prov(r, directory=working_dir)
        #except Exception as e:
        #   print(e)

@cli.command(name='ratelimit')
def cmd_ratelimit():
    poster = Poster(endpoint=graphql_endpoint, token=graphql_token)
    q = "query { viewer { login } rateLimit { limit remaining used resetAt } }"
    resp = poster.post(dict(query=q))
    data = resp.json()
    print(data)

if __name__ == '__main__':
    cli()
