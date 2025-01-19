import json
import os
import sys

def convert_text_to_transcript(input_file):
    # Get project root directory
    PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # Read the input file
    try:
        with open(input_file, 'r') as file:
            text = file.read()
    except FileNotFoundError:
        print(f"Error: File '{input_file}' not found")
        sys.exit(1)
    except Exception as e:
        print(f"Error reading file: {str(e)}")
        sys.exit(1)

    # Split text into words
    words = text.split()
    
    # Initialize variables
    text_data = []
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

    # Ensure temp directory exists
    temp_dir = os.path.join(PROJECT_ROOT, 'temp')
    os.makedirs(temp_dir, exist_ok=True)

    # Write to transcript.json
    try:
        with open(os.path.join(temp_dir, 'transcript.json'), 'w') as outfile:
            json.dump(text_data, outfile, indent=4)
        print(f"Successfully created transcript.json in {temp_dir}")
    except Exception as e:
        print(f"Error writing transcript.json: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python txt_to_transcript.py <input_text_file>")
        sys.exit(1)
    
    input_file = sys.argv[1]
    convert_text_to_transcript(input_file)
