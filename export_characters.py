import json
from groq import Groq
from dotenv import load_dotenv
import os
import time

load_dotenv()

cumulative_characters = []
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# Load chunks data
with open('chunks.json', 'r') as infile:
    chunks = json.load(infile)

# Process each chunk
for idx, chunk in enumerate(chunks):
    text = chunk['text']
    # Craft the prompt to ensure no comments in the JSON response
    prompt = (
        f"Extract the characters mentioned in the text and reply with a valid JSON list "
        f"of their names, like [\"Character1\", \"Character2\"]. Ensure that the response "
        f"is valid JSON and does not include any comments or explanations. Text: {text}"
    )

    retries = 5
    for attempt in range(retries):
        try:
            # Send request to Groq API
            completion = client.chat.completions.create(
                model="llama-3.1-8b-instant",
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
                        cumulative_characters.extend(characters)
                        print(f"Processed chunk {idx + 1}/{len(chunks)}")
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

# Remove duplicates
cumulative_characters = list(set(cumulative_characters))

# Fine-tune the character list by removing irrelevant or incomplete characters
refine_prompt = (
    "Given the following list of character names, remove any duplicates or irrelevant obviously "
    "non-character name entries. Additionally, ensure that only the actual character names are included, "
    "and remove any nicknames, titles, or alternative references (e.g., 'You-Know-Who' should be replaced with 'Voldemort'). "
    "Ensure that the response is valid JSON and does not include any comments or explanations. "
    "Reply with a valid JSON list of their names, like [\"Character1\", \"Character2\"]. "
    "List: " + json.dumps(cumulative_characters)
)


# Retry logic for refining the character list
retries = 5
for attempt in range(retries):
    try:
        # Send request to Groq API to refine the character list
        refine_completion = client.chat.completions.create(
            model="llama-3.1-70b-versatile",
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
                    cumulative_characters = refined_characters
                    print("Character list refined successfully.")
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
with open('characters.json', 'w') as outfile:
    json.dump(cumulative_characters, outfile, indent=4)
