from pprint import pprint
import boto3

def put_control_item( key, business_date, restaurant, dynamodb=None):
    if not dynamodb:
        dynamodb = boto3.resource('dynamodb')

    table = dynamodb.Table('MainControl')
    response = table.put_item(
       Item={
            "business_date": business_date,
            "country": "AR",
            "dataset": "flexcash",
            "id": key,
            "lambda_memory_limit_in_mb": "2048",
            "last_procesed_sequence": 0,
            "pipeline": "np",
            "pipeline_stage": "StageB",
            "restaurant_id": restaurant,
            "retry_count": 4,
            "status": "failed",
            "team": "core"
        }
    )
    return response


if __name__ == '__main__':

    for m in range(1,4):
        for d in range(10,25):
            k = "XYZ"+str(m)+str(d)
            business_date = "2021-0"+str(m)+"-"+str(d)
            resp = put_control_item(k,business_date,k)
    print(resp)