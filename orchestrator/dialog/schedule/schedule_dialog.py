import pandas as pd
import random
import argparse

def assign_random_values(file_path):
    """
    Reads an Excel file, assigns random numbers, IMAs, and wait times to each dialogue line.

    Args:
        file_path (str): Path to the Excel file.

    Returns:
        pandas.DataFrame: DataFrame with added 'Number', 'IMA', and 'Wait Time' columns.
    """
    df = pd.read_excel(file_path)
    df['Number'] = [random.randint(1, 3) for _ in range(len(df))]
    df['IMA'] = [random.choice(['discord', 'messenger', 'signal', 'skype', 'slack', 'teams', 'telegram', 'whatsapp']) for _ in range(len(df))]
    df['Wait Time (seconds)'] = [random.randint(0, 60) for _ in range(len(df))]
    return df

def export_to_excel(df, output_file_path):
    """
    Exports the DataFrame to an Excel file.

    Args:
        df (pandas.DataFrame): The DataFrame to export.
        output_file_path (str): The path where the Excel file will be saved.
    """
    df.to_excel(output_file_path, index=False)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Process Excel files and assign random values.')
    parser.add_argument('-i', '--input_file', 
                        type=str, 
                        default='play_dialogue_hamlet.xlsx',
                        help='Path to the input Excel file (default: input.xlsx)')
    parser.add_argument('-o', '--output_file', 
                        type=str, 
                        default='play_dialogue_hamlet_scheduled.xlsx',
                        help='Path to the output Excel file (default: output.xlsx)')

    args = parser.parse_args()

    input_file = "in/" + args.input_file
    output_file = "out/" + args.output_file

    df = assign_random_values(input_file)
    export_to_excel(df, output_file)
    print(f"Data has been exported to {args.output_file}")
