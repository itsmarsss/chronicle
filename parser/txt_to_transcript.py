import json
import os

# Get project root directory
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

text_data = []
# Read the input file
with open(PROJECT_ROOT + '/temp/input.txt', 'r') as file:
    text = file.read()

    # Split text into words
    words = text.split()

    # Initialize variables
    current_page = 0
    words_per_page = 500

    # Process text in chunks of 500 words
    for i in range(0, len(words), words_per_page):
        # Get chunk of words
        chunk = words[i:i + words_per_page]
        
        # Create text entry
        text_data_entry = {
            'page_num': current_page,
            'text': ' '.join(chunk)
        }
        text_data.append(text_data_entry)
        current_page += 1

print(json.dumps(text_data, indent=4))

# Ensure temp directory exists
temp_dir = os.path.join(PROJECT_ROOT, 'temp')
os.makedirs(temp_dir, exist_ok=True)

# Write to transcript.json
with open(os.path.join(temp_dir, 'transcript.json'), 'w') as outfile:
        json.dump(text_data, outfile, indent=4)

print(f"Transcript saved to 'transcript.json' in {temp_dir}")