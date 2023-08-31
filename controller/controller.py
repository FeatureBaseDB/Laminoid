from google.auth import compute_engine
from googleapiclient import discovery

# get the token from gcp tag on instance
import httplib2
http = httplib2.Http()
url = 'http://metadata.google.internal/computeMetadata/v1/instance/tags'
headers = {'Metadata-Flavor': 'Google'}
response, content = http.request(url, 'GET', headers=headers)
evalcontent = eval(content)
print(evalcontent)
for item in evalcontent:
        if 'token' in item:
            key,token = item.split('-')


credentials = compute_engine.Credentials()
compute = discovery.build('compute', 'v1', credentials=credentials)

print(compute)

result = compute.instances().list(project="sloth-compute", zone="us-central1-a").execute()
print(result)