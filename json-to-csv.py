import json
import csv
import difflib
import os
from textwrap import indent
import requests
import csv
import time

from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

DEFAULT_TIMEOUT = 2 # seconds

class TimeoutHTTPAdapter(HTTPAdapter):
    def __init__(self, *args, **kwargs):
        self.timeout = DEFAULT_TIMEOUT
        if "timeout" in kwargs:
            self.timeout = kwargs["timeout"]
            del kwargs["timeout"]
        super().__init__(*args, **kwargs)

    def send(self, request, **kwargs):
        timeout = kwargs.get("timeout")
        if timeout is None:
            kwargs["timeout"] = self.timeout
        return super().send(request, **kwargs)

r = requests.Session()
retry_strategy = Retry(
    total=3,
    backoff_factor=1,
    status_forcelist=[429, 500, 502, 503, 504, 104],
    method_whitelist=["HEAD", "GET", "POST", "OPTIONS"]
)

r.mount("http://", TimeoutHTTPAdapter(max_retries=retry_strategy))
r.mount("https://", TimeoutHTTPAdapter(max_retries=retry_strategy))

#fields = [ 'commit_node_id', 'age', 'message',  'user' ]

# ultra pro max juggaad, do not try this at home
# wtf am I even writing
# So yeah throw git diff at the problem why fucking not 
def generate_diff( data ):
    src_txt = []
    dest_txt = []
    for i in data['edits']:
        src_txt.append(i['src']['text'])
        dest_txt.append(i['tgt']['text'])
    with open( 'src.txt', 'w+' ) as src_file:
        src_file.write( ('\n' * 20).join(src_txt) )
    with open( 'dest.txt', 'w+' ) as dest_file:
        dest_file.write( ('\n' * 20).join(dest_txt) )
    os.system( 'git --no-pager diff -U0 --no-index src.txt dest.txt' )
    os.system( 'rm -rf src.txt dest.txt' )

github_token_id = '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' # put token here


auth_param_construct = { 'Authorization': f'Bearer {github_token_id}' }

# Opening JSON file and loading the data
# into the variable data
with open('github-typo-corpus.v1.0.0.jsonl') as json_file:
    data = list(json_file)

with open('commit_blame_query.gql') as commit_blame_gql_file:
    commit_blame_gql_qry = commit_blame_gql_file.read()

with open('text_query.gql') as text_gql_file:
    text_gql_qry = text_gql_file.read()
csv_file = open( 'commit_data.csv', 'a')
csv_writer = csv.writer(csv_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
#csv_writer.writerow(fields)
count = 0
higher_than = int(input('Entry to start from: '))
bonk_file = open( 'bonk.txt', 'a' )
#n = int(input('Data point to pretty print: '))
for json_line in data:
    count += 1 
    if count < higher_than:
        continue
    curr_data = json.loads(json_line)
    print('[*] Waiting for 0.5 secs praying to god that the mighty gods of github don\'t rate-limit us')
    time.sleep(0.1)
    print(f'[+] Working on datapoint number {count}')
    #print(json.dumps(curr_data, indent=4))
    #generate_diff( curr_data )
    repo_data = curr_data[ 'repo' ].replace( 'https://github.com', '' ).split('/')
    repo = repo_data[2]
    owner = repo_data[1]
    try:
        resp = r.get( f'https://api.github.com/repos/{owner}/{repo}/commits/{curr_data["commit"]}', headers=auth_param_construct )
        #print( curr_data[ 'repo' ] )
        #print(json.loads( resp.text ))
        parents = json.loads( resp.text )["parents"]
        parent_url = parents[0]['url']
        parent_resp = r.get( parent_url, headers=auth_param_construct )
        for edit in curr_data[ 'edits' ]:
            parent_resp_json = json.loads( parent_resp.text )
            commit_blame_qr = commit_blame_gql_qry.replace( '$parent_node_id', parent_resp_json['node_id'] )
            commit_blame_qr = commit_blame_qr.replace( '$filename', edit['src']['path'] )
            commit_blame_grql_resp = r.post( 'https://api.github.com/graphql', json={'query': commit_blame_qr}, headers=auth_param_construct )
            commit_blame_qr = json.loads(commit_blame_grql_resp.text)
            file_node_id = commit_blame_qr['data']['node']['file']['object']['id']
            text_gql_qr = text_gql_qry.replace( '$file_node_id', file_node_id )
            file_text_resp = r.post( 'https://api.github.com/graphql', json={'query': text_gql_qr }, headers=auth_param_construct )
            file_text_arr = json.loads(file_text_resp.text)['data']['node']['text'].split('\n')
            typo_text = edit['src']['text']
            line_number = file_text_arr.index( typo_text ) + 1
            blame_data = commit_blame_qr['data']['node']['blame']['ranges']
            for i in blame_data:
                if line_number >= i['startingLine'] and line_number <= i['endingLine']:
                    #print([ i['commit']['id'], i['age'], i['commit']['message'], '' if not i['commit']['author']['user'] else i['commit']['author']['user']['login'] , i['commit']['author']['name'], i['commit']['author']['email'] ])
                    csv_writer.writerow([ i['commit']['id'], i['age'], i['commit']['message'], '' if not i['commit']['author']['user'] else i['commit']['author']['user']['login'] , i['commit']['author']['name'], i['commit']['author']['email'] ])
                    break
    except Exception as e:
        print(f'[^] **ALERT** --> {count} is being skipped cause the following issue')
        print(e)
        print(f'And this is the response recieved for the first REST API query')
        try:
            print(r.get( f'https://api.github.com/repos/{owner}/{repo}/commits/{curr_data["commit"]}', headers=auth_param_construct ).text)
        except Exception as e:
            print('Ah whatever even that request did not succeed at all')
            bonk_file.write(f'{count}')

    #print(json.dumps(blame_data, indent=4))