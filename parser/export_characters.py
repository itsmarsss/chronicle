import json
from openai import OpenAI
from dotenv import load_dotenv
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

# Get project root directory
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
temp_dir = os.path.join(PROJECT_ROOT, 'temp')
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

load_dotenv()

cumulative_characters = []
client = OpenAI(
    api_key=os.getenv("API_KEY"),
    base_url="https://api.deepseek.com"
)

# Load chunks data
with open(os.path.join(temp_dir, 'chunks.json'), 'r') as infile:
    chunks = json.load(infile)

# Function to process each chunk
def process_chunk(idx, chunk):
    text = chunk['text']
    # Craft the prompt to ensure no comments in the JSON response
    prompt = (
        f"Extract the names of characters mentioned in the text and resolve pronouns or relational terms "
        f"to identify the specific individuals they refer to (e.g., determine who 'he' or 'she' refers to, "
        f"and whose 'dad' or 'mom' is being mentioned) based on the context. Replace any occurrences of 'I' with 'Narrator' "
        f"when identifying characters. Reply with a valid JSON list of their names, such as "
        f"[\"Character1\", \"Character2\"]. Ensure that the response is valid JSON and contains no comments or explanations. "
        f"Text: {text}"
    )



    retries = 3
    for attempt in range(retries):
        try:
            # Send request to Groq API
            completion = client.chat.completions.create(
                model="deepseek-chat",  # llama-3.1-8b-instant
                messages=[{"role": "user", "content": prompt}],
                temperature=1,
                max_completion_tokens=1024,
                top_p=1,
                stream=False,
                response_format={"type": "json_object"},  # Corrected response format
                stop=None,
            )

            # Extract the generated text from the response
            generated_text = completion.choices[0].message.content

            # Find the JSON list within the response
            start = generated_text.find('[')
            end = generated_text.rfind(']')
            if start != -1 and end != -1 and end > start:
                json_str = generated_text[start:end+1]
                try:
                    characters = json.loads(json_str)
                    if isinstance(characters, list):
                        # Add the chunk number and characters to cumulative_characters
                        return {"chunk_num": idx+1, "characters": characters}
                    else:
                        print(f"Invalid response format for chunk {idx + 1}")
                except json.JSONDecodeError as json_err:
                    print(f"JSON decode error for chunk {idx + 1}: {json_err}")
            else:
                print(f"No JSON list found in response for chunk {idx + 1}")
            break  # Break out of the retry loop if successful
        except Exception as err:
            print(f"An error occurred for chunk {idx + 1}, attempt {attempt + 1}/{retries}: {err}")
            if attempt < retries - 1:
                time.sleep(2)  # Wait for 2 seconds before retrying
            else:
                print(f"Failed after {retries} attempts. Moving on to the next chunk.")
    return None  # Return None if all attempts fail

# Process chunks in parallel with a maximum of 10 threads
with ThreadPoolExecutor(max_workers=10) as executor:
    future_to_chunk = {executor.submit(process_chunk, idx, chunk): idx for idx, chunk in enumerate(chunks)}
    for future in as_completed(future_to_chunk):
        result = future.result()
        if result:
            cumulative_characters.append(result)
            print(f"Processed chunk {result['chunk_num']}/{len(chunks)}")

# Save the cumulative characters data to a JSON file
with open(os.path.join(temp_dir, 'cumulative_characters.json'), 'w') as outfile:
    json.dump(cumulative_characters, outfile, indent=4)

# Collect all unique character names across all chunks
all_characters = set()
for chunk in cumulative_characters:
    all_characters.update(chunk['characters'])

# Fine-tune the character list by standardizing names
refine_prompt = (
    "Given the following list of character names, standardize the names to ensure consistency. "
    "For example, if 'harry potter' and 'Harry Potter' appear, standardize them to 'Harry Potter'. "
    "If there are synonymous names (e.g., 'You-Know-Who' and 'Voldemort'), always keep the most descriptive and canonical name (e.g., 'Voldemort'). "
    "Remove any nicknames, titles, or alternative references that are less descriptive. "
    "Ensure that the response is **only** a valid JSON list of standardized character names, like [\"Character1\", \"Character2\"]. "
    "Do **not** include any additional comments, explanations, or metadata in the response. "
    "List: " + json.dumps(list(all_characters))
)

# Retry logic for refining the character list
retries = 3
for attempt in range(retries):
    try:
        # Send request to Groq API to refine the character list
        refine_completion = client.chat.completions.create(
            model="deepseek-chat",  # llama-3.1-70b-versatile
            messages=[{"role": "user", "content": refine_prompt}],
            temperature=0.7,
            max_completion_tokens=1024,
            top_p=1,
            stream=False,
            response_format={"type": "json_object"},  # Corrected response format
            stop=None,
        )

        # Extract the refined character list from the response
        refined_text = refine_completion.choices[0].message.content

        # Find the JSON list within the response
        start = refined_text.find('[')
        end = refined_text.rfind(']')
        if start != -1 and end != -1 and end > start:
            json_str = refined_text[start:end+1]
            try:
                refined_characters = json.loads(json_str)
                if isinstance(refined_characters, list):
                    # Create a mapping from original names to standardized names
                    name_mapping = {}
                    for original_name in all_characters:
                        for standardized_name in refined_characters:
                            if original_name.lower() == standardized_name.lower():
                                name_mapping[original_name] = standardized_name
                                break

                    # Update each chunk's character list with standardized names
                    for chunk in cumulative_characters:
                        chunk['characters'] = [name_mapping.get(name, name) for name in chunk['characters']]

                    print("Character names standardized successfully.")
                else:
                    print("Invalid response format for refined character list.")
            except json.JSONDecodeError as json_err:
                print(f"JSON decode error in refined list: {json_err}")
        else:
            print("No JSON list found in refined response.")
        break  # Break out of the retry loop if successful
    except Exception as err:
        print(f"An error occurred while refining the character list, attempt {attempt + 1}/{retries}: {err}")
        if attempt < retries - 1:
            time.sleep(2)  # Wait for 2 seconds before retrying
        else:
            print(f"Failed after {retries} attempts. Moving on.")

# Save the refined characters to a JSON file
with open(os.path.join(temp_dir, 'characters.json'), 'w') as outfile:
    json.dump(cumulative_characters, outfile, indent=4)
