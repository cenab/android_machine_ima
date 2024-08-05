import pandas as pd

text_file_path = 'hamlet_dialogue.txt'  

with open(text_file_path, 'r') as file:
    lines = file.readlines()

data = []

for line in lines:
    line = line.strip()  
    if line:  
        parts = line.split('. ', 1)
        if len(parts) == 2:
            character, dialogue = parts
        else:
            character, dialogue = data[-1][0], line  
        data.append([character, dialogue])

df = pd.DataFrame(data, columns=['Character', 'Dialogue'])

excel_file_path = 'play_dialogue_hamlet.xlsx'

df.to_excel(excel_file_path, index=False)

print(f"Text file has been converted to Excel and saved as '{excel_file_path}'")
