import argparse
import boto3
import json
import multiprocessing
import ast
import sys
import pprint
import time
import botostubs


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

def get_principal_database_permissions( *, Principal = None, CatalogId = None, DatabaseName = None,  separator = " " ):

    client = boto3.client('lakeformation')
    ResourceType = 'DATABASE'

    Resource = {
        'Database': {
            'CatalogId': CatalogId,
            'Name': DatabaseName
        }
    }

    r = client.list_permissions(
        CatalogId=CatalogId, 
        Principal=Principal, 
        ResourceType=ResourceType,
        Resource=Resource
    )
    permission_list = r['PrincipalResourcePermissions']
    principal_arn = Principal['DataLakePrincipalIdentifier']
    result = []

    # Iterator over permission list of a specific Principal and a Resource of type database.
    for p in permission_list:
        resource_permission_list = p['Permissions']
        permission_string = ""
        #Iterate over the database permission actions
        for rp in resource_permission_list:
            permission_string = CatalogId + separator + principal_arn + \
                separator + DatabaseName + separator + rp
            result.append(permission_string)

    
    return result

def get_principal_table_permissions( *, Principal = None, CatalogId = None, DatabaseName = None, TableName = None, separator = " " ):

    client = boto3.client('lakeformation')
    ResourceType = 'TABLE'
    ResourceTable={
        'Table': {
            'CatalogId': CatalogId,
            'DatabaseName': DatabaseName,
            'Name': TableName
        }
    }
    
    r = client.list_permissions(
        CatalogId=CatalogId, 
        Principal=Principal, 
        ResourceType=ResourceType,
        Resource=ResourceTable
    )
    permission_list = r['PrincipalResourcePermissions']
    principal_arn = Principal['DataLakePrincipalIdentifier']
    result = []

    # Iterator over permission list of a specific Principal and a Resource of type table.
    for p in permission_list:
        resource_permission_list = p['Permissions']
        permission_string = ""
        #Iterate over the table permission actions
        for rp in resource_permission_list:
            permission_string = CatalogId + separator + principal_arn + \
                separator + DatabaseName + separator + TableName + separator + rp
            result.append(permission_string)

    
    return result

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

def get_table_names(*, DatabaseName=None):
    client = boto3.client('glue')
    result = []
    table_list = client.get_tables(DatabaseName=DatabaseName)
    for t in table_list['TableList']:
        result.append(t['Name'])
    return result
        

def get_database_names():
    client = boto3.client('glue')
    result = []
    response = client.get_databases()
    for d in response['DatabaseList']:
        result.append(d['Name'])
    return result

def main1():
    lf = boto3.client('lakeformation')
    glue = boto3.client('glue')
    CatalogId='821879089030'

    ResourceType='DATABASE'
    ResourceCatalog={
        'Catalog': {}
    }
    ResourceDatabase={
        'Database': {
            'CatalogId': '821879089030',
            'Name': 'arcosdorados_datalake_core_flexcash_db'
        }
    }
    ResourceDataLocation={
        'DataLocation': {
            'CatalogId': '821879089030',
            'ResourceArn': 'arn:aws:s3:::arcosdorados-datalake-dev-us-east-1-821879089030-stage'
        }
    }
    ResourceTable={
        'Table': {
            'CatalogId': '821879089030',
            'DatabaseName': 'arcosdorados_datalake_core_flexcash_db',
            'Name': 'tb_register_pre_stage'
            #'TableWildcard': {}
        }
    }


    res = lf.list_permissions(CatalogId=CatalogId, ResourceType=ResourceType, Resource=ResourceDatabase)

    database_name = 'arcosdorados_datalake_core_flexcash_db'
    catalog_id = '821879089030'
    pid = 1
    for p in res['PrincipalResourcePermissions']:
        #print(p['Principal'])
        #print(p['Resource'])
        #print(p['Permissions'])
        principal = {
            'DataLakePrincipalIdentifier': p['Principal']['DataLakePrincipalIdentifier']
        }
        table_list = glue.get_tables(DatabaseName=database_name)

        all_principal_table_permissions = []
        for t in table_list['TableList']:
            table_name = t['Name']
            all_principal_table_permissions.extend(get_principal_table_permissions(
                CatalogId=catalog_id, 
                Principal=principal,   
                DatabaseName=database_name,
                TableName=table_name            
            ))
            
        
        for p in all_principal_table_permissions:
            print(str(pid) + " " + p)
            pid+=1



if __name__ == '__main__':

    # databases = get_database_names()
    # for db in databases:
    #     tables = get_table_names(DatabaseName=db)
    #     for table in tables:
    #         print(db + " " + table)

    lf = boto3.client('lakeformation')
    # glue = boto3.client('glue')
    s3client = boto3.client('s3')  # type: botostubs.S3
    client = boto3.client('s3')  # type: botostubs.S3
    
    
    
    
    
    
    
    
    

    
    



    CatalogId='821879089030'

    ResourceType='DATABASE'
    ResourceCatalog={
        'Catalog': {}
    }
    ResourceDatabase={
        'Database': {
            'CatalogId': '821879089030',
            'Name': 'arcosdorados_datalake_core_flexcash_db'
        }
    }
    ResourceDataLocation={
        'DataLocation': {
            'CatalogId': '821879089030',
            'ResourceArn': 'arn:aws:s3:::arcosdorados-datalake-dev-us-east-1-821879089030-stage'
        }
    }
    ResourceTable={
        'Table': {
            'CatalogId': '821879089030',
            'DatabaseName': 'arcosdorados_datalake_core_flexcash_db',
            'Name': 'tb_register_pre_stage'
            #'TableWildcard': {}
        }
    }



    res = lf.list_permissions(CatalogId=CatalogId,Resource=ResourceTable,ResourceType="TABLE")
    fetch = True
    
    permissions = res['PrincipalResourcePermissions']
    for permission in permissions:
        for p in permission['Permissions']:
            print(permission['Principal']['DataLakePrincipalIdentifier'] + " " + str(permission['Resource']) + " " + p)



    while fetch:

        try:

            token = res['NextToken']
            res = lf.list_permissions(CatalogId=CatalogId,Resource=ResourceTable, ResourceType="TABLE", NextToken=token)
            permissions = res['PrincipalResourcePermissions']
            for permission in permissions:
                for p in permission['Permissions']:
                    print(permission['Principal']['DataLakePrincipalIdentifier'] + " " + str(permission['Resource']) + " " + p)

        except:
            print("done")
            fetch = False

    



        
    


            
            
