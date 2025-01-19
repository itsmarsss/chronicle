import json
import os
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

# Get project root directory
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Load the results data
with open(os.path.join(PROJECT_ROOT, 'out', 'results.json'), 'r') as infile:
    results = json.load(infile)

# Initialize the Sentence-BERT model for name vectorization
model = SentenceTransformer('paraphrase-MiniLM-L6-v2')

# Helper function to convert names into vectors
def get_name_vector(name):
    return model.encode([name])[0]  # Return the vector for the name

# Helper function to calculate cosine similarity between two vectors
def cosine_sim(v1, v2):
    return cosine_similarity([v1], [v2])[0][0]

# Helper function to find the most specific name in a group
def find_most_specific_name(names):
    return max(names, key=lambda name: (len(name.split()), len(name)))  # Prefer longer names

# Adjusted function to group similar character names
def group_similar_characters(characters_dict, similarity_threshold=0.9):
    grouped_characters = []
    character_ids = list(characters_dict.keys())
    total_ids = len(character_ids)
    
    print(f"Starting to group {total_ids} characters...")
    
    name_vectors = {id: get_name_vector(characters_dict[id]["name"]) for id in character_ids}
    visited = set()
    
    for i, id1 in enumerate(character_ids):
        if id1 in visited:
            continue  # Skip if already grouped
        
        name1 = characters_dict[id1]["name"]
        group = [id1]
        vector1 = name_vectors[id1]
        visited.add(id1)
        
        for j in range(i + 1, len(character_ids)):
            id2 = character_ids[j]
            if id2 in visited:
                continue  # Skip if already grouped
            
            name2 = characters_dict[id2]["name"]
            
            # Skip if one name is a substring of the other
            if name1 in name2 or name2 in name1:
                continue  # Do not group
            
            vector2 = name_vectors[id2]
            similarity = cosine_sim(vector1, vector2)
            
            if similarity >= similarity_threshold:
                print(f"    Names '{name1}' and '{name2}' are similar (similarity: {similarity:.2f}). Grouping them.")
                group.append(id2)
                visited.add(id2)
        
        grouped_characters.append(group)
        print(f"  Group for '{name1}': {group}")
    
    print("Finished grouping characters.")
    return grouped_characters

# Group similar character names
print("Starting character refinement...")
grouped_characters = group_similar_characters(results["characters"])

# Create a mapping from original IDs to a canonical name
name_mapping = {}
for group in grouped_characters:
    # Find the most specific name in the group
    canonical_id = max(group, key=lambda id: (len(results["characters"][id]["name"].split()), len(results["characters"][id]["name"])))
    canonical_name = results["characters"][canonical_id]["name"]
    print(f"  Group for '{canonical_name}': {group}")
    
    for char_id in group:
        name_mapping[char_id] = canonical_id

print("Created name mapping for canonical names.")

# Merge contexts for similar characters
refined_characters = {}
for group in grouped_characters:
    canonical_id = max(group, key=lambda id: (len(results["characters"][id]["name"].split()), len(results["characters"][id]["name"])))
    canonical_name = results["characters"][canonical_id]["name"]
    merged_contexts = []
    
    for char_id in group:
        if char_id in results["characters"]:
            merged_contexts.extend(results["characters"][char_id]["contexts"])
    
    # Remove duplicate contexts
    merged_contexts = list(set(merged_contexts))
    
    # Add the canonical character to the refined characters dictionary
    refined_characters[canonical_id] = {
        "id": canonical_id,
        "name": canonical_name,
        "contexts": merged_contexts
    }

print("Merged contexts for similar characters.")

# Filter out characters with fewer than 5 contexts
filtered_characters = {
    char_id: char_data
    for char_id, char_data in refined_characters.items()
    if len(char_data["contexts"]) >= 5
}

print(f"Filtered out characters with fewer than 5 contexts. Remaining characters: {len(filtered_characters)}")

# Update contexts to reflect the filtered characters
filtered_contexts = {}
for context_id, context_data in results["contexts"].items():
    filtered_characters_list = [
        char_name
        for char_name in context_data["characters"]
        if any(
            char_name == char_data["name"]
            for char_data in filtered_characters.values()
        )
    ]
    
    # Remove duplicate characters
    filtered_characters_list = list(set(filtered_characters_list))
    
    filtered_contexts[context_id] = {
        "id": context_data["id"],
        "chunk_num": context_data["chunk_num"],
        "page_nums": context_data["page_nums"],
        "text": context_data["text"],
        "characters": filtered_characters_list,
        "important": context_data["important"]
    }

print("Updated contexts to reflect filtered characters.")

# Combine the filtered results
filtered_results = {
    "characters": filtered_characters,
    "contexts": filtered_contexts
}

# Ensure out directory exists
out_dir = os.path.join(PROJECT_ROOT, 'out')
os.makedirs(out_dir, exist_ok=True)

# Save the filtered results to a new JSON file
with open(os.path.join(out_dir, 'filtered_results.json'), 'w') as outfile:
    json.dump(filtered_results, outfile, indent=4)

print(f"Filtered results saved to 'filtered_results.json'.")
