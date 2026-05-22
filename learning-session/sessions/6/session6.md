# Session 6 — Advanced RAG and Production Retrieval Systems

## Goal of This Session

By the end of this session, you will understand:

```text id="adv_rag001"
- Why basic RAG often fails
- Hybrid search
- Reranking
- Metadata filtering
- Query rewriting
- Multi-query retrieval
- Parent-child chunking
- Contextual compression
- Retrieval evaluation
- Production retrieval architecture
```

You will evolve your Session 5 RAG system into something MUCH closer to real enterprise AI systems.

This session is where you stop building “toy RAG.”

---

# Part 1 — Why Basic RAG Fails

Your Session 5 RAG works.

But real-world systems quickly hit problems:

```text id="adv_rag002"
- wrong chunks retrieved
- too much irrelevant context
- semantic mismatch
- missing exact keywords
- poor chunk boundaries
- noisy retrieval
- duplicated information
```

This is why retrieval engineering became its own specialization.

---

# IMPORTANT INDUSTRY REALITY

Most enterprise AI failures are:

```text id="adv_rag003"
retrieval failures
```

NOT model failures.

This is VERY important.

---

# Part 2 — The Retrieval Pipeline Is The Real Product

Beginners think:

```text id="adv_rag004"
LLM is the product
```

Reality:

```text id="adv_rag005"
Retrieval quality
+
Context engineering
+
Workflow design
=
The real product
```

The LLM is only ONE component.

---

# Part 3 — Hybrid Search

Basic vector search has weaknesses.

Example:

Query:

```text id="adv_rag006"
"SPR_REPORT_ACTIVE_CASE"
```

Semantic embeddings may fail because:

* exact technical identifiers
* code names
* ticket IDs
* filenames
* acronyms

require keyword matching.

---

# Solution: Hybrid Search

Combine:

```text id="adv_rag007"
Vector Search
+
Keyword Search
```

This is EXTREMELY common in production.

---

# Hybrid Retrieval Architecture

```text id="adv_rag008"
User Query
 ↓
Embedding Search
 ↓
Keyword Search
 ↓
Merge Results
 ↓
Rerank
 ↓
Return Best Chunks
```

---

# Part 4 — Simple Keyword Search

## retriever.py

```python id="adv_rag009"
def keyword_search(query, documents):

    matches = []

    query_lower = query.lower()

    for doc in documents:

        if query_lower in doc["text"].lower():

            matches.append(doc)

    return matches
```

---

# Then Combine Results

```python id="adv_rag010"
def hybrid_search(query):

    vector_results = retrieve(query)

    keyword_results = keyword_search(
        query,
        vector_store
    )

    combined = vector_results + keyword_results

    return combined
```

---

# IMPORTANT CONCEPT

Vector search handles:

```text id="adv_rag011"
semantic meaning
```

Keyword search handles:

```text id="adv_rag012"
exact matches
```

Both are needed.

---

# Part 5 — Reranking (VERY Important)

Initial retrieval is often noisy.

Example:

Top 10 retrieved chunks:

* some relevant
* some partially relevant
* some garbage

---

# Reranking Means

```text id="adv_rag013"
Retrieve many
↓
Use stronger model
↓
Select best few
```

This dramatically improves quality.

---

# Why Reranking Matters

Without reranking:

```text id="adv_rag014"
Context pollution
```

becomes a MAJOR issue.

LLMs become distracted by irrelevant chunks.

---

# Simple Reranking Concept

```text id="adv_rag015"
Retrieve Top 20
↓
Rerank
↓
Keep Best 5
```

Very common production architecture.

---

# Simple Manual Reranker

## retriever.py

```python id="adv_rag016"
def rerank(query, retrieved_chunks):

    scored = []

    query_words = set(query.lower().split())

    for chunk in retrieved_chunks:

        chunk_words = set(
            chunk["text"].lower().split()
        )

        overlap = len(
            query_words.intersection(chunk_words)
        )

        scored.append({
            "chunk": chunk,
            "score": overlap
        })

    scored.sort(
        key=lambda x: x["score"],
        reverse=True
    )

    return [
        item["chunk"]
        for item in scored[:5]
    ]
```

---

# IMPORTANT

This is a primitive reranker.

Production systems use:

