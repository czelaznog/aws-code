# aws-code/lake-formation 

General utility scripts for Lake Formation Administrators. With the script you can scan, grant or revoke lake formation permission. Filter by multiple criteria (resource type, database name, table name, principal arn, permission action) is supported. Python 3.7+ required.

## 1. lakeformation.py

Script to scan, grant or revoke lake formation permissions.

### - usage

python lakeformation -a action -r resource_type [-p PRINCIPAL] [-d DATABASE] [-t TABLE] [-s PERMISSION]

### - options


- **-a ACTION**, specifies the action to perform in lake formation, valid values are **scan**, **grant** or **revoke**.
- **-r RESOURCE**, specifies the resource type. It will grant, revoke or scan permissions for this resource type. Valid values are **table**, **database** or **data_location** 
- **-p PRINCIPAL**, grant, revoke or filter by the princpal ARN. You must specify the complete AWS ARN in the option.
- **-d DATABASE**, grant, revoke or filter by the databases name. For **scan** you can also add a regular expression in the parameter and it will be evaluated during the filter.
- **-d TABLE**, grant, revoke or filter by the table name. For **scan** you can also add a regular expression in the parameter and it will be evaluated during the filter.
- **-s PERMISSION**, grant, revoke or filter by the permission name. 
- **-c CATALOG**, filter by a specific data catalog. Default is the callers role account catalog. 

### - examples


- Scan all the table permissions in the data catalog

    python lakeformation.py -a scan -r table

- Scan all the database permissions in the data catalog

    python lakeformation.py -a scan -r database

- Scan all the database permissions in the data catalog for a specific principal

    python lakeformation.py -a scan -r database -p principal_arn

- Scan all the database permissions in the data catalog for a specific principal and a specific database

    python lakeformation.py -a scan -r database -p principal_arn -d database_name

- Scan all the table permissions of type SELECT

    python lakeformation.py -a scan -r table -s SELECT

- Scan permissions for ALL_TABLES for a specific principal
    
    python lakeformation.py -a scan -r table -t ALL_TABLES -p arn:aws:iam::12345678910:role/PrincipalName

- Grant permissions to a specific principal and specific table in default database

    python lakeformation.py -a grant -r table -d default -t TableName -p arn:aws:iam::12345678910:role/PrincipalName -s SELECT

- Grant permissions to a specific principal to AL_TABLES in default database (must use ALL_TABLES for table name)

    python lakeformation.py -a grant -r table -d default -t ALL_TABLES -p arn:aws:iam::12345678910:role/PrincipalName -s SELECT

- Revoke permissions from a specific principal from AL_TABLES in default database (must use ALL_TABLES for table name)

    python lakeformation.py -a revoke -r table -d default -t ALL_TABLES -p arn:aws:iam::12345678910:role/PrincipalName -s SELECT