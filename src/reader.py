
# function to read multiple csv files
def csvs_reader(spark, files_paths, schema):
    return spark.read \
        .option("schema", schema) \
        .option("header", True) \
        .option("multiLine", True) \
        .option("quote", "\"") \
        .option("escape", "\"") \
        .csv(files_paths, sep=",")


# function to read a single csv
def csv_reader(spark, file_path, schema):
    return spark.read.format("csv") \
        .option("schema", schema) \
        .option("header", True) \
        .option("multiLine", True) \
        .option("quote", "\"") \
        .option("escape", "\"") \
        .option("path", file_path) \
        .load()
