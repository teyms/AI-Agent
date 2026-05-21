# Session 5 — RAG (Retrieval-Augmented Generation)

## Goal of This Session

By the end of this session, you will understand:

```text id="rag001"
- What RAG actually is
- Why RAG exists
- Embeddings
- Chunking
- Vector databases
- Similarity search
- Retrieval pipelines
- Context injection
- Grounded responses
- Citations
- Why most enterprise AI systems are actually RAG systems
```

You will build your FIRST real RAG system manually.

This is one of the MOST important topics in modern AI engineering.

---

# Part 1 — The Big Problem

LLMs are powerful.

But they have MAJOR limitations.

Example:

```text id="rag002"
"What is our company's PTO policy?"
```

The model does NOT know:

* your internal documents
* company databases
* recent PDFs
* private knowledge
* latest policies

Without retrieval:

```text id="rag003"
LLM hallucinates
```

This is unacceptable in production.

---

# THIS Is Why RAG Exists

RAG means:

```text id="rag004"
Retrieve relevant information
↓
Inject into prompt
↓
Generate grounded response
```

The model answers using REAL retrieved data.

---

# Core RAG Architecture

```text id="rag005"
Documents
 ↓
Chunking
 ↓
Embeddings
 ↓
Vector Database
 ↓
User Query
 ↓
Query Embedding
 ↓
Similarity Search
 ↓
Retrieve Relevant Chunks
 ↓
Inject Into Prompt
 ↓
LLM Generates Answer
```

This architecture dominates enterprise AI.

---

# Part 2 — What Is An Embedding?

An embedding is:

```text id="rag006"
Numerical semantic representation of text
```

Example:

```text id="rag007"
"cat"
"kitten"
"feline"
```

have similar embeddings because their meanings are related.

---

# Embedding Mental Model

Think:

```text id="rag008"
Meaning → coordinates in high-dimensional space
```

Similar meanings:

* closer vectors

Different meanings:

* farther vectors

---

# IMPORTANT CONCEPT

Embeddings capture:

```text id="rag009"
semantic similarity
```

NOT exact keyword matching.

This is VERY important.

---

# Part 3 — Why Traditional Search Is Not Enough

Traditional keyword search:

```text id="rag010"
"car"
```

may NOT find:

```text id="rag011"
"vehicle"
```

Embeddings can.

This is why vector search became important.

---

# Part 4 — Project Structure

```text id="rag012"
session5/
├── main.py
├── ingest.py
├── retriever.py
├── rag.py
├── documents/
├── vector_store.json
├── requirements.txt
└── .env
```

---

# Install Dependencies

```bash id="rag013"
pip install openai python-dotenv numpy
```

---

# requirements.txt

```text id="rag014"
openai
python-dotenv
numpy
```

---

# Part 5 — Create Example Documents

Create:

```text id="rag015"
documents/company_policy.txt
```

Example content:

```text id="rag016"
Employees are entitled to 14 days of annual leave.

Medical leave requires manager approval.

Remote work is allowed 3 days per week.
```

---

# Part 6 — Document Ingestion

## ingest.py

```python id="rag017"
import os
```

---

# Read Documents

```python id="rag018"
def load_documents(folder_path):

    documents = []

    for filename in os.listdir(folder_path):

        filepath = os.path.join(folder_path, filename)

        with open(filepath, "r", encoding="utf-8") as file:

            content = file.read()

            documents.append({
                "filename": filename,
                "content": content
            })

    return documents
```

---

# IMPORTANT CONCEPT

RAG begins with:

```text id="rag019"
Document ingestion
```

This is often a HUGE engineering challenge in real systems.

---

# Part 7 — Chunking (VERY Important)

LLMs cannot process massive documents efficiently.

So we split documents into chunks.

---

# Why Chunking Matters

Bad chunking:

```text id="rag020"
Cuts sentences badly
Breaks context
Poor retrieval
Hallucinations
```

Good chunking is CRITICAL.

---

# Simple Chunker

## ingest.py

```python id="rag021"
def chunk_text(text, chunk_size=200):

    chunks = []

    for i in range(0, len(text), chunk_size):

        chunk = text[i:i + chunk_size]

        chunks.append(chunk)

    return chunks
```

