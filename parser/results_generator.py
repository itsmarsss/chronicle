import json
import uuid
import os

# Get project root directory
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Load the merged chunks data
out_dir = os.path.join(PROJECT_ROOT, 'temp')
with open(os.path.join(out_dir, 'merged_chunks.json'), 'r') as infile:
    merged_data = json.load(infile)

# Initialize dictionaries for characters and contexts
characters_dict = {}
contexts_dict = {}

# Helper function to generate a unique ID
def generate_uid():
    return str(uuid.uuid4())

# Process each chunk to build the characters and contexts dictionaries
for chunk in merged_data:
    # Generate a unique ID for the context
    context_id = generate_uid()
    
    # Add the context to the contexts dictionary
    contexts_dict[context_id] = {
        "id": context_id,
        "chunk_num": chunk["chunk_num"],
        "page_nums": chunk["page_nums"],
        "text": chunk["text"],
        "characters": chunk["characters"],
        "important": chunk["important"]
    }
    
    # Process each character in the chunk
    for character_name in chunk["characters"]:
        # Check if the character already exists in the characters dictionary
        character_found = None
        for uid, character_data in characters_dict.items():
            if character_data["name"] == character_name:
                character_found = uid
                break
        
        # If the character doesn't exist, create a new entry
        if not character_found:
            character_id = generate_uid()
            characters_dict[character_id] = {
                "id": character_id,
                "name": character_name,
                "contexts": [context_id]  # Add the current context ID
            }
        else:
            # If the character exists, add the current context ID to their contexts list
            characters_dict[character_found]["contexts"].append(context_id)

# Sort characters by the number of contexts they appear in (descending order)
sorted_characters = sorted(
    characters_dict.items(),
    key=lambda item: len(item[1]["contexts"]),
    reverse=True
)

# Convert the sorted list back into a dictionary
sorted_characters_dict = {item[0]: item[1] for item in sorted_characters}

# Combine the results into the final structure
results = {
    "characters": sorted_characters_dict,
    "contexts": contexts_dict
}

# Ensure out directory exists
out_dir = os.path.join(PROJECT_ROOT, 'out')
os.makedirs(out_dir, exist_ok=True)

# Save the results to a new JSON file
with open(os.path.join(out_dir, 'results.json'), 'w') as outfile:
    json.dump(results, outfile, indent=4)

print("Results saved to 'results.json'.")
