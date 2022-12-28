OVERVIEW-

In this project, I have assumed that the csv files would come daily and I have implemented the incremental load of csv files, loading of these source files into fact and dimension tables.

Assumptions-
1. assumed that the source files arrive at source folder daily in csv format. 
2. The target in the architecture designed is data warehouse. so, the output data is stored in facts and dimension tables.
But for illustration purpose I am storing the facts and dimensions in the fact and dim folders in csv format.
3. The complete end-to-end pipeline implementation is not done, as feature extraction from the message_content is done using NLTK, AI/ML models.
4. For Illsutration, I have chosen a dimension traders with schema (trader_id,trader_name,end_time_ms) and a fact with schema (message_id, message_timestamp, message_content, reply_message_id, trader_id, chat_link, processing_time)

Steps Involved in the process-

1. A unix find command is run using subprocess to find the files received on the run day of script. 
2. These source files, traders dimension are read using spark and stored in a dataframe.
3. All the distinct traders which are present in the source and not present in traders dimension are fetched into dataframe.
4. To the distinct traders dataframe, the columns(tarder_id, end_time_ms) are added. trader_id is the current epoch time, it indicates that the column in validFrom that time. end_to_ms is validTo, for now it is being loaded as 0.
5. The transformed distinct traders data is then persisted into the traders dimension.
6. Now, the updated traders dimension data is read and joined with source data. The trader_id is updated in the source data, required columns are fetched and persisted into fact.

