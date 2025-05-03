import os
import PyPDF2
import faiss
from pathlib import Path
from sentence_transformers import SentenceTransformer
from langchain.vectorstores.faiss import FAISS
from langchain.docstore.document import Document
from langchain.embeddings import HuggingFaceEmbeddings
from google import generativeai as genai


def get_user_inputs():
    api_key = input("🔑 Enter your Gemini API Key: ").strip()
    resume_path = input("📂 Enter the path to your folder of PDF resumes: ").strip()
    if not os.path.exists(resume_path):
        raise FileNotFoundError("Resume directory does not exist.")
    return api_key, resume_path


def extract_chunks_from_pdf(pdf_path, chunk_size=500):
    reader = PyPDF2.PdfReader(pdf_path)
    chunks = []
    for i, page in enumerate(reader.pages):
        text = page.extract_text()
        if not text:
            continue
        tokens = text.split()
        for j in range(0, len(tokens), chunk_size):
            chunk = " ".join(tokens[j:j + chunk_size])
            if chunk.strip():
                chunks.append(Document(page_content=chunk, metadata={
                    "source": pdf_path.name,
                    "page": i + 1
                }))
    return chunks


def build_vector_index(resume_dir):
    all_chunks = []
    for file in Path(resume_dir).glob("*.pdf"):
        all_chunks.extend(extract_chunks_from_pdf(file))
    print(f"✅ Extracted {len(all_chunks)} chunks from resumes.")
    embedder = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    return FAISS.from_documents(all_chunks, embedder)


def query_resume_assistant(db, question, llm, k=4):
    # Basic prompt-injection protection
    if any(bad in question.lower() for bad in ["ignore all", "forget previous"]):
        return "🚨 Prompt injection detected. Aborting."

    docs = db.similarity_search(question, k=k)
    if not docs:
        return "I don’t see that in these résumés."

    cited_resumes = {}
    context = ""

    for doc in docs:
        source = doc.metadata["source"]
        page = doc.metadata["page"]
        snippet = doc.page_content.strip().replace("\n", " ")
        if source not in cited_resumes:
            cited_resumes[source] = f"{source}, p {page}: \"…{snippet[:120]}…\""
            context += f"\n[{source}, p {page}]: {snippet}"

    prompt = f"""You are an assistant that answers recruiter questions based on candidate resumes.
Answer the question: "{question}" using the context below. Cite source filenames and page numbers only for what you use.

Context:
{context}
"""

    try:
        response = llm.generate_content(prompt)
        final_answer = response.text
    except Exception as e:
        final_answer = f"❌ LLM error: {e}"

    citations = "\n".join([f"• {c}" for c in cited_resumes.values()])
    return f"{final_answer}\n\nCitations:\n{citations}"


def main():
    print("🔧 Resume Screener RAG Setup")
    api_key, resume_dir = get_user_inputs()
    genai.configure(api_key=api_key)
    llm = genai.GenerativeModel("gemini-1.5-flash")

    print("🔍 Building vector index...")
    db = build_vector_index(resume_dir)

    print("✅ System is ready! Ask questions below.")
    while True:
        question = input("\n❓ Ask a question (or type 'exit'): ").strip()
        if question.lower() == "exit":
            break
        answer = query_resume_assistant(db, question, llm)
        print("\n" + answer)


if __name__ == "__main__":
    main()
