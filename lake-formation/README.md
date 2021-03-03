# aws-code/lake-formation 

General utility scripts for Lake Formation Administrators. With the script you can scan lake formation permissions, filter by multiple criteria (resource type, database name, table name, principal arn, permission action). Additionally you can grant or revoke permissions. Python 3.7+ required.

## 1. lake-scan

Script to scan lake formationn permissions.

### - usage

python lake-scan -r resource_type [-p PRINCIPAL] [-d DATABASE] [-t TABLE] [-s PERMISSION]

### - options

- **-p PRINCIPAL**, filters the results by the princpal ARN. You must specify the complete AWS ARN in the option.
- **-d DATABASE**, filter the results by databases names. You can also add a regular expression in the parameter and it will be evaluated during the filter.
- **-d TABLE**, filter the results by table names. You can also add a regular expression in the parameter and it will be evaluated during the filter.
- **-d PERMISSION**, filter the results by specific permission action name. Check that the permission specified is a valid permission for the specified resource type. 
- **-c CATALOG**, filter by a specific data catalog. Default is the callers role account catalog. 

### - examples

- List all the table permissions in the data catalog

    python lake-scan.py -r table

- List all the database permissions in the data catalog

    python lake-scan.py -r database

- List all the database permissions in the data catalog for a specific principal

    python lake-scan.py -r database -p principal_arn

- List all the database permissions in the data catalog for a specific principal and a specific database

    python lake-scan.py -r database -p principal_arn -d database_name

- List all the table permissions of type SELECT

    python lake-scan.py -r table -s SELECT
