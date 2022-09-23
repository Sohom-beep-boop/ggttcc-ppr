import pandas as pd
import json

data = pd.read_csv('commit_data.csv')
#data.drop_duplicates(inplace=True)
user_data = data[['user']].drop_duplicates()
#print(data)
print(len(user_data))
print(pd.isnull(user_data).sum())
print(user_data)
dirty_username_list = user_data.values.tolist()
username_list = []
for user in dirty_username_list:
    username_list.append( user[0] )
with open('users.json', 'w+') as f:
    f.write(json.dumps(username_list))