* cross-encoder rerankers
* specialized ranking models
* LLM reranking

---

# Part 6 — Metadata Filtering

Enterprise systems MUST support filters.

Example:

```text id="adv_rag017"
department = HR
date > 2025
document_type = policy
security_level = internal
```

Without filtering:

* retrieval quality suffers
* security risks increase

---

# Add Metadata During Ingestion

## ingest.py

```python id="adv_rag018"
vector_store.append({
    "text": chunk,
    "embedding": embedding,
    "source": doc["filename"],
    "department": "HR",
    "document_type": "policy"
})
```

---

# Filtered Retrieval

## retriever.py

```python id="adv_rag019"
def filtered_retrieve(query, department=None):

    query_embedding = create_embedding(query)

    results = []

    for item in vector_store:

        if department:

            if item["department"] != department:
                continue

        similarity = cosine_similarity(
            query_embedding,
            item["embedding"]
        )

        results.append({
            "text": item["text"],
            "score": similarity
        })

    results.sort(
        key=lambda x: x["score"],
        reverse=True
    )

    return results[:5]
```

---

# THIS Is VERY Important

Metadata filtering is critical for:

```text id="adv_rag020"
multi-tenant systems
permissions
security
enterprise governance
```

---

# Part 7 — Query Rewriting

Users ask vague questions.

Example:

```text id="adv_rag021"
"What's the leave policy?"
```

Better retrieval query:

```text id="adv_rag022"
"employee annual leave policy paid leave vacation"
```

---

# Query Rewriting Architecture

```text id="adv_rag023"
User Query
 ↓
LLM Rewrites Query
 ↓
Improved Retrieval
```

Very common production technique.

---

# Query Rewriter

## retriever.py

```python id="adv_rag024"
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI()
```

---

# Rewrite Function

```python id="adv_rag025"
def rewrite_query(query):

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {
                "role": "system",
                "content": """
Rewrite the query to improve retrieval.
Expand abbreviations and clarify intent.
"""
            },
            {
                "role": "user",
                "content": query
            }
        ]
    )

    return response.choices[0].message.content
```

---

# IMPORTANT CONCEPT

Sometimes:

```text id="adv_rag026"
Better query
=
Better retrieval
```

even more than changing embeddings.

---

# Part 8 — Multi-Query Retrieval

One query may miss information.

Solution:

Generate multiple retrieval queries.

---

# Example

Original:

```text id="adv_rag027"
"What is remote work policy?"
```

Generated queries:

```text id="adv_rag028"
- remote work policy
- work from home policy
- hybrid work rules
- telecommuting guidelines
```

This improves recall dramatically.

---

# Multi-Query Architecture

```text id="adv_rag029"
User Query
 ↓
Generate Multiple Queries
 ↓
Run Retrieval Multiple Times
 ↓
Merge Results
 ↓
Deduplicate
 ↓
Rerank
```

Very common advanced RAG pattern.

---

# Part 9 — Contextual Compression

Sometimes retrieved chunks are TOO LARGE.

You do NOT want:

```text id="adv_rag030"
20 pages of irrelevant context
```

Solution:

Compress retrieved content before generation.

---

# Compression Architecture

```text id="adv_rag031"
Retrieved Chunks
 ↓
Extract Relevant Sentences
 ↓
Pass Smaller Context To LLM
```

This reduces:

* cost
* latency
* context pollution

---

# Simple Compression Concept

```python id="adv_rag032"
def compress_chunk(chunk, query):

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {
                "role": "system",
                "content": """
Extract only information relevant
to the query.
"""
            },
            {
                "role": "user",
                "content": f"""
Query:
{query}

Chunk:
{chunk}
"""
            }
        ]
    )

    return response.choices[0].message.content
```

---

# Part 10 — Parent-Child Chunking

Very important production concept.

---

# Problem

Small chunks:

* retrieve accurately
* lose context

Large chunks:

* preserve context
* reduce retrieval precision

---

# Solution

```text id="adv_rag033"
Parent-Child Retrieval
```

---

# Architecture

```text id="adv_rag034"
Large Parent Document
 ↓
Small Child Chunks
 ↓
Retrieve Child
 ↓
Return Parent Context
```

This gives:

* accurate retrieval
* richer context

Very important in enterprise systems.

---

# Part 11 — Retrieval Evaluation

