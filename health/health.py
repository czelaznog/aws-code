import boto3

client = boto3.client('health')

response = client.enable_health_service_access_for_organization()

print(response)