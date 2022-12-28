import subprocess
import sys
import time
import reader as reader
import writer as writer
from pyspark.sql.functions import lit
from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StringType, IntegerType, StructField, TimestampType


# function to run a unix command
def run_cmd(args_list):
    proc = subprocess.Popen(' '.join(args_list), stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    s_output, s_err = proc.communicate()
    s_return = proc.returncode
    return s_return, s_output, s_err


#  function to retrieve today's csv source files
def get_todays_source_files():
    # running the below command to get the today's source files
    args = ["find", "\'../resources/source\'", "-mtime", "-1", "-type", "f", "-print"]
    ret, out, err = run_cmd(args)

    if ret==0:
        # today's fils
        todays_files = out.decode("utf-8").strip().split("\n")

        # filtering for csv files in today's files
        source_files_path = []
        for file in todays_files:
            if file[-4:] == ".csv":
                source_files_path.append(file)
        return source_files_path
    else:
        print(err)
        sys.exit()


if __name__ == '__main__':
    # creating spark session
    spark = SparkSession.builder.config("spark.conf.master", "Local[*]").appName("asset management app").getOrCreate()

    # getting today's csv source files
    source_files_path = get_todays_source_files()
    if len(source_files_path) == 0:
        sys.exit()
    print(source_files_path)

    # source schema
    source_schema = StructType([
        StructField("message_id", IntegerType(), True),
        StructField("message_timestamp", TimestampType(), True),
        StructField("message_content", StringType(), True),
        StructField("reply_message_id", IntegerType(), True),
        StructField("trader_id", StringType(), True),
        StructField("chat_link", IntegerType(), True),
        StructField("processing_time", TimestampType(), True)
    ])

    # traders dim schema
    traders_schema = StructType([
        StructField("trader_id", IntegerType(), True),
        StructField("trader_name", StringType(), True),
        StructField("end_date_ms", IntegerType(), True),
    ])

    # reading source data into a dataframe
    source_df = reader.csvs_reader(spark, source_files_path, source_schema)
    source_df.show()

    # reading traders dimension data into a dataframe
    traders_df = reader.csv_reader(spark, "../resources/dim/traders/*.csv",
                                   traders_schema)
    traders_df.show()

    # renaming trader_id column to trader_name and creating trader_id column with nulls
    source_df_stg = source_df.withColumnRenamed("trader_id", "trader_name").withColumn("trader_id",
                                                                                       lit(None).cast(IntegerType()))
    source_df_stg.show()

    # retrieving the distinct traders which are present in source but in traders dim
    if traders_df.count() != 0:

        distinct_traders = source_df_stg.join(traders_df, source_df_stg.trader_name == traders_df.trader_name, "left") \
            .filter(traders_df.trader_name.isNull()).select(source_df_stg.trader_name).distinct()
    else:
        distinct_traders = source_df_stg.select("trader_name").distinct()

    distinct_traders.show()

    # adding 2 more columns to distinct traders dataframe to persist into traders dimension
    # The 2 columns - trader_id(pk in fact table, fk in traders dim), this take the current epoch( indicating validFrom)
    # end_time_ms- indicates it's validTo or expiry date. Currently loading with 0
    traders_to_insert = distinct_traders.withColumn("trader_id", lit(int(time.time()))) \
        .withColumn("end_time_ms", lit(0))
    traders_to_insert.show()

    # writers the new traders information in the traders dim and reading the updated traders dimension data
    if traders_to_insert.count() != 0:

        # write the new traders details to the tarders dimension
        writer.csv_writer(traders_to_insert, "../resources/dim/traders/",
                          "append", 'true')

        # reading updated traders dimension data into a dataframe
        traders_df_updated = reader.csv_reader(spark,
                                               "../resources/dim/traders/*.csv",
                                               traders_schema)
        traders_df_updated.show()
    else:
        traders_df_updated = traders_df

    # update the trader_ids in the source dataframe
    source_df_stg_updated = source_df_stg.join(traders_df_updated,
                                               source_df_stg.trader_name == traders_df_updated.trader_name, "left") \
        .drop(source_df_stg.trader_id) \
        .drop(source_df_stg.trader_name) \
        .drop(traders_df_updated.trader_name) \
        .drop(traders_df_updated.end_time_ms)
    source_df_stg_updated.show()

    # source load to fact
    writer.csv_writer(source_df_stg_updated, "../resources/fact/", "append",
                      'false')
