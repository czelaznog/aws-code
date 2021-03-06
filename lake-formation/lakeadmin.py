import argparse
import boto3
import json
import multiprocessing
import ast
import sys
import pprint
import time
import botostubs
import getopt
import awswrangler as wr
import pandas as pd
import re
from tabulate import tabulate

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

def get_db_permissions_df( DataFrameColumns=list, PrincipalDatabasePermissions=list):

    df = pd.DataFrame(columns=DataFrameColumns)
    for p in PrincipalDatabasePermissions:
        for rp in p['Permissions']:
            df_row = []
            df_row.append(p['Principal']['DataLakePrincipalIdentifier'])
            df_row.append(p['Resource']['Database']['CatalogId'])
            df_row.append('database')
            df_row.append(p['Resource']['Database']['Name'])
            df_row.append(rp)
            df = df.append(pd.DataFrame([df_row], columns=DataFrameColumns), ignore_index=False )

    return df


def get_table_permissions_df( table, DataFrameColumns=list, PrincipalDatabasePermissions=list, table_expression=str):

    df = pd.DataFrame(columns=DataFrameColumns)
    for p in PrincipalDatabasePermissions:
        for rp in p['Permissions']:
            lakeformation_table = ""
            df_row = []
            df_row.append(p['Principal']['DataLakePrincipalIdentifier'])
            try: 
                df_row.append(p['Resource']['Table']['CatalogId'])
                df_row.append('table')
                df_row.append(p['Resource']['Table']['DatabaseName'])
                df_row.append(p['Resource']['Table']['Name'])
                lakeformation_table = p['Resource']['Table']['Name']
                df_row.append('false')
            except:
                df_row.append(p['Resource']['TableWithColumns']['CatalogId'])
                df_row.append('table')
                df_row.append(p['Resource']['TableWithColumns']['DatabaseName'])
                df_row.append(p['Resource']['TableWithColumns']['Name'])
                lakeformation_table = p['Resource']['TableWithColumns']['Name']
                df_row.append('true')               
            df_row.append(rp)
            if table_name_validation(lakeformation_table, table_expression):
                df = df.append(pd.DataFrame([df_row], columns=DataFrameColumns), ignore_index=False )

    df.drop_duplicates(inplace=True, ignore_index=True)
    return df

def get_table_principal_permissions( *, CatalogId = None, DatabaseName = None, TableName = None, Principal = None):
    
    Resource = {
        'Table': {
            'CatalogId': CatalogId,
            'DatabaseName': DatabaseName,
            'Name': TableName
        }
    }

    client = boto3.client('lakeformation') # type: botostubs.LakeFormation
    principal_permissions = []
    if Principal is None:
        result = client.list_permissions( CatalogId=CatalogId, Resource=Resource)
    else: 
        result = client.list_permissions( CatalogId=CatalogId, Resource=Resource, Principal=Principal)

    principal_permissions = result['PrincipalResourcePermissions']
    fetch = True

    while fetch:
        try:
            token = result['NextToken']
            if Principal is None:
                result = client.list_permissions( CatalogId=CatalogId, Resource=Resource, NextToken=token)
            else: 
                result = client.list_permissions( CatalogId=CatalogId, Resource=Resource, Principal=Principal, NextToken=token)
            
            principal_permissions.extend(result['PrincipalResourcePermissions'])
        except:
            fetch = False

    return principal_permissions

def get_database_principal_permissions( *, CatalogId = None, DatabaseName = None, Principal = None):

    Resource = {
        'Database': {
            'CatalogId': CatalogId,
            'Name': DatabaseName
        }
    }

    client = boto3.client('lakeformation') # type: botostubs.LakeFormation
    principal_permissions = []
    if Principal is None:
        result = client.list_permissions( CatalogId=CatalogId, Resource=Resource)
    else: 
        result = client.list_permissions( CatalogId=CatalogId, Resource=Resource, Principal=Principal)

    principal_permissions = result['PrincipalResourcePermissions']
    fetch = True

    while fetch:
        try:
            token = result['NextToken']
            if Principal is None:
                result = client.list_permissions( CatalogId=CatalogId, Resource=Resource, NextToken=token)
            else: 
                result = client.list_permissions( CatalogId=CatalogId, Resource=Resource, Principal=Principal, NextToken=token)
            principal_permissions.extend(result['PrincipalResourcePermissions'])
        except:
            fetch = False

    return principal_permissions

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
    ap.add_argument('-c', '--catalog', help = "Filter by catalog name")
    ap.add_argument('-d', '--database', help = "Filter database by regex pattern")
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


