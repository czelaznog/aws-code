import requests
import boto3
import uuid
import time
import random
import json

client = boto3.client('kinesis', region_name='us-east-1')
partition_key = str(uuid.uuid4())

number_of_results = 500
r = requests.get('https://randomuser.me/api/?exc=login&results=' + str(number_of_results))
data = r.json()["results"]

while True:
        # The following chooses a random user from the 500 random users pulled from the API in a single API call.
        random_user_index = int(random.uniform(0, (number_of_results - 1)))
        random_user = data[random_user_index]
        random_user = json.dumps(data[random_user_index])
        client.put_record(
                StreamName='my-data-stream',
                Data=random_user,
                PartitionKey=partition_key)
        time.sleep(random.uniform(0, 1))