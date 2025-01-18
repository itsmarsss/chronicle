# Install required packages
# pip install pypdf langchain-community faiss-cpu sentence-transformers requests

from pypdf import PdfReader
from langchain_community.vectorstores import FAISS
from langchain.llms.base import LLM
import requests
from langchain.text_splitter import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer
from langchain.docstore.document import Document
from langchain.embeddings.base import Embeddings
from pydantic import Field
from langchain.prompts import PromptTemplate
from langchain.chains import RetrievalQA
import json

# Custom Ollama LLM class
class OllamaLLM(LLM):
    model: str = Field(...)

    def _call(self, prompt, stop=None):
        response = requests.post(
            f"http://localhost:11434/api/generate",
            json={
                "model": self.model,
                "prompt": prompt,
                "n_predict": 200,
                "temperature": 0.7,
                "stop": stop if stop else [],
            },
        )
        if response.status_code == 200:
            accumulated_response = ""
            for line in response.iter_lines():
                if line:
                    line_str = line.decode('utf-8')
                    try:
                        line_json = json.loads(line_str)
                        if "response" in line_json and "text" in line_json["response"]:
                            accumulated_response += line_json["response"]["text"]
                        if "done" in line_json and line_json["done"]:
                            if "response" in line_json and "text" in line_json["response"]:
                                accumulated_response += line_json["response"]["text"]
                            break
                    except json.JSONDecodeError as e:
                        print("JSONDecodeError in line:", line_str)
                        continue
            return accumulated_response
        else:
            return f"Error: {response.status_code}"

    @property
    def _identifying_params(self):
        return {"name_of_model": self.model}

    @property
    def _llm_type(self):
        return "custom"

# Custom Embeddings class
class CustomEmbeddings(Embeddings):
    def __init__(self, model_name):
        self.model = SentenceTransformer(model_name)

    def embed_documents(self, texts):
        embeddings = self.model.encode(texts, convert_to_tensor=True)
        print("Embeddings shape:", embeddings.shape)
        return embeddings.tolist()

    def embed_query(self, text):
        embedding = self.model.encode([text], convert_to_tensor=True)
        return embedding.tolist()[0]

# Function to extract text from PDF
def extract_text_from_pdf(pdf_path):
    reader = PdfReader(pdf_path)
    text = ""
    for page_num, page in enumerate(reader.pages, start=1):
        page_text = page.extract_text()
        if page_text:
            text += f"Page {page_num}: " + page_text + "\n"
        else:
            text += f"Page {page_num}: (No text extracted)\n"
    print("Extracted Text:")
    print(text)
    return text

# Function to split text into chunks
def split_text_into_chunks(text, chunk_size=500, chunk_overlap=50):
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    documents = [Document(page_content=text)]
    chunks = text_splitter.split_documents(documents)
    print("Chunks length:", len(chunks))
    print("First chunk content:", chunks[0].page_content if chunks else "No chunks")
    return chunks

# Function to create vector database
def create_vector_database(chunks, embedding_model_name="all-MiniLM-L6-v2"):
    embedding_model = CustomEmbeddings(model_name=embedding_model_name)
    db = FAISS.from_documents(chunks, embedding_model)
    return db

# Function to set up QA chain
def setup_qa_chain(db, llm):
    # Define a custom prompt template
    template = """Use the following context to answer the question at the end.
{context}
Question: {question}
Answer:"""
    prompt = PromptTemplate(template=template, input_variables=["context", "question"])

    # Create RetrievalQA chain
    qa = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=db.as_retriever(k=5),
        chain_type_kwargs={"prompt": prompt},
    )
    return qa

# Function to get important characters
def get_important_characters(qa):
    query = "Who are the main characters in Hamlet?"
    try:
        result = qa.invoke(query)
        return result
    except Exception as e:
        print("Error running QA chain:", e)
        return "Error: Failed to retrieve characters"

# Function to get main events
def get_main_events(qa):
    query = "What are the main events in Hamlet?"
    try:
        result = qa.invoke(query)
        return result
    except Exception as e:
        print("Error running QA chain:", e)
        return "Error: Failed to retrieve events"

# Main function
def main(pdf_path, model_name="llama3.1", embedding_model_name="all-MiniLM-L6-v2"):
    # Extract text from PDF
    text = extract_text_from_pdf(pdf_path)

    # Split text into chunks
    chunks = split_text_into_chunks(text)

    # Create vector database
    db = create_vector_database(chunks, embedding_model_name)

    # Set up Ollama LLM
    llm = OllamaLLM(model=model_name)

    # Set up QA chain
    qa = setup_qa_chain(db, llm)

    # Extract important characters
    characters = get_important_characters(qa)
    print("Important Characters:")
    print(characters)

    # Extract main events
    events = get_main_events(qa)
    print("\nMain Events:")
    print(events)

# Run the main function with your PDF path
if __name__ == "__main__":
    main("Hamlet-1-36.pdf")