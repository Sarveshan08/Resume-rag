import os
os.environ["HF_TOKEN"] = ""
os.environ["HUGGING_FACE_HUB_TOKEN"] = ""
os.environ["HF_API_TOKEN"] = ""
import json
import re 
import pypdf
import chromadb
from groq import Groq
from sentence_transformers import SentenceTransformer
from prompts import SUMMARY_PROMPT, JD_MATCH_PROMPT, QA_PROMPT, STAR_OPTIMIZER_PROMPT, PARSE_RESUME_TO_JSON_PROMPT, RESUME_CLASSIFIER_PROMPT

def get_groq_client(custom_key):
    """
    Initializes and returns the Groq client.
    Requires an API key to be passed in.
    """
    if not custom_key or not custom_key.strip():
        raise ValueError("Groq API Key is missing. Please enter a key in the sidebar.")
    return Groq(api_key=custom_key.strip())

def clean_reasoning(text):
    """
    Removes any <think>...</think> tags and their contents from the LLM output.
    Useful when querying models that return raw chain-of-thought blocks.
    """
    cleaned_text = re.sub(r'<think>.*?</think>','', text, flags=re.DOTALL)
    return cleaned_text.strip()

def load_embedding_model():
    """
    Loads the sentence transformer embedding model locally.
    """
    return SentenceTransformer("all-MiniLM-L6-v2")

def get_chroma_client():
    """
    Initializes an in-memory ChromaDB client for session isolation.
    """
    return chromadb.EphemeralClient()

def classify_is_resume(groq_client, raw_text, model="llama-3.3-70b-versatile"):
    """
    Uses the LLM to classify whether the uploaded PDF is a resume or not.
    Returns True if it is a resume, False otherwise.
    """
    sample_text = raw_text[:1500].strip()
    
    if not sample_text:
        return False
    
    response = groq_client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": RESUME_CLASSIFIER_PROMPT},
            {"role": "user", "content": f"Classify this document:\n\n{sample_text}"}
        ],
        temperature=0,
        max_tokens=10
    )
    
    result = response.choices[0].message.content.strip().upper()
    return result == "RESUME"

def extract_pdf_pages(uploaded_file):
    """
    Extracts text page-by-page from an uploaded PDF.
    Returns a list of dicts: [{"page_number": int,"text": str}]
    """
    reader = pypdf.PdfReader(uploaded_file)
    extracted_data = []

    for idx, page in enumerate(reader.pages):
        text = page.extract_text()
        extracted_data.append({
            "page_number": idx + 1,
            "text": text if text else ""
        })
    return extracted_data

def chunk_pdf_pages(pdf_pages, chunk_size = 800, chunk_overlap=150):
    """
    Splits page texts into overlapping chunks for finer grain retrieval.
    Retains the original page number metadata for referencing.
    """
    chunks = []
    chunk_id = 0

    for page in pdf_pages:
        page_num = page["page_number"]
        text = page["text"]
        start = 0
        while start < len(text):
            end = start + chunk_size
            chunk_content = text[start:end]
            chunks.append({
                "chunk_id": chunk_id,
                "page_number": page_num,
                "text": chunk_content
            })
            chunk_id += 1
            start += (chunk_size - chunk_overlap)
            if len(text) - start < chunk_overlap:
                break
    return chunks

def index_resume_chunks(db_client, chunks, embedding_model, collection_name= "resume_rag"):
    """
    Indexes the text chunks into ChromaDB. Overwrites any existing index.
    """
    try:
        db_client.delete_collection(name=collection_name)
    except Exception:
        pass
    collection = db_client.get_or_create_collection(name=collection_name)
    documents = [c["text"] for c in chunks]
    ids = [str(c["chunk_id"]) for c in chunks]
    metadatas = [{"page_number": c["page_number"]} for c in chunks]
    embeddings = embedding_model.encode(documents).tolist()

    collection.add(
        documents = documents,
        embeddings = embeddings,
        ids = ids,
        metadatas = metadatas
    )
    return collection

