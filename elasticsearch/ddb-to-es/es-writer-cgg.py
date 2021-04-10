import boto3
import requests
from requests_aws4auth import AWS4Auth



region = 'us-east-1' # e.g. us-east-1
service = 'es'
credentials = boto3.Session().get_credentials()
awsauth = AWS4Auth(credentials.access_key, credentials.secret_key, region, service, session_token=credentials.token)

host = 'vpc-healthevents-12cd1b220bcb-hthtzfkufqm6qmpgmboffwwum4.us-east-1.es.amazonaws.com' # the Amazon ES domain, with https://

#index = 'lambda-index'
index = 'my-index'
type = '_doc'
url = host + '/' + index + '/' + type + '/'
# + '/' 

payload = {
    "settings" : {
        "number_of_shards" : 7,
        "number_of_replicas" : 2
    }
}

headers = { "Content-Type": "application/json" }

def lambda_handler(event, context):
    
    print(host)
    try:
        r = requests.get(host, auth=awsauth, headers=headers)
        print(r)
    except Exception as e:
        print(e)
    
    print(awsauth)
    print(credentials.access_key)
    print(credentials.secret_key)
    print(credentials.token)
    count = 0
    print(event)
    try:
        for record in event['Records']:
            # Get the primary key for use as the Elasticsearch ID
            id = record['dynamodb']['Keys']['id']['S']
            print("tHe id obtained")
            print(id)
            if record['eventName'] == 'REMOVE':
                r = requests.delete(url + id, auth=awsauth)
            else:
                try:
                    print("trying to send request")
                    print("URL: "+ url + id)
                    document = record['dynamodb']['NewImage']
                    print(document)
                    #r = requests.put(url, auth=awsauth, json=document, headers=headers)
                    r = requests.put(url+id, auth=awsauth, json=document, headers=headers)
                    #r = requests.put(url, auth=awsauth, json=payload)
                    print(r.text)
                    print(r.content)
                    print(r)
                    print("request sent")
                except Exception as e:
                    print(e)
            count += 1
            print(str(count) + ' records processed.')
        print("done")
    except Exception as e:
        print("error: ")
        print(e)
        return "processed with errors"
    return str(count) + ' records processed.'