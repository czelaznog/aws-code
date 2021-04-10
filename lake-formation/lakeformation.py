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


def get_location_permissions_df( DataFrameColumns=list, PrincipalDatabasePermissions=list, resource_permission = str):

    df = pd.DataFrame(columns=DataFrameColumns)
    for p in PrincipalDatabasePermissions:
        for rp in p['Permissions']:
            df_row = []
            df_row.append(p['Principal']['DataLakePrincipalIdentifier'])
            df_row.append(p['Resource']['DataLocation']['CatalogId'])
            df_row.append('data_location')
            df_row.append(p['Resource']['DataLocation']['ResourceArn'])
            df_row.append(rp)
            df = df.append(pd.DataFrame([df_row], columns=DataFrameColumns), ignore_index=False )

    return df

def get_db_permissions_df( DataFrameColumns=list, PrincipalDatabasePermissions=list, resource_permission = str):

    df = pd.DataFrame(columns=DataFrameColumns)
    for p in PrincipalDatabasePermissions:
        for rp in p['Permissions']:
            df_row = []
            df_row.append(p['Principal']['DataLakePrincipalIdentifier'])
            df_row.append(p['Resource']['Database']['CatalogId'])
            df_row.append('database')
            df_row.append(p['Resource']['Database']['Name'])
            df_row.append(rp)
            if( resource_permission is None or resource_permission == rp ):
                df = df.append(pd.DataFrame([df_row], columns=DataFrameColumns), ignore_index=False )

    return df

def get_table_permissions_df( table, DataFrameColumns=list, PrincipalDatabasePermissions=list, table_expression=str, resource_permission = str):

    df = pd.DataFrame(columns=DataFrameColumns)
    for p in PrincipalDatabasePermissions:
        for rp in p['Permissions']:
            df_row = []
            df_row.append(p['Principal']['DataLakePrincipalIdentifier'])
            try: 
                df_row.append(p['Resource']['Table']['CatalogId'])
                df_row.append('table')
                df_row.append(p['Resource']['Table']['DatabaseName'])
                if( table == 'ALL_TABLES'): df_row.append(table)
                else: df_row.append(p['Resource']['Table']['Name'])
                df_row.append('false')
            except:
                df_row.append(p['Resource']['TableWithColumns']['CatalogId'])
                df_row.append('table')
                df_row.append(p['Resource']['TableWithColumns']['DatabaseName'])
                if( table == 'ALL_TABLES'): df_row.append(table)
                else: df_row.append(p['Resource']['TableWithColumns']['Name'])
                df_row.append('true')               
            df_row.append(rp)
            if( resource_permission is None or resource_permission == rp ):
                #if table_name_validation(lakeformation_table, table_expression):
                df = df.append(pd.DataFrame([df_row], columns=DataFrameColumns), ignore_index=False )

    df.drop_duplicates(inplace=True, ignore_index=True)
    return df

