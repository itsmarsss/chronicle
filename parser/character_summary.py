import json
from openai import OpenAI
from dotenv import load_dotenv
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

# Get project root directory
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
out_dir = os.path.join(PROJECT_ROOT, 'out')

load_dotenv()

client = OpenAI(
    api_key=os.getenv("API_KEY"),
    base_url="https://api.deepseek.com"
)

# Load filtered_results.json
print("Loading filtered_results.json...")
with open(os.path.join(out_dir, 'filtered_results.json'), 'r') as infile:
    filtered_results = json.load(infile)
print("filtered_results.json loaded successfully.")

# Extract characters and contexts
characters = filtered_results.get("characters", {})
contexts = filtered_results.get("contexts", {})
print(f"Found {len(characters)} characters and {len(contexts)} contexts.")

# Function to generate a character summary using Deepseek
def generate_character_summary(character_name, context_texts):
    combined_text = "\n".join(context_texts)
    prompt = (
        f"Below are excerpts from a story that mention the character '{character_name}'. "
        f"Write a short 1 sentence summary of the character based on these excerpts.\n\n"
        f"Excerpts:\n{combined_text}\n\n"
        f"Character Summary:"
    )

    retries = 3
    for attempt in range(retries):
        try:
            # Send request to Deepseek API
            print(f"Generating summary for '{character_name}' (attempt {attempt + 1}/{retries})...")
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
            print(f"Summary generated for '{character_name}'.")
            return generated_text.strip()
        except Exception as err:
            print(f"An error occurred on attempt {attempt + 1}/{retries} for character '{character_name}': {err}")
            if attempt < retries - 1:
                time.sleep(2)  # Wait for 2 seconds before retrying
            else:
                print(f"Failed to generate summary for character '{character_name}' after {retries} attempts.")
                return None

# Function to process a single character
def process_character(character_id, character_data):
    context_ids = character_data.get("contexts", [])
    context_texts = []

    # Gather all text from the character's contexts
    for context_id in context_ids:
        if context_id in contexts:
            context_texts.append(contexts[context_id]["text"])

    # Generate a summary for the character
    if context_texts:
        summary = generate_character_summary(character_data["name"], context_texts)
        if summary:
            character_data["summary"] = summary
        else:
            character_data["summary"] = "No summary available."
    else:
        character_data["summary"] = "No relevant contexts found."

    return character_id, character_data

# Process characters in parallel with a maximum of 10 threads
print("Processing characters...")
with ThreadPoolExecutor(max_workers=100) as executor:
    # Submit tasks for each character
    future_to_character = {
        executor.submit(process_character, character_id, character_data): character_id
        for character_id, character_data in characters.items()
    }

    # Process results as they are completed
    for future in as_completed(future_to_character):
        character_id = future_to_character[future]
        try:
            character_id, character_data = future.result()
            print(f"Finished processing character: {character_data['name']}.")
        except Exception as err:
            print(f"An error occurred while processing character {character_id}: {err}")

# Save the updated characters data to a new JSON file
with open(os.path.join(out_dir, 'output.json'), 'w') as outfile:
    json.dump({"characters": characters}, outfile, indent=4)

print("Character summaries saved to 'output.json'.")