---

# Better Real-World Chunking

Production systems often chunk by:

* paragraphs
* headings
* semantic boundaries
* markdown sections

NOT just characters.

---

# Part 8 — Creating Embeddings

## ingest.py

```python id="rag022"
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI()
```

---

# Embedding Function

```python id="rag023"
def create_embedding(text):

    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=text
    )

    return response.data[0].embedding
```

---

# IMPORTANT CONCEPT

You are converting:

```text id="rag024"
Text
↓
Vector
```

This vector enables similarity search.

---

# Part 9 — Building Simple Vector Store

## ingest.py

```python id="rag025"
import json
```

---

# Create Vector Store

```python id="rag026"
def build_vector_store():

    documents = load_documents("documents")

    vector_store = []

    for doc in documents:

        chunks = chunk_text(doc["content"])

        for chunk in chunks:

            embedding = create_embedding(chunk)

            vector_store.append({
                "text": chunk,
                "embedding": embedding,
                "source": doc["filename"]
            })

    with open("vector_store.json", "w") as f:
        json.dump(vector_store, f)
```

---

# IMPORTANT UNDERSTANDING

You just built a VERY primitive vector DB manually.

Real vector DBs optimize:

* storage
* indexing
* similarity search
* scalability

---

# Part 10 — Retrieval

Now we retrieve relevant chunks.

---

# retriever.py

```python id="rag027"
import json
import numpy as np
from ingest import create_embedding
```

---

# Load Vector Store

```python id="rag028"
with open("vector_store.json", "r") as f:
    vector_store = json.load(f)
```

---

# Cosine Similarity

```python id="rag029"
def cosine_similarity(a, b):

    a = np.array(a)
    b = np.array(b)

    return np.dot(a, b) / (
        np.linalg.norm(a) * np.linalg.norm(b)
    )
```

---

# Retrieve Relevant Chunks

```python id="rag030"
def retrieve(query, top_k=3):

    query_embedding = create_embedding(query)

    scores = []

    for item in vector_store:

        similarity = cosine_similarity(
            query_embedding,
            item["embedding"]
        )

        scores.append({
            "text": item["text"],
            "source": item["source"],
            "score": similarity
        })

    scores.sort(
        key=lambda x: x["score"],
        reverse=True
    )

    return scores[:top_k]
```

---

# THIS Is Vector Search

You are retrieving:

```text id="rag031"
Semantically similar chunks
```

NOT keyword matches.

Very important.

---

# Part 11 — Building The RAG Pipeline

## rag.py

```python id="rag032"
from retriever import retrieve
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI()
```

---

# Main RAG Function

```python id="rag033"
def ask_rag(question):

    retrieved_chunks = retrieve(question)

    context = "\n\n".join([
        chunk["text"]
        for chunk in retrieved_chunks
    ])

    response = client.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": f"""
Answer ONLY using the provided context.

Context:
{context}
"""
            },
            {
                "role": "user",
                "content": question
            }
        ]
    )

    return response.choices[0].message.content
```

---

# IMPORTANT CONCEPT

The model is now:

```text id="rag034"
Grounded
```

because it answers using retrieved data.

This reduces hallucinations significantly.

---

# Part 12 — Main Entry Point

## main.py

```python id="rag035"
from rag import ask_rag

while True:

    question = input("\nQuestion: ")

    if question.lower() == "exit":
        break

    answer = ask_rag(question)

    print("\nAnswer:")
    print(answer)
```

---

# Example

Input:

```text id="rag036"
How many annual leave days do employees get?
```

Output:

```text id="rag037"
Employees are entitled to 14 days of annual leave.
```

---

# Part 13 — Citations (VERY Important)

Production RAG systems should provide sources.

Without citations:

* users cannot verify answers

---

# Add Citations

## rag.py

```python id="rag038"
def ask_rag(question):

    retrieved_chunks = retrieve(question)

    context = "\n\n".join([
        chunk["text"]
        for chunk in retrieved_chunks
    ])

    sources = list(set([
        chunk["source"]
        for chunk in retrieved_chunks
    ]))

    response = client.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": f"""
Answer ONLY using provided context.

Context:
{context}
"""
            },
            {
                "role": "user",
                "content": question
            }
        ]
    )

    answer = response.choices[0].message.content

    return {
        "answer": answer,
        "sources": sources
    }
```

