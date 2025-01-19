import json
from openai import OpenAI
from dotenv import load_dotenv
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

load_dotenv()

client = OpenAI(    
    api_key=os.getenv("API_KEY"),
    base_url="https://api.deepseek.com"
)

# Function to process each chunk
def prompt_ai(prompt):
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
                    response = json.loads(json_str)
                    if isinstance(response, list):
                        # Add the chunk number and characters to cumulative_characters
                        return {"response": response}
                    else:
                        print(f"Invalid response format for response")
                except json.JSONDecodeError as json_err:
                    print(f"JSON decode error for response {json_err}")
            else:
                print(f"No JSON list found in response for response")
            break  # Break out of the retry loop if successful
        except Exception as err:
            print(f"An error occurred for response, attempt {attempt + 1}/{retries}: {err}")
            if attempt < retries - 1:
                time.sleep(2)  # Wait for 2 seconds before retrying
            else:
                print(f"Failed after {retries} attempts. Moving on to the next chunk.")
    return None  # Return None if all attempts fail


def process_question(question, char, page, story=""):

    sentim_contexts = []
    all_context = []
    prev_pages = page - 10

    for key in result["contexts"]:
        if char in result["contexts"][key]["characters"]:
            if result["contexts"][key]["page_nums"][-1] <= page and result["contexts"][key]["page_nums"][-1] > prev_pages:
                sentim_contexts.append(result["contexts"][key]["text"])
            if result["contexts"][key]["page_nums"][-1] <= page:
                all_context.append(result["contexts"][key]["text"])
    
    # print(sentim_contexts)
    # print(all_context)
    sentiments = []
    personalities = []

    if sentim_contexts:
        p = f"What are the main sentiments of {char} with the given dialogues? {sentim_contexts}. Please put your response in list format [sentiment1, sentiment2, ...]. Ensure that the response is valid JSON and does not include any comments or explanations."
        sentiments = prompt_ai(p)
    if all_context:
        p = f"What are the most important personality traits of {char} with the given dialogues? {all_context}. Please put your response in list format [trait1, trait2, ...]. Ensure that the response is valid JSON and does not include any comments or explanations."
        personalities = prompt_ai(p)

    # print(sentiments)
    # print(personalities)

    # Craft the prompt to ensure no comments in the JSON response
    prompt = (
        f"You are now {char} in the story {story}. Based off of {char}'s personalities: {personalities} and recent sentiments: {sentiments}"
        f"what would {char} say in response to the following question: {question}"
        f"Ensure that the response is a string and that you don't have any knowledge of anything outside of this book."
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
                stop=None,
            )
            # print(completion.choices[0].message)
            # generated_text = completion.choices[0].message.content
            return {"response": completion.choices[0].message.content}
            
            # Find the JSON list within the response
            start = generated_text.find('[')
            end = generated_text.rfind(']')
            if start != -1 and end != -1 and end > start:
                json_str = generated_text[start:end+1]
                try:
                    response = json.loads(json_str)
                    if isinstance(response, list):
                        # Add the chunk number and characters to cumulative_characters
                        return {"response": response}
                    else:
                        print(f"Invalid response format for ")
                except json.JSONDecodeError as json_err:
                    print(f"JSON decode error for: {json_err}")
            else:
                print(f"No JSON list found in response for ")
            break  # Break out of the retry loop if successful
        except Exception as err:
            print(f"An error occurred for, attempt {attempt + 1}/{retries}: {err}")
            if attempt < retries - 1:
                time.sleep(2)  # Wait for 2 seconds before retrying
            else:
                print(f"Failed after {retries} attempts. Moving on to the next chunk.")
    return None  # Return None if all attempts fail

def chatbot(question, char, page, story=""):
    # cumulative_characters = []

    # Load chunks data
    with open('../out/output.json', 'r') as infile:
        result = json.load(infile)
    return process_question(question, char, page, story)

# For Testing Purposes Only
# while True:
#     question = input("Enter question: ")
#     print(chatbot(question, "Louise Banks", 10, "Story of Your Life"))
# # Function to get important characters
# def get_important_personality(qa, char):
#     query = f"What are the most important personality traits of {char} with the given information? Please put your response in list format [\"trait1", "trait2\", ...]."
#     try:
#         result = qa.invoke(query)
#         return result
#     except Exception as e:
#         print("Error running QA chain:", e)
#         return "Error: Failed to retrieve characters"

# # Function to get main events
# def get_main_sentiments(qa):
#     query = "What are the main events in Hamlet?"
#     try:
#         result = qa.invoke(query)
#         return result
#     except Exception as e:
#         print("Error running QA chain:", e)
#         return "Error: Failed to retrieve events"

# def ask_question(qa, question, char, personality, sentiment):
#     query = f"You are now {char} in the story. Remember that your personality is {personality} and your recent sentiment 
#                 is {sentiment}. You are now to respond to the following question: {question}"
#     try:
#         result = qa.invoke(query)
#         return result
#     except Exception as e:
#         print("Error running QA chain:", e)
#         return "Error: Failed to retrieve events"