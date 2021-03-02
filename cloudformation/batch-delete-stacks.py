import argparse
import boto3
import json
import multiprocessing
import ast
import sys
import pprint


# Starts Multipart Upload
def start_upload(bucket, key):
    s3_client = boto3.client('s3')

    response = s3_client.create_multipart_upload(
        Bucket = bucket,
        Key = key
    )

    return response['UploadId']

# Add upload part
def add_part(proc_queue, body, bucket, key, part_number, upload_id):
    s3_client = boto3.client('s3')

    response = s3_client.upload_part(
        Body = body,
        Bucket = bucket,
        Key = key,
        PartNumber = part_number,
        UploadId = upload_id
    )

    print(f"Finished Part: {part_number}, ETag: {response['ETag']}")
    proc_queue.put({'PartNumber': part_number, 'ETag': response['ETag']})
    return

# End Multipart Upload
def end_upload(bucket, key, upload_id, finished_parts):
    s3_client = boto3.client('s3')

    response = s3_client.complete_multipart_upload(
        Bucket = bucket,
        Key = key,
        MultipartUpload={
            'Parts': finished_parts
        },
        UploadId = upload_id
    )

    return response

def get_stack_names(stack_filter):
    cfn_client = boto3.client(
        'cloudformation',
        region_name = 'us-east-2'
    )
    response = cfn_client.list_stacks(
      StackStatusFilter = stack_filter
    )
    return response['StackSummaries']

def delete_stack(stack_name, stack_region):
    cfn_client = boto3.client(
        'cloudformation',
        region_name = stack_region
    )
    response = cfn_client.delete_stack(
        StackName=stack_name,
    )
    return response

# Primary logic
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('-f', '--filter', help = "Filter condition for listing stacks")
    ap.add_argument('-k', '--key', help = "Key for destination object")
    ap.add_argument('-p', '--processes', type = int, choices = range(1,256), metavar = '[1-256]', default = 10, help = "Number of upload processes to run simultaneously")
    args = vars(ap.parse_args())
    
    stack_filter = []
    if args['filter'] in [None, '']:
        stack_filter = []
    else:
        stack_filter = ast.literal_eval(args['filter'])

    stacks = get_stack_names(stack_filter)
    for s in stacks:   

        stack_name = s['StackName']
        print(f"Sent for deletion: {stack_name}")
        response = delete_stack(stack_name, "us-east-2")
        pprint.pprint(response)
        print("")
        
    

if __name__ == '__main__':
    main()
