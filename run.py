import typing
import time

import click
from decouple import config
import logging

import graphql

from model import *
from crawler import crawl
from converter import convert

logger = logging.getLogger(__name__)

graphql_endpoint = config('ENDPOINT', default='https://api.github.com/graphql')
graphql_token = config('TOKEN')

@click.group()
def cli():
    logging.basicConfig(level=config('LOG_LEVEL', default='INFO'))

@cli.command(name='crawl')
@click.option('-i', '--num_issues', 'num_issues', required=False, type=click.INT, default=10, help='Specify number of issues/prs per query')
@click.option('-e', '--num_events', 'num_events', required=False, type=click.INT, default=250, help='Specify events per issues/prs query')
@click.argument('repo') # '-r', '--repo', 'repos', required=True, help='repo to crawl')
def cmd_crawl(
    repo,
    num_issues: int,
    num_events: int
):
    repos = [repo]
    for r in repos:
        #try:
           crawl(r, graphql_endpoint, graphql_token, num_issues=num_issues, num_events=num_events)
        #except Exception as e:
        #   print(e)

@cli.command(name='convert')
@click.argument('repo') # '-r', '--repo', 'repos', required=True, help='repo to crawl')
def cmd_convert(
    repo
):
    repos = [repo]
    for r in repos:
        #try:
           convert(r)
        #except Exception as e:
        #   print(e)

if __name__ == '__main__':
    cli()