def database_name_validation( database_name, expression ):
    regex = re.compile(expression)
    return regex.match(database_name)

def table_name_validation( table_name, expression ):
    regex = re.compile(expression)
    return regex.match(table_name)

def show_table_permissions( catalog_id, database_expression, table_expression, principal):

    if principal is not None:
        principal_dict = { 'DataLakePrincipalIdentifier': principal }
    else:
        principal_dict = None

    #expression = "^((?!dev).)*stld.*$"
    df_columns = ['principal', 'catalog_id', 'resource', 'database_name', 'table_name', 'table_with_columns', 'permission']
    databases = get_database_names()
    fdf = pd.DataFrame(columns=df_columns)
    skip = False
    for db in databases:
        if database_name_validation( db, database_expression ):            
            tables = get_table_names(DatabaseName=db)
            if table_expression == 'ALL_TABLES':
                skip = True
            for table in tables:
                if table_name_validation(table, table_expression) or skip:
                    table_principal_permissions = get_table_principal_permissions( CatalogId=catalog_id, DatabaseName=db, TableName=table, Principal=principal_dict)
                    df = get_table_permissions_df(table, df_columns, table_principal_permissions, table_expression)
                    fdf = fdf.append(df, ignore_index=True)

    fdf.reset_index(drop=True, inplace=True)
    fdf.drop_duplicates(inplace=True, ignore_index=False)
    print(tabulate(fdf, showindex=True, headers=fdf.columns, tablefmt='psql'))

def show_database_permissions( catalog_id, database_expression, principal):

    if principal is not None:
        principal_dict = { 'DataLakePrincipalIdentifier': principal }
    else:
        principal_dict = None

    #expression = "^((?!dev).)*stld.*$"
    db_df_columns = ['principal', 'catalog_id', 'resource', 'database_name', 'permission']
    databases = get_database_names()
    db_df = pd.DataFrame(columns=db_df_columns)
    for db in databases:
        if database_name_validation( db, database_expression ):
            db_principal_permissions = get_database_principal_permissions( CatalogId=catalog_id, DatabaseName=db, Principal=principal_dict)
            df = get_db_permissions_df( db_df_columns, db_principal_permissions)
            db_df = db_df.append(df, ignore_index=True)

    print(tabulate(db_df, showindex=True, headers=db_df.columns, tablefmt='psql'))

if __name__ == '__main__':

    ap = argparse.ArgumentParser()
    ap.add_argument('-r', '--resource', choices = ['table', 'database'],  required = True,  help = "Filter by resource type")
    ap.add_argument('-p', '--principal', help = "Filter by principal ARN")
    ap.add_argument('-c', '--catalog', help = "Filter by catalog name")
    ap.add_argument('-d', '--database', help = "Filter database name by regex pattern")
    ap.add_argument('-t', '--table', help = "Filter glue table name by regex pattern")
    
    args = vars(ap.parse_args())

    
    if args['database'] in [None, '']:
        args['database'] = "."

    if args['table'] in [None, '']:
        args['table'] = "."

    if args['catalog'] in [None, '']:
        args['catalog'] = boto3.client('sts').get_caller_identity().get('Account')

    if args['principal'] in [None, '']:
        args['principal'] = None

    catalog_id = args['catalog']
    database_expression = args['database']
    table_expression = args['table']
    resource_type = args['resource'] 
    principal = args['principal']


    if resource_type == 'database':
        show_database_permissions( catalog_id, database_expression, principal )
    elif resource_type == 'table':
        show_table_permissions( catalog_id, database_expression, table_expression, principal )