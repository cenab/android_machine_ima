import pandas as pd
import argparse
import sys
import os
from tqdm import tqdm

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
    current_dialogue = []

    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()

        for line in tqdm(lines, desc="Parsing dialogue"):
            line = line.strip()
            if not line:
                continue

            # Check if the line is a character name followed by dialogue
            if line.endswith('.') and line.split('.')[0].isalpha():  # Character name
                if current_character is not None:
                    # Save the previous character's dialogue before switching
                    data.append((current_character, ' '.join(current_dialogue).strip()))

                current_character = line.split('.')[0]  # Extract character name
                current_dialogue = [line.split('.', 1)[1].strip()]  # Start new dialogue
                continue

            # Skip lines that are stage directions
            if line.startswith('[') and line.endswith(']'):
                continue  # Skip stage directions

            # If the line is valid dialogue, append it to the current dialogue
            current_dialogue.append(line)  # Append dialogue without character name

        # Append the last character's dialogue after finishing the loop
        if current_character is not None:
            data.append((current_character, ' '.join(current_dialogue).strip()))
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
    df_concat = pd.concat([df] * 40, ignore_index=True)  # Simplified concatenation
    
    try:
        # Create the directory if it doesn't exist
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        df_concat.to_excel(output_path, index=False)
        print(f"Excel file saved successfully as '{output_path}'")
    except IOError as e:
        print(f"Error writing Excel file: {e}", file=sys.stderr)
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="Convert Hamlet dialogue text to Excel.")
    parser.add_argument("input_file", nargs="?", default="hamlet_dialogue.txt",
                        help="Path to the input text file (default: hamlet_dialogue.txt)")
    parser.add_argument("output_file", nargs="?", default="play_dialogue_hamlet.xlsx",
                        help="Path to the output Excel file (default: play_dialogue_hamlet.xlsx)")
    parser.add_argument("-i", "--input_file", dest="input_file_opt",
                        help="Path to the input text file (optional flag)")
    parser.add_argument("-o", "--output_file", dest="output_file_opt",
                        help="Path to the output Excel file (optional flag)")
    args = parser.parse_args()

    input_file = args.input_file_opt or args.input_file
    output_file = args.output_file_opt or args.output_file

    dialogue_data = parse_dialogue(input_file)
    save_to_excel(dialogue_data, output_file)
    
    # Save to schedule/in directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    schedule_in_dir = os.path.join(script_dir, "..", "schedule", "in")
    output_file_in_schedule = os.path.join(schedule_in_dir, os.path.basename(output_file))
    save_to_excel(dialogue_data, output_file_in_schedule)

if __name__ == "__main__":
    main()