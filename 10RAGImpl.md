# 10 RAG Techniques - Implementation Roadmap

## 1. Architectural Strategy: Ingestion vs. Retrieval
To provide an intuitive UX, we must categorize RAG techniques based on *when* they are applied.

### A. Ingestion-Time (The "How we Store" Layer)
These techniques change how the document is processed, split, and embedded.
*   **User Action**: Select these **during file upload** in the "Manage Subjects" tab.
*   **Why**: Once a file is processed (e.g., chunked by "Semantic" vs "Fixed"), it is stored that way in the Vector DB. To change it, you must re-upload/re-process.

### B. Retrieval-Time (The "How we Search" Layer)
These techniques change how we find and process chunks *after* the user asks a question.
*   **User Action**: Select these **in the Sidebar** during the chat.
*   **Why**: You can apply different search strategies (like Reranking or Query Transformation) on the *same* stored data without re-processing.

---

## 2. The 10 Techniques Breakdown

### Technique 1: Simple RAG (Implemented ✅)
*   **Type**: Baseline
*   **Description**: Standard fixed-size chunking + Cosine Similarity.

### Technique 2: Semantic Chunking
*   **Type**: Ingestion
*   **Implementation**: Use LLM/Embeddings to split text by *meaning* rather than character count.
*   **UI Change**: "Upload" Dropdown -> `Chunking Logic: [Fixed (Default), Semantic]`

### Technique 3: Chunk Size Selector
*   **Type**: Ingestion
*   **Implementation**: Allow user to define chunk size (Small=Granular, Large=Context).
*   **UI Change**: "Upload" Slider -> `Chunk Size: 512 - 2048 tokens`

### Technique 4: Context Enriched RAG
*   **Type**: Ingestion
*   **Implementation**: Generate a summary of the surrounding section and prepend it to the chunk.
*   **UI Change**: "Upload" Checkbox -> `[x] Enrich Chunks with Context`

### Technique 5: Contextual Chunk Headers
*   **Type**: Ingestion
*   **Implementation**: Prepend document structure (H1 > H2 > H3) to each chunk so the model knows "where" this chunk came from.
*   **UI Change**: "Upload" Checkbox -> `[x] Add Section Headers`

### Technique 6: Document Augmentation
*   **Type**: Ingestion
*   **Implementation**: Generate domain-specific Q&A or summaries and add them as *additional* retrievable chunks.
*   **UI Change**: "Upload" Checkbox -> `[x] Augment with Q&A Generation`

### Technique 7: Query Transformation
*   **Type**: Retrieval
*   **Implementation**: Rewrite the user's question (e.g., decompose complex questions, fix ambiguity) before searching.
*   **UI Change**: Sidebar -> `Query Strategy: [Direct, Query Rewrite, Multi-Query]`

### Technique 8: Reranker
*   **Type**: Retrieval
*   **Implementation**: Retrieve 20 results (instead of top 5), then use a high-precision `Cross-Encoder` model to sort them by relevance.
*   **UI Change**: Sidebar -> `[x] Enable Reranker`

### Technique 9: Recursive / Sentence Window (RSE)
*   **Type**: Retrieval (Hybrid)
*   **Implementation**: Index small "sentence" chunks, but retrieve the full "window" (surrounding 5 sentences) for context.
*   **UI Change**: Sidebar -> `Context logic: [Standard, Sentence Window]`

### Technique 10: Contextual Compression
*   **Type**: Retrieval
*   **Implementation**: Use an LLM to "compress" the retrieved chunks, removing irrelevant fluff before sending to the final Chat Model.
*   **UI Change**: Sidebar -> `[x] Compress Context`

---

## 3. Implementation Execution

### Phase 1: Ingestion Engine (Techniques 2-6)
Ideally, we implement a "Processing Pipeline" class in `rag_engine.py`.
1.  **Refactor `ingest_file`**: Accept `configuration` object (chunk_strategy, chunk_size, augmentation_flags).
2.  **UI**: Update "Manage Subjects" with an "Advanced Upload Settings" expander.

### Phase 2: Retrieval Engine (Techniques 7-10)
Update `query` method in `rag_engine.py`.
1.  **Refactor `query`**: Accept `retrieval_config` object (rerank=True, query_transform=True).
2.  **UI**: Update Sidebar with "Advanced Retrieval Settings".

## 4. Current Code Context
*   **Repo**: `mba_case_study_buddy`
*   **Files**: `app.py`, `rag_engine.py`
*   **State**: Simple RAG (Tech 1) active. Streaming enabled. UI has Tabs. Ingestion is fixed character split.

## 5. Next Steps
1.  Implement **Semantic Chunking** (Tech 2) using `semantic-text-splitter` or LLM-based approaches.
2.  Implement **Reranker** (Tech 8) using `sentence-transformers/all-MiniLM-L6-v2` cross-encoder logic (or similar).
3.  Add UI controls for these.
