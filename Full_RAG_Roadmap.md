# Full RAG Implementation Roadmap (Techniques 9-22)

## 1. Project Context
*   **Current State**: Techniques 1-8 and 10 are implemented in `mba_case_study_buddy`.
*   **Missing from Top 10**: Technique 9 (Sentence Window / Recursive Retrieval).
*   **Goal**: Plan implementation for Tech 9 and the remaining techniques (11-22) from the reference repository, plus enhance the "Learn RAG" educational section.

## 2. Missing "Top 10" Technique

### Technique 9: Sentence Window Retrieval (Recursive)
*   **Concept**: Separate "What you search" (small sentence) from "What you send to LLM" (large window).
*   **Implementation Plan**:
    1.  **Ingestion**: 
        *   Split text into *sentences*.
        *   For each sentence, store it as a vector.
        *   *Metadata*: Store the `window` (e.g., 5 sentences before + 5 after) in a separate field or Key-Value store.
    2.  **Retrieval**:
        *   Search against sentence vectors (high precision).
        *   Fetch the `window` text from metadata.
        *   Send the `window` to the LLM.
*   **Why implementation was delayed**: Requires a different storage schema (Parent-Child relationship) than the current simple chunking.

---

## 3. Remaining Techniques (11-22) Implementation Plan

We categorize these by complexity and prerequisite requirements.

### Phase A: Query & Logic Enhancements (Low Complexity)
These can be implemented on top of the current architecture.

#### Technique 19: HyDE (Hypothetical Document Embeddings)
*   **Concept**: Use LLM to hallucinate a "perfect answer", embed *that*, and search for real documents matching the hallucination.
*   **Benefit**: Matches semantic intent even if keywords differ significantly.
*   **Code**: Add `hyde` option to `transform_query`.

#### Technique 12: Adaptive RAG (The "Router")
*   **Concept**: Classify the query *before* retrieval.
    *   *Simple Query* -> Use Memory / LLM directly.
    *   *Complex/Specific* -> Use RAG.
*   **Implementation**: A lightweight LLM call: "Is this question about specific case details? [Yes/No]".

#### Technique 14: Proposition Chunking
*   **Concept**: Break complex sentences into atomic "propositions" (simple facts).
*   **Implementation**: Ingestion processing step (using LLM) to rewrite complex headers/sentences into standalone facts.

### Phase B: Agentic & Feedback (Medium Complexity)

#### Technique 11: Feedback Loop RAG
*   **Concept**: User rates the answer (👍/👎).
*   **Implementation**: 
    1.  Add Feedback UI in Streamlit.
    2.  Store `(Query, RetrievedChunks, Rating)` in a "Golden Dataset".
    3.  Use this dataset to fine-tune the Reranker or Embedding model (long-term).

#### Technique 13: Self-RAG
*   **Concept**: The LLM critiques its own retrieval.
*   **Implementation**: 
    1.  LLM generates answer `[Retrieval]`.
    2.  LLM checks: "Is this relevant? [Relevant]". If not, re-query or say "I don't know".

### Phase C: Structural & Platform Shifts (High Complexity)

#### Technique 17: Graph RAG
*   **Requirements**: Neo4j or NetworkX.
*   **Concept**: Extract entities (People, Companies) and relationships. Search traverses the graph. "How is Sarah related to the CEO?".
*   **Implementation**: Major backend overhaul to ingest into a Graph DB.

#### Technique 15: Multimodal RAG
*   **Requirements**: `clip` or `llava` models.
*   **Concept**: Embed images (charts in PDFs) and text into the same space.
*   **Implementation**: Use `pymupdf` to extract images, embed with multimodal model.

#### Technique 18: Hierarchy RAG (Raptor)
*   **Concept**: Cluster chunks -> Summarize clusters -> Embed summaries. Tree-based retrieval.
*   **Benefit**: Answer high-level questions ("What is the overall trend?") by hitting top-level summaries.

#### Other Niche Techniques
*   **Tech 16 (Fusion RAG)**: Similar to Multi-Query but uses Reciprocal Rank Fusion (RRF) algorithm to combine lists. Easy to add to Tech 7.
*   **Tech 20 (CRAG - Corrective RAG)**: Retrieve -> Evaluate (Web Search if poor) -> Generate. Requires Web Search tool.
*   **Tech 21 (RAG with RL)**: Reinforcement Learning. (Advanced research scope).
*   **Tech 22 (Big Data KG)**: Knowledge Graphs at scale.

---

## 4. "Learn RAG" Section Enhancements

To make the app a true "Learning Hub", we will implement detail views for each technique.

### Strategy
Add a **"Deep Dive" Mode** in the "Learn RAG" tab. When a user clicks a technique card, open a detailed page.

### Content per Technique
For each technique, we will add:
1.  **Visual Diagram**: A generic Mermaid diagram showing the data flow.
    *   *Example*: "Query -> Query Transform -> Vector DB" vs "Query -> Vector DB".
2.  **Interactive Code Snippet**: Show the simplified Python code logic (`rag_engine.py` snippet).
3.  **Pros & Cons Table**:
    *   *Direct Query*: Fast, but fails on ambiguity.
    *   *Multi-Query*: High recall, but 3x latency.
4.  **"Try It" Link**: Direct deep-link to the Config tab with that setting pre-selected.

### Example Upgrade (Semantic Chunking)
*   **Visual**: Diagram showing a continuous text stream being cut at "Topic Shifts" vs "Fixed Characters".
*   **Code**:
    ```python
    boundaries = llm.predict("Find topic shifts in this text...")
    split_text(text, boundaries)
    ```
*   **Real-world Analogy**: "Like reading a book chapter by chapter (Semantic) vs tearing pages out every 300 words (Fixed)."

## 5. Execution Plan (Next Steps)

1.  **Immediate**: Fix **Technique 9 (Sentence Window)**.
    *   *Action*: Update `ingest_file` to split by sentence but keep window context.
2.  **Next Batch**: Implement **Adaptive RAG (12)** and **HyDE (19)**.
    *   *Action*: Add Router logic to `query` method. Add HyDE option to transformation.
3.  **Educational**: Upgrade "Learn RAG" tab.
    *   *Action*: Add Mermaid diagram support and detailed markdown descriptions for Tech 1-10.