def query_resume_context(collection, query_text, embedding_model, n_results = 5):
    """
    Queries ChromaDB for chunks semantically similar to the search query.
    Returns:
    - raw_context: Combined text blocks.
    - results: Raw query outputs containing metadata and page numbers.
    """
    query_embedding = embedding_model.encode([query_text]).tolist()
    results = collection.query(
        query_embeddings=query_embedding,
        n_results=n_results,
    )
    
    context_chunks = []
    if results["documents"] and len(results["documents"][0]) > 0:
        for text, meta in zip (results["documents"][0], results["metadatas"][0]):
            page_info = f"[Source Page {meta['page_number']}]\n{text}"
            context_chunks.append(page_info)
    combined_context = "\n\n---\n\n".join(context_chunks)
    return combined_context, results

def get_resume_summary(client, raw_text, model = "llama-3.3-70b-versatile"):
    """
    Generates a structured analysis and scorecard for the full resume.
    """
    truncated_text = raw_text[:20000]

    response = client.chat.completions.create(
        messages = [
            {"role": "system", "content": SUMMARY_PROMPT},
            {"role": "user", "content": f"Here is the resume content:\n\n{truncated_text}"}
        ],
        model = model,
        temperature = 0.3
    )
    return clean_reasoning(response.choices[0].message.content)

def perform_jd_gap_analysis(client, jd_text, retrieved_context, model = "llama-3.3-70b-versatile"):
    """
    Compares the Job Description requirements with the candidate's actual retrieved resume sections.
    """
    response = client.chat.completions.create(
        messages=[
            {"role": "system", "content": JD_MATCH_PROMPT},
            {"role": "user", "content": f"Target Job Description:\n{jd_text}\n\nCandidate Resume Highlights (Retrieved Context):\n{retrieved_context}"}
        ],
        model = model,
        temperature = 0.3
    )
    return clean_reasoning(response.choices[0].message.content)

def answer_resume_question(client, user_query, retrieved_context, chat_history=[], model="llama-3.3-70b-versatile"):
    """
    Answers a question about the resume using the retrieved RAG context.
    Optionally accepts chat history.
    """
    messages = [{"role": "system", "content": f"{QA_PROMPT}\n\nContext from Resume:\n{retrieved_context}"}]
    
    for msg in chat_history[-6:]:
        messages.append({"role": msg["role"], "content": msg["content"]})
        
    messages.append({"role": "user", "content": user_query})
    
    response = client.chat.completions.create(
        messages=messages,
        model=model,
        temperature=0.2
    )
    return clean_reasoning(response.choices[0].message.content)

def optimize_resume_bullet(client, bullet_text, role_context="", model="llama-3.3-70b-versatile"):
    """
    Rewrites a weak bullet point into a high-impact STAR statement.
    """
    user_content = f"Bullet Point to rewrite: '{bullet_text}'"
    if role_context:
        user_content += f"\nRole Context: {role_context}"
        
    response = client.chat.completions.create(
        messages=[
            {"role": "system", "content": STAR_OPTIMIZER_PROMPT},
            {"role": "user", "content": user_content}
        ],
        model=model,
        temperature=0.5
    )
    return clean_reasoning(response.choices[0].message.content)

def parse_resume_to_json(client, raw_text, model="llama-3.3-70b-versatile"):
    """
    Extracts all resume details into a structured JSON dictionary.
    Fails gracefully by returning an empty schema if the LLM output is malformed.
    """
    response = client.chat.completions.create(
        messages=[
            {"role": "system", "content": PARSE_RESUME_TO_JSON_PROMPT},
            {"role": "user", "content": f"Extract details from this resume text:\n\n{raw_text[:20000]}"}
        ],
        model=model,
        temperature=0.1
    )
    content = clean_reasoning(response.choices[0].message.content)
    content = content.replace("```json", "").replace("```", "").strip()
    
    try:
        return json.loads(content)
    except Exception as e:
        return {
            "personal_info": {
                "name": "", "title": "", "email": "", "phone": "", 
                "location": "", "linkedin": "", "portfolio": ""
            },
            "summary": "",
            "skills": {"technical": [], "soft": []},
            "experience": [],
            "projects": [],
            "education": []
        }