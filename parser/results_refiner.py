import json
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

# Load the results data
with open('results.json', 'r') as infile:
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

# List of generic words to ignore
GENERIC_WORDS = {"he", "she", "they", "it", "him", "her", "them", "I", "you", "we", "Mr.", "Mrs.", "Dr.", "Prof."}

# Helper function to check if a name is generic
def is_generic_name(name):
    return name.lower() in GENERIC_WORDS

# Adjusted function to group similar character names
def group_similar_characters(characters_dict, similarity_threshold=0.8):
    grouped_characters = []
    character_ids = list(characters_dict.keys())  # Work with IDs
    total_ids = len(character_ids)
    
    print(f"Starting to group {total_ids} characters...")
    
    # Precompute the vectors for all names
    name_vectors = {id: get_name_vector(characters_dict[id]["name"]) for id in character_ids}
    
    visited = set()
    
    for i, id1 in enumerate(character_ids):
        if id1 in visited:
            continue  # Skip if already grouped
        
        name1 = characters_dict[id1]["name"]
        if is_generic_name(name1) or len(name1) < 3:  # Ignore generic or too-short names
            continue
        
        group = [id1]
        vector1 = name_vectors[id1]
        visited.add(id1)
        
        for j in range(i + 1, len(character_ids)):
            id2 = character_ids[j]
            if id2 in visited:
                continue  # Skip if already grouped
            
            name2 = characters_dict[id2]["name"]
            if is_generic_name(name2) or len(name2) < 3:  # Ignore generic or too-short names
                continue
            
            vector2 = name_vectors[id2]
            
            # Calculate similarity between the two name vectors
            similarity = cosine_sim(vector1, vector2)
            
            # Substring matching heuristic
            is_substring_match = name1 in name2 or name2 in name1
            
            # Group if similarity is high or there's a valid substring match
            if similarity >= similarity_threshold or is_substring_match:
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

# Update contexts to reflect the refined character names
refined_contexts = {}
total_contexts = len(results["contexts"])
print(f"Updating {total_contexts} contexts...")

for idx, (context_id, context_data) in enumerate(results["contexts"].items()):
    refined_characters_list = []
    for character_name in context_data["characters"]:
        # Map the character name to its canonical ID, if available
        for char_id, char_data in results["characters"].items():
            if char_data["name"] == character_name and char_id in name_mapping:
                refined_characters_list.append(results["characters"][name_mapping[char_id]]["name"])
                break
        else:
            refined_characters_list.append(character_name)
    
    # Remove duplicate characters
    refined_characters_list = list(set(refined_characters_list))
    
    refined_contexts[context_id] = {
        "id": context_data["id"],
        "chunk_num": context_data["chunk_num"],
        "page_nums": context_data["page_nums"],
        "text": context_data["text"],
        "characters": refined_characters_list
    }
    
    print(f"  Updated context {idx + 1}/{total_contexts}:")
    print(f"    Chunk Num: {context_data['chunk_num']}")
    print(f"    Characters: {refined_characters_list}")

print("Finished updating contexts.")

# Combine the refined results
refined_results = {
    "characters": refined_characters,
    "contexts": refined_contexts
}

# Save the refined results to a new JSON file
with open('refined_results.json', 'w') as outfile:
    json.dump(refined_results, outfile, indent=4)

print("Refined results saved to 'refined_results.json'.")
