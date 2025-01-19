import pypdf
import json
import os

# Get project root directory
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

text_data = []
with open(PROJECT_ROOT + "/temp/input.pdf", 'rb') as file:
    pdf_reader = pypdf.PdfReader(file)
    num_pages = len(pdf_reader.pages)
    for page_num in range(num_pages):
        page = pdf_reader.pages[page_num]
        text = page.extract_text()
        if text is None:
            continue
        text_data_entry = {
            'page_num': page_num,
            'text': text
        }
        text_data.append(text_data_entry)
        # print("Page:", page_num + 1)
        # print(text)
        # print("-" * 20)

print(json.dumps(text_data, indent=4))

# Ensure temp directory exists
temp_dir = os.path.join(PROJECT_ROOT, 'temp')
os.makedirs(temp_dir, exist_ok=True)

with open(os.path.join(temp_dir, 'transcript.json'), 'w') as outfile:
    json.dump(text_data, outfile, indent=4)

print("Transcript saved to 'transcript.json'.")
