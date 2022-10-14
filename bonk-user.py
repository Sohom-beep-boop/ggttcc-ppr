import json
import requests
from datetime import datetime

import time

from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

import csv

csv_file = open( 'user_data.csv', 'a')
csv_writer = csv.writer(csv_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)

api = 'https://api.github.com'
api_gql = 'https://api.github.com/graphql'

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

all_users = []
with open('./users.json') as f:
    all_users = json.load(f)

user = all_users[0]
# put token here
patty = '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'

auth_param_construct = { 'Authorization': f'Bearer {patty}' }

total_gql_query = ''
with open('./totals.gql') as total_gql_file:
    total_gql_query = total_gql_file.read()

year_gql_query = ''
with open('./totals.gql') as year_gql_file:
    year_gql_query = year_gql_file.read()

langs_gql_query = ''
with open('./langs.gql') as langs_gql_file:
    langs_gql_query = langs_gql_file.read()

i = 1

start_at = int(input('What ID user did ya last fetch ? '))
flag = True
for user in all_users:
    try:
        if ( i == start_at ):
            flag = False
        elif flag:
            i+=1
            continue
        resp = requests.get( api + '/users/' + user , headers=auth_param_construct  )
        resp_data = json.loads( resp.text )
        #print(json.dumps(resp_data, indent=2))
        #print('Username --> ', resp_data['login'])
        #print('Name -->', resp_data['name'])
        #print('Company --> ', resp_data['company'])
        #print('Location  --> ', resp_data['location'])
        date = datetime.strptime(resp_data['created_at'], "%Y-%m-%dT%H:%M:%SZ")
        #print('Time of stay --> ', (date.now() - date).total_seconds())
        print(f'[-] Downloading data for user number {i} ' + resp_data['login'])
        total_gql_qr = total_gql_query.replace( '$user', user )
        resp = requests.post(api_gql, json={ 'query': total_gql_qr }, headers=auth_param_construct)
        #print(resp.headers)
        #print(resp)
        #print(resp.text)
        user_data = json.loads(resp.text)
        user_data = user_data['data']['user']['contributionsCollection']
        #print(json.dumps(resp_data, indent=2))
        #print(api + '/search/commits?q=author:' + user)
        resp = requests.get(api + '/search/commits?q=author:' + user, headers=auth_param_construct)
        resp_data_total_count = json.loads(resp.text)
        csv_writer.writerow( [resp_data['login'], resp_data['name'], resp_data['company'], resp_data['location'], (date.now() - date).total_seconds(), user_data['totalIssueContributions'], user_data['totalCommitContributions'], user_data['totalRepositoryContributions'], user_data['totalPullRequestContributions'], user_data['totalPullRequestReviewContributions'], user_data['totalRepositoriesWithContributedIssues'], user_data['totalRepositoriesWithContributedCommits'], user_data['totalRepositoriesWithContributedPullRequests'], user_data['totalRepositoriesWithContributedPullRequestReviews'], resp_data_total_count['total_count'] ] )
        #time.sleep(20)
    except Exception as e:
        print(f'[-] Could not downloading data for user number {i} ' + resp_data['login'])
        print(e)
    #print(resp_data['total_count'])
    """
    resp = r.post(api_gql, json={ 'query': langs_gql_query, 'variables': { 'login': user } }, headers=auth_param_construct)
    resp_data = json.loads(resp.text)
    print(resp_data)
    """
    i+=1

