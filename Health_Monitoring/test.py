import pandas as pd
import os
import json
import matplotlib.pyplot as plt



# Load the configuration file
with open('mmitss-monitor-rsu-config.json', 'r') as file:
    config = json.load(file)

log_directory = config['LogDirectory']
time_index = config['TimeIndex']
plot_directory = config['PlotDirectory']

# Define the possible timestamp columns
timestamp_columns = ['log_timestamp_verbose', 'log_timestamp_posix', 'timestamp_verbose', 'timestamp_posix']

def load_and_sort_csv(file_path):
    # Read the CSV file
    df = pd.read_csv(file_path)

    # Find the timestamp column that exists in this DataFrame
    for timestamp in timestamp_columns:
        if timestamp in df.columns:
            # Convert timestamp to datetime if it's in a verbose format
            if 'verbose' in timestamp:
                df[timestamp] = pd.to_datetime(df[timestamp])
            # Sort the DataFrame based on the timestamp
            df = df.sort_values(by=timestamp)
            break

    return df

# Find all files in the log directory that include the time index
file_paths = [os.path.join(log_directory, f) for f in os.listdir(log_directory) if time_index in f]

# Load and sort each file
dataframes = [load_and_sort_csv(path) for path in file_paths]

# Now you have a list of DataFrames, sorted by their respective timestamp columns
print('yes')

# The list of message types corresponding to the dataframes from index 1 to 4
message_types = ['ssm', 'bsm', 'srm']  # 'spat' is removed

# Initialize a dictionary to store message counts per 10 minutes
message_counts_per_10min = {msg: [] for msg in message_types}

# Iterate over the message types and corresponding dataframes
for msg_type, df in zip(message_types, [dataframes[2], dataframes[3], dataframes[4]]):
    # Find the verbose timestamp column and convert to datetime if necessary
    timestamp_col = df.columns[df.columns.str.contains('verbose')][0]
    df[timestamp_col] = pd.to_datetime(df[timestamp_col])

    # Set the datetime column as the DataFrame index
    df.set_index(timestamp_col, inplace=True)

    # Ensure the index is now a DatetimeIndex
    if not isinstance(df.index, pd.DatetimeIndex):
        df.index = pd.to_datetime(df.index)

    # Group by 10-minute intervals and count the entries
    ten_minute_counts = df.resample('H').size()
    message_counts_per_10min[msg_type] = ten_minute_counts

# Combine the dataframes for plotting
combined_df = pd.DataFrame(message_counts_per_10min)

# Plotting
combined_df.plot(kind='bar', width=0.8)
plt.title('10-Minute Distribution of Messages (Excluding SPAT)')
plt.xlabel('Time (10-minute intervals)')
plt.ylabel('Number of Messages')
plt.xticks(rotation=45)
plt.legend(title='Message Type')
plt.tight_layout()
plt.show()