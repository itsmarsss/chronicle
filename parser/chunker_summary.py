import json
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from openai import OpenAI
from dotenv import load_dotenv

# Get project root directory
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Configuration parameters
chunk_size_words = 500  # Number of words per chunk
overlap_size_words = 100  # Number of words overlapping between chunks

# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = OpenAI(
    api_key=os.getenv("API_KEY"),
    base_url="https://api.deepseek.com"
)

# Load data from transcript.json
temp_dir = os.path.join(PROJECT_ROOT, 'temp')
os.makedirs(temp_dir, exist_ok=True)

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

print("Creating chunks...")
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

# Function to generate a 1-sentence summary for a chunk
def generate_chunk_summary(chunk):
    prompt = (
        f"Below is a chunk of text from a document. Write a concise 1-sentence summary of the key points.\n\n"
        f"Text:\n{chunk['text']}\n\n"
        f"Summary:"
    )

    retries = 3
    for attempt in range(retries):
        try:
            # Send request to Deepseek API
            print(f"Generating summary for chunk {chunk['chunk_num']} (attempt {attempt + 1}/{retries})...")
            completion = client.chat.completions.create(
                model="deepseek-chat",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,  # Lower temperature for more focused responses
                max_completion_tokens=1024,
                top_p=0.9,  # Slightly lower top_p to reduce randomness
                stream=False,
                stop=None,
            )

            # Extract the generated text from the response
            generated_text = completion.choices[0].message.content
            print(f"Summary generated for chunk {chunk['chunk_num']}.")
            return chunk['chunk_num'], generated_text.strip()
        except Exception as err:
            print(f"An error occurred on attempt {attempt + 1}/{retries} for chunk {chunk['chunk_num']}: {err}")
            if attempt < retries - 1:
                time.sleep(2)  # Wait for 2 seconds before retrying
            else:
                print(f"Failed to generate summary for chunk {chunk['chunk_num']} after {retries} attempts.")
                return chunk['chunk_num'], "No summary available."

# Process chunks in parallel with a maximum of 10 threads
print("Generating summaries for chunks...")
with ThreadPoolExecutor(max_workers=10) as executor:
    # Submit tasks for each chunk
    future_to_chunk = {
        executor.submit(generate_chunk_summary, chunk): chunk['chunk_num']
        for chunk in chunks
    }

    # Process results as they are completed
    for future in as_completed(future_to_chunk):
        chunk_num = future_to_chunk[future]
        try:
            chunk_num, summary = future.result()
            # Add the summary to the corresponding chunk
            for chunk in chunks:
                if chunk['chunk_num'] == chunk_num:
                    chunk['summary'] = summary
                    break
            print(f"Finished processing chunk {chunk_num}.")
        except Exception as err:
            print(f"An error occurred while processing chunk {chunk_num}: {err}")

# Save chunks to chunks.json
with open(os.path.join(temp_dir, 'chunks.json'), 'w') as outfile:
    json.dump(chunks, outfile, indent=4)

print("Chunks saved to 'chunks.json'.")