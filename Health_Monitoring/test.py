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
message_types = ['srm', 'spat', 'ssm', 'bsm']

# Initialize a dictionary to store message counts per hour
message_counts_per_hour = {msg: [] for msg in message_types}

# Iterate over the message types and corresponding dataframes
for msg_type, df in zip(message_types, dataframes[1:]):  # Skip the first dataframe
    # Ensure the timestamp is in datetime format (if not already done)
    timestamp_col = df.columns[df.columns.str.contains('verbose')][0]  # Find the verbose timestamp column
    df[timestamp_col] = pd.to_datetime(df[timestamp_col])

    # Group by the hour and count the entries
    hourly_counts = df.resample('H', on=timestamp_col).size()
    message_counts_per_hour[msg_type] = hourly_counts

# Combine the dataframes for plotting
combined_df = pd.DataFrame(message_counts_per_hour)

# Plotting
combined_df.plot(kind='bar', width=0.8)
plt.title('Hourly Distribution of Messages')
plt.xlabel('Hour')
plt.ylabel('Number of Messages')
plt.xticks(rotation=45)
plt.legend(title='Message Type')
plt.tight_layout()
plt.show()
print('yes')