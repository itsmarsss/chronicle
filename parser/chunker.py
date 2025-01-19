import json
import os

# Get project root directory
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Configuration parameters
chunk_size_words = 500  # Number of words per chunk
overlap_size_words = 100  # Number of words overlapping between chunks

# Load data from transcript.json
temp_dir = os.path.join(PROJECT_ROOT, 'temp')
with open(os.path.join(temp_dir, 'transcript.json'), 'r') as infile:
    data = json.load(infile)

# Collect words and their corresponding page numbers
words = []
page_nums = []
for page in data:
    text = page['text']
    page_words = text.split()
    words.extend(page_words)
    page_num = page['page_num'] + 1  # Assuming page_num starts at 0
    page_nums.extend([page_num] * len(page_words))

# Create chunks of words with specified overlap
chunks = []
start_index = 0
total_words = len(words)

while start_index < total_words:
    end_index = start_index + chunk_size_words
    if end_index > total_words:
        end_index = total_words
    chunk_words = words[start_index:end_index]
    chunk_text = ' '.join(chunk_words)
    chunk_page_nums = sorted(list(set(page_nums[start_index:end_index])))
    chunks.append({
        'chunk_num': len(chunks) + 1,
        'page_nums': chunk_page_nums,
        'text': chunk_text
    })
    start_index += chunk_size_words - overlap_size_words

# Save chunks to chunks.json
with open(os.path.join(temp_dir, 'chunks.json'), 'w') as outfile:
    json.dump(chunks, outfile, indent=4)

print("Chunks saved to 'chunks.json'.")
