import boto3

s3 = boto3.resource('s3')
bucket = s3.Bucket('cgg.datalake.raw')
bucket.object_versions.all().delete()