---

# Example Output

```json id="rag039"
{
  "answer": "Employees receive 14 days annual leave.",
  "sources": [
    "company_policy.txt"
  ]
}
```

---

# Part 14 — Why Chunking Quality Matters

This is one of the MOST important RAG lessons.

Bad chunking:

```text id="rag040"
Sentence split badly
↓
Retrieval loses meaning
↓
Wrong answers
```

Chunking quality strongly affects:

* retrieval quality
* hallucination rate
* citation accuracy

---

# Part 15 — Why Retrieval Quality Matters

RAG quality depends mostly on:

```text id="rag041"
retrieval quality
```

NOT model intelligence.

This surprises many beginners.

---

# Important Production Reality

Most RAG failures happen because:

* wrong chunks retrieved
* missing chunks
* bad chunking
* poor embeddings
* noisy context

NOT because the LLM is weak.

---

# Part 16 — Memory vs RAG (Again)

VERY important distinction.

---

# Memory

About:

* user
* conversation
* ongoing tasks

Example:

```text id="rag042"
User likes Python
```

---

# RAG

About:

* external knowledge
* documents
* databases
* company files

Example:

```text id="rag043"
Retrieve HR policy
```

---

# Part 17 — Real Enterprise RAG Architecture

Production systems often look like:

```text id="rag044"
PDFs
Confluence
Slack
Databases
Emails
Google Drive
SharePoint
 ↓
Ingestion Pipeline
 ↓
Chunking
 ↓
Embeddings
 ↓
Vector DB
 ↓
Retrieval
 ↓
LLM
```

This is HUGE in enterprise AI.

---

# Part 18 — Real Vector Databases

You manually built vector storage.

Real systems use:

| Vector DB             | Notes                        |
| --------------------- | ---------------------------- |
| Pinecone              | Managed vector DB            |
| Qdrant                | Popular open-source          |
| Weaviate              | Enterprise-focused           |
| Chroma                | Beginner-friendly            |
| PostgreSQL + pgvector | Very common practical choice |

For you later:

```text id="rag045"
Postgres + pgvector
```

is probably highest ROI.

---

# Part 19 — Common Beginner Mistakes

## Mistake 1

Thinking RAG magically solves hallucinations.

Bad retrieval still causes hallucinations.

---

## Mistake 2

Using huge chunks.

Too much irrelevant context hurts quality.

---

## Mistake 3

No citations.

Users cannot verify responses.

---

## Mistake 4

Retrieving too many chunks.

Context pollution becomes serious.

---

## Mistake 5

Treating vector DB as memory.

RAG and memory are different systems.

---

# Part 20 — What You Learned

You now understand:

## Conceptually

* RAG architecture
* embeddings
* semantic search
* chunking
* vector retrieval
* grounding
* citations

## Technically

* embedding generation
* chunking pipeline
* vector storage
* cosine similarity
* retrieval pipeline
* context injection

This is one of the MOST important AI engineering skills.

---

# Your Exercises

## Exercise 1 — Better Chunking

Chunk by:

* paragraphs
* headings
* sections

instead of characters.

---

## Exercise 2 — Add Multiple Documents

Add:

* engineering handbook
* onboarding docs
* FAQ docs

---

## Exercise 3 — Add Source Citations

Show:

* source filename
* matching chunk

---

## Exercise 4 — Add Conversation Memory

Combine:

* RAG
* memory system

together.

---

## Exercise 5 — Add Retrieval Threshold

If similarity score too low:

```text id="rag046"
"I don't have enough information."
```

instead of hallucinating.

---

# Session 6 Preview

Next you’ll learn:

# Advanced RAG and Production Retrieval Systems

You will build:

```text id="rag047"
- hybrid search
- reranking
- metadata filtering
- retrieval evaluation
- multi-query retrieval
- contextual compression
- parent-child chunking
- query rewriting
```

You’ll finally understand:

* why basic RAG often fails
* why retrieval engineering is difficult
* why enterprise RAG systems are hard to build well
* how modern production retrieval systems work