def get_location_principal_permissions( *, CatalogId = None, LocationArn=None, Principal = None):

    FullLocationArn = 'arn:aws:s3:::' + LocationArn
    #print(FullLocationArn)
    Resource = {
        'DataLocation': {
            'CatalogId': CatalogId,
            'ResourceArn': FullLocationArn
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

def get_table_principal_permissions( *, CatalogId = None, DatabaseName = None, TableName = None, Principal = None):
    
    if( TableName == 'ALL_TABLES'):
        Resource = {
            'Table': {
                'CatalogId': CatalogId,
                'DatabaseName': DatabaseName,
                'TableWildcard': {}
            }
        }
    else:
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

def show_table_permissions( catalog_id, database_expression, table_expression, principal, resource_permission):

    if principal is not None:
        principal_dict = { 'DataLakePrincipalIdentifier': principal }
    else:
        principal_dict = None

    #expression = "^((?!dev).)*stld.*$"
    df_columns = ['principal', 'catalog_id', 'resource', 'database_name', 'table_name', 'table_with_columns', 'permission']
    databases = get_database_names()
    fdf = pd.DataFrame(columns=df_columns)
    for db in databases:
        if database_name_validation( db, database_expression ):  
            if(table_expression == 'ALL_TABLES'):          
                table_principal_permissions = get_table_principal_permissions( CatalogId=catalog_id, DatabaseName=db, TableName=table_expression, Principal=principal_dict)
                df = get_table_permissions_df(table_expression, df_columns, table_principal_permissions, table_expression, resource_permission)
                fdf = fdf.append(df, ignore_index=True)
            else:
                tables = get_table_names(DatabaseName=db)
                for table in tables:
                    if table_name_validation(table, table_expression):
                            table_principal_permissions = get_table_principal_permissions( CatalogId=catalog_id, DatabaseName=db, TableName=table, Principal=principal_dict)
                            df = get_table_permissions_df(table, df_columns, table_principal_permissions, table_expression, resource_permission)
                            fdf = fdf.append(df, ignore_index=True)

    fdf.reset_index(drop=True, inplace=True)
    fdf.drop_duplicates(inplace=True, ignore_index=False)
    print(tabulate(fdf, showindex=True, headers=fdf.columns, tablefmt='psql'))

def show_database_permissions( catalog_id, database_expression, principal, resource_permission):

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
            df = get_db_permissions_df( db_df_columns, db_principal_permissions, resource_permission)
            db_df = db_df.append(df, ignore_index=True)

    print(tabulate(db_df, showindex=True, headers=db_df.columns, tablefmt='psql'))

def show_location_permissions( catalog_id, location_expression, principal, resource_permission):

    
    
    
    if principal is not None:
        principal_dict = { 'DataLakePrincipalIdentifier': principal }
    else:
        principal_dict = None

    
    db_df_columns = ['principal', 'resource', 'catalog_id',  'resource_arn', 'permission']
    client = boto3.client('s3') # type: botostubs.S3
    buckets = client.list_buckets()
    locations = buckets['Buckets']     
    db_df = pd.DataFrame(columns=db_df_columns)
    for location in locations:
        
        loc_principal_permissions = get_location_principal_permissions( CatalogId=catalog_id, LocationArn=location['Name'], Principal=principal_dict)
        df = get_location_permissions_df( db_df_columns, loc_principal_permissions, resource_permission)
        db_df = db_df.append(df, ignore_index=True)

    print(tabulate(db_df, showindex=True, headers=db_df.columns, tablefmt='psql'))

def grant_permission( *, ResourceType=None, CatalogId=None, DatabaseName=None, TableName=None, Principal=None, Permissions=[] ):

    client = boto3.client('lakeformation') # type: botostubs.LakeFormation
    PrincipalDict = {'DataLakePrincipalIdentifier': Principal }
    Resource = None
    if(ResourceType == 'database'):
        Resource = {
            'Database': {
                'CatalogId': CatalogId,
                'Name': DatabaseName,
            }
        }
    elif ResourceType == 'table' and TableName not in [None, '']:
        if( TableName == 'ALL_TABLES'):
            Resource = {
                'Table': {
                    'CatalogId': CatalogId,
                    'DatabaseName': DatabaseName,
                    'TableWildcard': {}
                }
            }
        else:
            Resource = {
                'Table': {
                    'CatalogId': CatalogId,
                    'DatabaseName': DatabaseName,
                    'Name': TableName
                }
            }
        
    try:
        client.grant_permissions( Principal=PrincipalDict, CatalogId=CatalogId, Resource=Resource, Permissions=Permissions)
    except Exception as e:
        print(e)

def revoke_permission( *, ResourceType=None, CatalogId=None, DatabaseName=None, TableName=None, Principal=None, Permissions=[] ):

    client = boto3.client('lakeformation') # type: botostubs.LakeFormation
    PrincipalDict = {'DataLakePrincipalIdentifier': Principal }
    Resource = None
    if ResourceType == 'database':
        Resource = {
            'Database': {
                'CatalogId': CatalogId,
                'Name': DatabaseName,
            }
        }
    elif ResourceType == 'table' and TableName not in [None, '']:
        if( TableName == 'ALL_TABLES'):
            Resource = {
                'Table': {
                    'CatalogId': CatalogId,
                    'DatabaseName': DatabaseName,
                    'TableWildcard': {}
                }
            }
        else:
            Resource = {
                'Table': {
                    'CatalogId': CatalogId,
                    'DatabaseName': DatabaseName,
                    'Name': TableName
                }
            }

    try:
        client.revoke_permissions( Principal=PrincipalDict, CatalogId=CatalogId, Resource=Resource, Permissions=Permissions)
    except Exception as e:
        print(e)

def main():

    ap = argparse.ArgumentParser()
    ap.add_argument('-a', '--action', choices = ['grant', 'revoke', 'scan'],  required = True,  help = "Define a script action")
    ap.add_argument('-r', '--resource', choices = ['table', 'database', 'data_location'], help = "Specify a resource")
    ap.add_argument('-p', '--principal', help = "Scan, revoke or grant by principal ARN")
    ap.add_argument('-c', '--catalog', help = "Scan, revoke or grant  by catalog name")
    ap.add_argument('-d', '--database', help = "Scan, revoke or grant  database name, can use regex in scan")
    ap.add_argument('-t', '--table', help = "Scan, revoke or grant by glue table name, can use regex in scan")
    ap.add_argument('-s', '--resource_permission', help = "Scan, revoke or grant by resource permission")
    
    args = vars(ap.parse_args())

    if args['action'] in ['scan'] and args['resource'] in [None, '']:
          raise SystemExit('Error. Scan action needs a resource type')

    if args['database'] in [None, '']:
        args['database'] = "."
    
    if args['resource_permission'] in [None, '']:
        args['resource_permission'] = None

    if args['table'] in [None, '']:
        args['table'] = "."

    if args['catalog'] in [None, '']:
        args['catalog'] = boto3.client('sts').get_caller_identity().get('Account')

    if args['principal'] in [None, '']:
        args['principal'] = None

    action = args['action'] 
    catalog_id = args['catalog']
    database_expression = args['database']
    table_expression = args['table']
    resource_type = args['resource'] 
    resource_permission = args['resource_permission']
    principal = args['principal']
    location_expression = "."

    if( action == 'scan'):
        if resource_type == 'database':
            show_database_permissions( catalog_id, database_expression, principal, resource_permission )
        elif resource_type == 'table':
            show_table_permissions( catalog_id, database_expression, table_expression, principal, resource_permission )
        elif resource_type == "data_location":
            show_location_permissions(catalog_id,location_expression,principal,"data_location_access")
    elif action == 'grant':
        print("Attempting Grant")
        grant_permission( 
            ResourceType = resource_type, 
            CatalogId=catalog_id,   
            DatabaseName = database_expression, 
            TableName=table_expression,
            Principal=principal,
            Permissions=[resource_permission] 
        )
    elif action == 'revoke':
        print("Attempting Revoke")
        revoke_permission( 
            ResourceType = resource_type, 
            CatalogId=catalog_id,   
            DatabaseName = database_expression, 
            TableName=table_expression,
            Principal=principal,
            Permissions=[resource_permission] 
        )

if __name__ == '__main__':

    main()

    