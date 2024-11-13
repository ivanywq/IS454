import os
from datetime import datetime

import pandas as pd


def combine_csv_files(input_folder, output_folder):
    # Ensure the output folder exists
    os.makedirs(output_folder, exist_ok=True)

    # List to hold DataFrames for each CSV file
    dataframes = []

    # Loop through all CSV files in the specified folder
    for filename in os.listdir(input_folder):
        if filename.endswith(".csv"):
            file_path = os.path.join(input_folder, filename)
            print(f"Processing {file_path}...")
            try:
                # Read each CSV file into a DataFrame and append it to the list
                df = pd.read_csv(file_path)
                dataframes.append(df)
            except Exception as e:
                print(f"Error reading {file_path}: {e}")

    # Combine all DataFrames into a single DataFrame
    if dataframes:
        combined_df = pd.concat(dataframes, ignore_index=True)

        # Get the current time and format it for the output filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"combined_transformed_data_{timestamp}.csv"
        output_path = os.path.join(output_folder, output_filename)

        # Save the combined DataFrame as a CSV
        combined_df.to_csv(output_path, index=False)
        print(f"Combined data saved to {output_path}")

        return combined_df
    else:
        print("No CSV files found in the specified folder.")
        return None
