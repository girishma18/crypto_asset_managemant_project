
def csv_writer(dataframe, target_path, mode, header):
    dataframe.write \
    .mode(mode) \
    .csv(target_path, header=header)