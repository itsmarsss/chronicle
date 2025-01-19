import json
from openai import OpenAI
from dotenv import load_dotenv
import os
import time

# Get project root directory
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
temp_dir = os.path.join(PROJECT_ROOT, 'temp')

load_dotenv()

client = OpenAI(
    api_key=os.getenv("API_KEY"),
    base_url="https://api.deepseek.com"
)

# Load chunks data
with open(os.path.join(temp_dir, 'chunks.json'), 'r') as infile:
    chunks = json.load(infile)

# Create a summarized version of all chunks
summarized_chunks = []
for idx, chunk in enumerate(chunks):
    summarized_chunks.append({
        "chunk_num": idx + 1,
        "page_nums": chunk["page_nums"],
        "summary": f"Chunk {idx + 1} (Pages {chunk['page_nums']}): {chunk['text'][:200]}..."  # Truncate text for summary
    })

# Combine all summaries into a single prompt
summarized_text = "\n\n".join([chunk["summary"] for chunk in summarized_chunks])

# Craft a prompt to identify the top 5-10 important chunks
prompt = (
    f"Below is a summarized version of all chunks in a document. Each chunk is labeled with its number, page numbers, and a brief summary.\n\n"
    f"Summarized Chunks:\n{summarized_text}\n\n"
    f"Identify the **top 5-10 most important chunks** based on the following criteria:\n"
    f"- The chunk significantly advances the plot or changes the direction of the story.\n"
    f"- The chunk involves major decisions, conflicts, or resolutions by key characters.\n"
    f"- The chunk has a lasting impact on the narrative or characters.\n\n"
    f"Respond with a JSON object containing the key 'important_chunks', which is a list of chunk numbers (e.g., [1, 5, 7]). "
    f"Only include the most pivotal chunks. Do not include minor details or routine actions.\n\n"
    f"Important Chunks:"
)

# Retry mechanism
retries = 3
for attempt in range(retries):
    try:
        # Send request to Deepseek API
        completion = client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,  # Lower temperature for more focused responses
            max_completion_tokens=1024,
            top_p=0.9,  # Slightly lower top_p to reduce randomness
            stream=False,
            response_format={"type": "json_object"},
            stop=None,
        )

        # Extract the generated text from the response
        generated_text = completion.choices[0].message.content

        # Parse the JSON response
        try:
            response = json.loads(generated_text)
            if isinstance(response, dict) and "important_chunks" in response:
                important_chunks = response["important_chunks"]
                print(f"Identified important chunks: {important_chunks}")

                # Filter the original chunks to include only the important ones
                important_chunks_details = [chunk for chunk in chunks if chunk["chunk_num"] in important_chunks]

                # Save the important chunks to a JSON file
                with open(os.path.join(temp_dir, 'important_chunks.json'), 'w') as outfile:
                    json.dump(important_chunks_details, outfile, indent=4)

                print("Important chunks saved to 'important_chunks.json'.")
                break  # Exit the retry loop if successful
            else:
                print("Invalid response format. Expected 'important_chunks' key.")
        except json.JSONDecodeError as json_err:
            print(f"JSON decode error: {json_err}")
    except Exception as err:
        print(f"An error occurred on attempt {attempt + 1}/{retries}: {err}")
        if attempt < retries - 1:
            time.sleep(2)  # Wait for 2 seconds before retrying
        else:
            print("Failed after 3 attempts. Exiting.")