Most beginners NEVER evaluate retrieval quality.

Huge mistake.

---

# What Should Be Evaluated?

```text id="adv_rag035"
- Did retrieval find correct chunk?
- Was chunk relevant?
- Was answer grounded?
- Were citations correct?
```

Evaluation becomes critical in production.

---

# Simple Evaluation Dataset

```python id="adv_rag036"
evaluation_cases = [
    {
        "question": "How many leave days?",
        "expected_source": "company_policy.txt"
    }
]
```

---

# Retrieval Accuracy Metric

```text id="adv_rag037"
Correct retrievals
/
Total retrievals
```

Very important metric.

---

# Part 12 — Hallucination Reduction

Advanced RAG helps reduce hallucinations.

But NEVER fully eliminates them.

---

# Important Rule

If retrieval confidence low:

```text id="adv_rag038"
"I don't know"
```

is MUCH better than hallucinating.

Production systems MUST do this.

---

# Confidence Threshold Example

```python id="adv_rag039"
if top_score < 0.65:
    return "Not enough information found."
```

---

# Part 13 — Production RAG Architecture

Real enterprise architecture:

```text id="adv_rag040"
Documents
PDFs
Confluence
Emails
Slack
Databases
 ↓
Ingestion Pipeline
 ↓
Chunking
 ↓
Metadata Extraction
 ↓
Embeddings
 ↓
Vector DB
 ↓
Hybrid Retrieval
 ↓
Reranking
 ↓
Compression
 ↓
LLM Generation
 ↓
Citations
```

This is MUCH more complex than basic tutorials.

---

# Part 14 — Real Enterprise Challenges

Production RAG systems struggle with:

```text id="adv_rag041"
- stale documents
- permission control
- duplicate content
- inconsistent formatting
- OCR quality
- huge ingestion pipelines
- ranking quality
- cost optimization
```

This is why enterprise AI engineering is hard.

---

# Part 15 — Why Frameworks Exist

You are manually building:

* retrieval pipelines
* reranking
* orchestration
* filtering
* query transformation

This is why:

* LlamaIndex
* LangChain

exist.

But now you understand:

* the mechanics
* the tradeoffs
* the architecture

FIRST.

---

# Part 16 — Common Beginner Mistakes

## Mistake 1

Thinking embeddings alone solve retrieval.

Wrong.

Retrieval quality requires:

* chunking
* reranking
* filtering
* query engineering

---

## Mistake 2

No metadata filtering.

Leads to:

* security issues
* irrelevant results

---

## Mistake 3

No evaluation.

Without evaluation:

* you do not know if retrieval works

---

## Mistake 4

Huge context injection.

Too much context hurts performance.

---

## Mistake 5

Trusting RAG blindly.

Retrieved content can still:

* be wrong
* outdated
* malicious
* incomplete

---

# Part 17 — What You Learned

You now understand:

## Conceptually

* advanced retrieval
* hybrid search
* reranking
* query rewriting
* contextual compression
* retrieval evaluation
* production RAG architecture

## Technically

* hybrid retrieval
* metadata filtering
* reranking pipelines
* query transformation
* confidence thresholds
* retrieval metrics

This is REAL retrieval engineering knowledge.

---

# Your Exercises

## Exercise 1 — Add Metadata Permissions

Example:

```text id="adv_rag042"
Only HR users can retrieve HR docs
```

---

## Exercise 2 — Add Multi-Query Retrieval

Generate:

* 3 rewritten queries
* merge results

---

## Exercise 3 — Add Deduplication

Prevent repeated chunks.

---

## Exercise 4 — Add Retrieval Evaluation

Measure:

* retrieval accuracy
* citation accuracy

---

## Exercise 5 — Add Parent-Child Retrieval

Retrieve:

* small chunks
* return larger parent context

---

# Session 7 Preview

Next you’ll learn:

# Tool-Using Reasoning Agents

You will build systems that can:

```text id="adv_rag043"
- reason across multiple steps
- choose tools dynamically
- reflect on failures
- retry intelligently
- use memory + RAG + tools together
- execute complex workflows
```

You’ll finally understand:

* ReAct-style agents
* reasoning loops
* observation/action cycles
* agent reflection
* why autonomous agents are difficult
* how modern reasoning agents actually work
