import graphql
from crawler import Poster
import json
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

import logging
logger = logging.getLogger(__name__)

class RangeTooWide(Exception):
    def __init__(self, total):
        super().__init__(f'Range Too Wide: {total} results')
        self.total = total

def search_for(poster, term, start_date, end_date, num_per_page, include_readme=False, cursor=None):
    d = ""
    if start_date and not end_date:
        d= "created:>=" + start_date
    if end_date and not start_date:
        d= "created:<=" + start_date
    if start_date and end_date:
        d= f'created:{start_date}..{end_date}'
    search = f'{term} in:readme {d} sort:created-asc'
    cursor = None
    searching = True
    results = []
    while(searching):
        query = graphql.search_repos(cursor, include_readme)
        body = {
                'query': query,
                'variables': {
                    'term': search,
                    'num_per_page': num_per_page,
                }
        }
        resp = poster.post(body)

        logger.error(f'post response had error code {resp.status_code} {body}')

        data = resp.json()
        search_results = data["data"]["search"]

        if search_results["repositoryCount"] > 1000:
            raise RangeTooWide(search_results["repositoryCount"])

        results.extend([x['node'] for x in search_results["edges"]])
        searching = search_results["pageInfo"]["hasNextPage"]
        cursor =    search_results["pageInfo"]["endCursor"]
        if num_per_page == 0:
            searching = False
    return results

"""
Find GitHub repositories that were created in a specific time range and whose
repository README.md file contains a given search term

GitHub's search APIs are limited to 1000 search results so inorder 
"""
def find(graphql_endpoint, graphql_token, term, start_date=None, end_date=None, include_readme=False):
    poster = Poster(endpoint=graphql_endpoint, token=graphql_token)
    all_results = []

    if not start_date or not end_date:
        try:
            results = search_for(poster, term, start_date, end_date, 50, include_readme)
            all_results.extend(results)
        except RangeTooWide as e:
            print(f"range too wide: {e.total}")
        print(json.dumps(all_results))
        return

    try:
        current_start = datetime.strptime(start_date, "%Y-%m-%d").date()
        target_end = datetime.strptime(end_date, "%Y-%m-%d").date()
    except ValueError:
        logger.error("Invalid date format. Use YYYY-MM-DD")
        return

    durations = [
        relativedelta(years=1),
        relativedelta(months=1),
        relativedelta(weeks=1),
        relativedelta(days=1)
    ]
    
    current_duration_idx = 0
    
    while current_start <= target_end:
        duration = durations[current_duration_idx]
        
        # Calculate end for this chunk (inclusive)
        chunk_end = current_start + duration - timedelta(days=1)
        
        if chunk_end > target_end:
            chunk_end = target_end
            
        s_date_str = current_start.isoformat()
        e_date_str = chunk_end.isoformat()
        
        try:
            results = search_for(poster, term, s_date_str, e_date_str, 50, include_readme)
            all_results.extend(results)
            
            # Success, advance time
            current_start = chunk_end + timedelta(days=1)
            # Reset to largest duration for next chunk
            current_duration_idx = 0
            
        except RangeTooWide:
            # If range is too wide, reduce duration
            if current_duration_idx < len(durations) - 1:
                current_duration_idx += 1
            else:
                # Already at smallest duration (1 day) and still too wide
                print(f"range too wide even at 1 day: {s_date_str}..{e_date_str}")
                # Skip this day to avoid infinite loop
                current_start = chunk_end + timedelta(days=1)
                current_duration_idx = 0

    print(json.dumps(all_results))
