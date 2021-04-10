## you can add custom mysql driver and make a connection as below link
## https://docs.aws.amazon.com/glue/latest/dg/aws-glue-programming-etl-connect.html#aws-glue-programming-etl-connect-jdbc#
# Before you run glue job, you first make a new glue connection for mysql with subnet, sg where mysql located and attache glue connection(you created) to glue job as below. (edited) 
# IMPORTANT
#Important : you mail fail connetion test in glue connection(you created). Because it use mysql driver 5.1. You shoud ignore the connection fail. Just add glue connection to glue job which let glue job node start in subnet which located in mysql database.
# you can use the attached mysql-jdbc driver for mysql 5.7 and above(mysql 8)
import sys
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.dynamicframe import DynamicFrame
from awsglue.job import Job
args = getResolvedOptions(sys.argv, ['JOB_NAME'])
sparkContext = SparkContext()
glueContext = GlueContext(sparkContext)
sparkSession = glueContext.spark_session
##Use the CData JDBC driver to read MySQL data from the Orders table into a DataFrame
connection_mysql5_7_options = {
    "url": "jdbc:mysql://xxxxxx.ap-northeast-2.rds.amazonaws.com:3306/public",
    "dbtable": "test",
    "user": "admin",
    "password": "xxxxx",
    "customJdbcDriverS3Path": "s3://your_path/mysql-connector-java-8.0.21.jar",
    "customJdbcDriverClassName": "com.mysql.cj.jdbc.Driver"
    }
df_mysql5_7 = glueContext.create_dynamic_frame.from_options(connection_type="mysql",
                                                          connection_options=connection_mysql5_7_options)
df_mysql5_7.show()
