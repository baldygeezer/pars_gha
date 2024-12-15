import os
import re
import subprocess


def run_git2prov(repo_name: str, repodir_path: str, dry_run: bool):
    # Used by re.sub as custom string replacement function
    def reference_replace(match):
        return match.group(1) + re.sub('[^A-Za-z0-9_-]', '', match.group(2)) + match.group(3)

    repo_url = "https://github.com/" + repo_name

    # If dry-running, don't capture stdout or stderr
    # NB: error log will generated even if no errors are encountered
    output_filepath = os.path.join(repodir_path, 'git2prov.ttl') if not dry_run else '/dev/null'
    error_filepath = os.path.join(repodir_path, 'git2prov-error.log') if not dry_run else '/dev/null'

    # Need to ensure utf-8 encoding is honoured for output, otherwise uploading to Fuseki will fail
    # so open file for writing as bytes, and properly decode before processing, and re-encode upon writing
    with open(output_filepath, 'wb') as output_file:
        with open(error_filepath, 'w') as error_file:
            # Need to process output from git2prov line by line to remove the files listed
            # at the start of the output
            pipe = subprocess.Popen(['git2prov', repo_url, 'PROV-O'], stdout=subprocess.PIPE, stderr=error_file, encoding='utf-8')

            # Once we've found the first TTL 'prefix', begin capturing output in file
            found_prefix = False
            while True:
                line = pipe.stdout.readline()
                if not line:
                    break

                if '@prefix' in line:
                    found_prefix = True

                if found_prefix:
                    # Sanitise strings to remove invalid strings (double-quotes within double-quotes, etc.)
                    # TODO: do proper sanitisation, including actual comment
                    line = re.sub('(rdfs:label\s+)(.*)@en', r'\1"Some comment"@en', line)
                    # Remove any characters that may be rejected by Fuseki in any entity or activity references
                    #line = re.sub(r'(result:)([^ \t]+)(.*)', file_commit_replace, line)
                    line = re.sub(r'(result:)(\S+)([\s]*)', reference_replace, line)
                    output_file.write(line.encode('utf-8'))
