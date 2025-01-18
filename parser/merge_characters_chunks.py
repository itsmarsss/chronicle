import json
import os

# Get project root directory
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
temp_dir = os.path.join(PROJECT_ROOT, 'temp')

# Load the characters JSON
with open(os.path.join(temp_dir, 'characters.json'), 'r') as characters_file:
    characters_data = json.load(characters_file)

# Load the chunks JSON
with open(os.path.join(temp_dir, 'chunks.json'), 'r') as chunks_file:
    chunks_data = json.load(chunks_file)

# Create a dictionary to map chunk_num to characters
characters_dict = {item['chunk_num']: item['characters'] for item in characters_data}

# Merge the data
merged_data = []
for chunk in chunks_data:
    chunk_num = chunk['chunk_num']
    if chunk_num in characters_dict:
        merged_data.append({
            "chunk_num": chunk_num,
            "page_nums": chunk['page_nums'],
            "text": chunk['text'],
            "characters": characters_dict[chunk_num]
        })
    else:
        # If no characters are found for this chunk, include it without characters
        merged_data.append({
            "chunk_num": chunk_num,
            "page_nums": chunk['page_nums'],
            "text": chunk['text'],
            "characters": []  # Empty list for characters
        })

# Save the merged data to a new JSON file
with open(os.path.join(temp_dir, 'merged_chunks.json'), 'w') as outfile:
    json.dump(merged_data, outfile, indent=4)

print("Merged data saved to 'merged_chunks.json'.")
