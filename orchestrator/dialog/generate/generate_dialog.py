import pandas as pd
import argparse
import sys
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
        df_concat.to_excel(output_path, index=False)
        print(f"Excel file saved successfully as '{output_path}'")
    except IOError as e:
        print(f"Error writing Excel file: {e}", file=sys.stderr)
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="Convert Hamlet dialogue text to Excel.")
    parser.add_argument("input_file", help="Path to the input text file (e.g., in/hamlet_dialogue.txt)")
    parser.add_argument("output_file", help="Path to the output Excel file (e.g., out/play_dialogue_hamlet.xlsx)")
    args = parser.parse_args()

    input_file = "in/" + args.input_file
    output_file = "out/" + args.output_file

    dialogue_data = parse_dialogue(input_file)
    save_to_excel(dialogue_data, output_file)

if __name__ == "__main__":
    main()