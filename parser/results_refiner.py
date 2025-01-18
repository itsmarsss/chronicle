import json
import os
from dotenv import load_dotenv
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer

load_dotenv()

# Get project root directory
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Load the results data
with open(os.path.join(PROJECT_ROOT, 'parser', 'results.json'), 'r') as infile:
    results = json.load(infile)

# Initialize the Sentence-BERT model for name vectorization
model = SentenceTransformer('paraphrase-MiniLM-L6-v2')

# Helper function to convert names into vectors
def get_name_vector(name):
    return model.encode([name])[0]  # Return the vector for the name

# Helper function to calculate cosine similarity between two vectors
def cosine_sim(v1, v2):
    return cosine_similarity([v1], [v2])[0][0]

# Helper function to group similar character names
def group_similar_characters(characters_dict, similarity_threshold=0.8):
    grouped_characters = []
    character_ids = list(characters_dict.keys())  # Work with IDs
    total_ids = len(character_ids)
    
    print(f"Starting to group {total_ids} characters...")
    
    # Precompute the vectors for all names
    name_vectors = {id: get_name_vector(characters_dict[id]["name"]) for id in character_ids}
    
    for i, id1 in enumerate(character_ids):
        if id1 in [id for group in grouped_characters for id in group]:
            continue  # Skip if already grouped
        
        group = [id1]
        name1 = characters_dict[id1]["name"]
        vector1 = name_vectors[id1]
        print(f"Processing character {i + 1}/{total_ids}: {name1}")
        
        for j in range(i + 1, len(character_ids)):
            id2 = character_ids[j]
            if id2 in [id for group in grouped_characters for id in group]:
                continue  # Skip if already grouped
            
            name2 = characters_dict[id2]["name"]
            vector2 = name_vectors[id2]
            
            # Calculate similarity between the two name vectors
            similarity = cosine_sim(vector1, vector2)
            if similarity >= similarity_threshold:
                print(f"    Names '{name1}' and '{name2}' are similar (similarity: {similarity:.2f}). Grouping them.")
                group.append(id2)
        
        grouped_characters.append(group)
        print(f"  Group for '{name1}': {group}")
    
    print("Finished grouping characters.")
    return grouped_characters

# Group similar character names
print("Starting character refinement...")
grouped_characters = group_similar_characters(results["characters"])

# Create a mapping from original names to a canonical name
name_mapping = {}
for group in grouped_characters:
    canonical_name = group[0]  # Use the first name in the group as the canonical name
    for name in group:
        name_mapping[name] = canonical_name
print("Created name mapping for canonical names.")

# Merge contexts for similar characters
refined_characters = {}
for group in grouped_characters:
    canonical_id = group[0]  # Use the first ID in the group as the canonical ID
    merged_contexts = []
    
    for char_id in group:
        if char_id in results["characters"]:
            merged_contexts.extend(results["characters"][char_id]["contexts"])
    
    # Remove duplicate contexts
    merged_contexts = list(set(merged_contexts))
    
    # Add the canonical character to the refined characters dictionary
    refined_characters[canonical_id] = {
        "id": canonical_id,
        "name": results["characters"][canonical_id]["name"],
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
        if character_name in name_mapping:
            refined_characters_list.append(name_mapping[character_name])
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
with open(os.path.join(PROJECT_ROOT, 'parser', 'refined_results.json'), 'w') as outfile:
    json.dump(refined_results, outfile, indent=4)

print("Refined results saved to 'refined_results.json'.")
