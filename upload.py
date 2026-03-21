import logging
import os
import requests

logger = logging.getLogger(__name__)

def upload(repo: str, endpoint: str, username: str, password: str, directory: str = 'output'):
    """
    Uploads the converted Turtle file (merged.ttl or merged.ttl.gz) from the repo's
    output directory to a Jena Fuseki endpoint.
    If both exist, the most recent one is used.
    """
    # Sanitize repo name for path
    repo_path = repo.replace("/", "_")
    target_dir = os.path.join(directory, repo_path)

    if not os.path.exists(target_dir):
        logger.warning(f"Directory {target_dir} does not exist. Skipping.")
        return

    # Files we are interested in
    candidates = ['merged.ttl', 'merged.ttl.gz']
    existing_files = []

    for cand in candidates:
        full_path = os.path.join(target_dir, cand)
        if os.path.exists(full_path):
            existing_files.append(full_path)

    if not existing_files:
        logger.warning(f"No merged.ttl or merged.ttl.gz found in {target_dir}. Skipping.")
        return

    # Sort by modification time to get the most recent one
    existing_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
    file_to_upload = existing_files[0]
    filename = os.path.basename(file_to_upload)

    # Fuseki Graph Store Protocol endpoint
    upload_url = f"{endpoint.rstrip('/')}/data"

    graph_uri = f"https://github.com/repos/{repo}"

    headers = {'Content-Type': 'text/turtle'}
    if filename.endswith('.gz'):
        headers['Content-Encoding'] = 'gzip'

    logger.info(f"Uploading {file_to_upload} to {upload_url} with graph {graph_uri}")

    with open(file_to_upload, 'rb') as f:
        try:
            # Using POST to append data to the specified named graph
            response = requests.post(
                upload_url,
                params={'graph': graph_uri},
                data=f,
                headers=headers,
                auth=(username, password)
            )

            response.raise_for_status()
            logger.info(f"Successfully uploaded {filename}")
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to upload {filename}: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response: {e.response.text}")
            raise
