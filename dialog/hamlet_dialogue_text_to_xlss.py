import pandas as pd
import argparse
import sys
from tqdm import tqdm

# TO RUN:
# python hamlet_dialogue_text_to_xlss.py hamlet_dialogue.txt play_dialogue_hamlet.xlsx

def parse_dialogue(file_path):
    """
    Parse the dialogue from the input text file.
    
    Args:
    file_path (str): Path to the input text file.
    
    Returns:
    list: A list of tuples containing (character, dialogue).
    """
    data = []
    current_character = None

    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()
            
        for line in tqdm(lines, desc="Parsing dialogue"):
            line = line.strip()
            if not line:
                continue
            
            if ': ' in line:
                parts = line.split(': ', 1)
                if len(parts) == 2:
                    current_character, dialogue = parts
                    data.append((current_character, dialogue))
                else:
                    data.append((current_character, line))
            elif current_character:
                data.append((current_character, line))
            else:
                print(f"Warning: Skipping line without character: {line}")
    
    except IOError as e:
        print(f"Error reading file: {e}", file=sys.stderr)
        sys.exit(1)
    
    return data

def save_to_excel(data, output_path):
    """
    Save the parsed dialogue data to an Excel file.
    
    Args:
    data (list): A list of tuples containing (character, dialogue).
    output_path (str): Path to the output Excel file.
    """
    df = pd.DataFrame(data, columns=['Character', 'Dialogue'])
    
    try:
        df.to_excel(output_path, index=False)
        print(f"Excel file saved successfully as '{output_path}'")
    except IOError as e:
        print(f"Error writing Excel file: {e}", file=sys.stderr)
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="Convert Hamlet dialogue text to Excel.")
    parser.add_argument("input_file", help="Path to the input text file")
    parser.add_argument("output_file", help="Path to the output Excel file")
    args = parser.parse_args()

    dialogue_data = parse_dialogue(args.input_file)
    save_to_excel(dialogue_data, args.output_file)

if __name__ == "__main__":
    main()