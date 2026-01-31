# --- SECTION DESCRIPTIONS ---
SECTION_INFO = {
    "ingestion": {
        "chunking_strategy": {
            "title": "Chunking Strategy",
            "description": "How documents are split into smaller pieces for storage and retrieval. This happens during file upload and determines the granularity of your search.",
            "sidebar_location": "📥 Ingestion → Chunking Strategy"
        },
        "enhancements": {
            "title": "Chunk Enhancements",
            "description": "Additional processing applied to chunks to improve retrieval quality. These add metadata, context, or generate synthetic data.",
            "sidebar_location": "📥 Ingestion → Enhancements"
        }
    },
    "retrieval": {
        "query_strategy": {
            "title": "Query Strategy",
            "description": "How your question is processed before searching. Transforms your input to improve matching with stored documents.",
            "sidebar_location": "🔍 Retrieval → Query Strategy"
        },
        "post_retrieval": {
            "title": "Post-Retrieval Processing",
            "description": "Techniques applied after initial search results are returned. These refine, rerank, or compress the results.",
            "sidebar_location": "🔍 Retrieval → Post-Retrieval"
        },
        "agentic": {
            "title": "Agentic RAG",
            "description": "Advanced techniques where the LLM makes decisions about the retrieval process itself - routing queries, validating results, or self-correcting.",
            "sidebar_location": "🔍 Retrieval → Advanced (Agentic)"
        }
    }
}

# --- COMPREHENSIVE RAG TECHNIQUES DATA ---
RAG_TECHNIQUES = {
    "ingestion": {
        "chunking_strategy": [
            {
                "id": "fixed_chunking",
                "name": "Fixed Chunking",
                "number": 3,
                "description": "Splits text into fixed-size chunks with optional overlap.",
                "benefit": "Fast, predictable, works well with uniform content",
                "when_to_use": "Homogeneous documents, when speed is priority",
                "config_key": "chunking_strategy",
                "config_value": "fixed",
                "pros": ["Fast processing", "Predictable chunk sizes", "Simple to understand"],
                "cons": ["May split mid-sentence", "No semantic awareness", "Context loss at boundaries"],
                "code": '''def fixed_chunk(text, chunk_size=1000, overlap=200):
    chunks = []
    for i in range(0, len(text), chunk_size - overlap):
        chunks.append(text[i:i + chunk_size])
    return chunks''',
                "diagram": '''graph LR
    A[Document] --> B[Split by Character Count]
    B --> C[Chunk 1<br/>1000 chars]
    B --> D[Chunk 2<br/>1000 chars]
    B --> E[Chunk N<br/>1000 chars]
    C --> F[(Vector DB)]
    D --> F
    E --> F'''
            },
            {
                "id": "semantic_chunking",
                "name": "Semantic Chunking",
                "number": 2,
                "description": "Uses AI to identify natural topic boundaries instead of arbitrary character counts.",
                "benefit": "Better context preservation, chunks align with actual topics",
                "when_to_use": "Documents with clear topic shifts, long-form content",
                "config_key": "chunking_strategy",
                "config_value": "semantic",
                "pros": ["Preserves semantic meaning", "Better retrieval accuracy", "Natural boundaries"],
                "cons": ["Slower (requires LLM)", "Variable chunk sizes", "May fail on unstructured text"],
                "code": '''def semantic_chunk(text):
    prompt = "Find topic boundaries in this text..."
    boundaries = llm.predict(prompt)
    return split_at_boundaries(text, boundaries)''',
                "diagram": '''graph LR
    A[Document] --> B[LLM Analyzes Topics]
    B --> C{Topic<br/>Boundaries}
    C --> D[Topic 1<br/>Introduction]
    C --> E[Topic 2<br/>Analysis]
    C --> F[Topic 3<br/>Conclusion]
    D --> G[(Vector DB)]
    E --> G
    F --> G'''
            },
            {
                "id": "sentence_window",
                "name": "Sentence Window",
                "number": 9,
                "description": "Index individual sentences but retrieve surrounding context window.",
                "benefit": "High precision search with rich context for generation",
                "when_to_use": "When you need precise matching but full context for answers",
                "config_key": "chunking_strategy",
                "config_value": "sentence_window",
                "pros": ["High search precision", "Rich context for LLM", "Best of both worlds"],
                "cons": ["More storage needed", "Complex metadata", "Requires special retrieval"],
                "code": '''def sentence_window_chunk(text, window=5):
    sentences = split_sentences(text)
    for i, sent in enumerate(sentences):
        window_text = sentences[max(0,i-window):i+window+1]
        store(sentence=sent, window=window_text)''',
                "diagram": '''graph TB
    A[Document] --> B[Split into Sentences]
    B --> C[Sentence 1]
    B --> D[Sentence 2]
    B --> E[Sentence 3]
    C --> F[Window: S1-S6]
    D --> G[Window: S1-S7]
    E --> H[Window: S1-S8]
    C --> I[(Sentence Index)]
    F --> J[(Window Store)]'''
            },
            {
                "id": "proposition_chunking",
                "name": "Proposition Chunking",
                "number": 14,
                "description": "Break complex sentences into atomic facts (propositions).",
                "benefit": "Maximum retrieval granularity, each fact is searchable",
                "when_to_use": "Dense factual documents, knowledge bases",
                "config_key": "chunking_strategy",
                "config_value": "proposition",
                "pros": ["Atomic facts are precise", "No information buried", "Excellent for Q&A"],
                "cons": ["Very slow processing", "Many small chunks", "May lose narrative flow"],
                "code": '''def proposition_chunk(text):
    prompt = "Break into atomic facts..."
    propositions = llm.extract_facts(text)
    # "The CEO founded the company in 2020"
    # -> ["There is a CEO", "The CEO founded a company",
    #     "The founding was in 2020"]
    return propositions''',
                "diagram": '''graph TB
    A[Complex Sentence] --> B[LLM Extracts Facts]
    B --> C[Fact 1: Entity exists]
    B --> D[Fact 2: Action occurred]
    B --> E[Fact 3: Time/Place]
    C --> F[(Vector DB)]
    D --> F
    E --> F'''
            }
        ],
        "enhancements": [
            {
                "id": "context_enrichment",
                "name": "Context Enrichment",
                "number": 4,
                "description": "AI generates summaries of surrounding content and prepends to each chunk.",
                "benefit": "Each chunk carries context about its place in the document",
                "when_to_use": "Complex documents where chunks may lose context",
                "config_key": "enrich_context",
                "config_value": True,
                "pros": ["Chunks know their context", "Better retrieval", "Reduced hallucination"],
                "cons": ["Slower ingestion", "Larger chunks", "LLM cost"],
                "code": '''def enrich_chunk(chunk, document):
    context = get_surrounding_text(chunk, document)
    summary = llm.summarize(context)
    return f"[CONTEXT: {summary}]\\n{chunk}"''',
                "diagram": '''graph LR
    A[Chunk] --> B[Get Surrounding Text]
    B --> C[LLM Summarizes]
    C --> D[Context Summary]
    D --> E[Prepend to Chunk]
    E --> F[Enriched Chunk]
    F --> G[(Vector DB)]'''
            },
            {
                "id": "header_extraction",
                "name": "Contextual Headers",
                "number": 5,
                "description": "Extracts document structure (H1 > H2 > H3) and tags each chunk.",
                "benefit": "Preserves document hierarchy, improves search relevance",
                "when_to_use": "Well-structured documents with clear headings",
                "config_key": "add_headers",
                "config_value": True,
                "pros": ["Preserves structure", "Better filtering", "Navigation context"],
                "cons": ["Only works with headers", "Regex-based", "May miss implicit structure"],
                "code": '''def add_headers(chunk, document):
    headers = extract_header_hierarchy(document)
    section = find_section_for_chunk(chunk, headers)
    return f"[SECTION: {section}]\\n{chunk}"
# Output: "[SECTION: Ch1 > Analysis > Market]\\n..."''',
                "diagram": '''graph TB
    A[Document] --> B[Extract Headers]
    B --> C[H1: Chapter 1]
    C --> D[H2: Analysis]
    D --> E[H3: Market]
    F[Chunk] --> G[Map to Headers]
    E --> G
    G --> H[Tagged Chunk]'''
            },
            {
                "id": "qa_augmentation",
                "name": "Q&A Augmentation",
                "number": 6,
                "description": "Generates question-answer pairs from content to expand search surface.",
                "benefit": "Finds documents even when query phrasing differs from content",
                "when_to_use": "FAQ-style retrieval, diverse query patterns",
                "config_key": "augment_qa",
                "config_value": True,
                "pros": ["Matches question patterns", "Expands searchability", "Better recall"],
                "cons": ["3x more chunks", "Slower ingestion", "May generate bad questions"],
                "code": '''def augment_with_qa(chunk):
    questions = llm.generate_questions(chunk)
    # ["What is the revenue?", "Who is the CEO?"]
    for q in questions:
        store(f"Q: {q}\\nA: {chunk[:500]}")''',
                "diagram": '''graph LR
    A[Chunk] --> B[LLM Generates Qs]
    B --> C[Q1: What is X?]
    B --> D[Q2: How does Y?]
    B --> E[Q3: Why did Z?]
    A --> F[(Main Index)]
    C --> G[(Q&A Index)]
    D --> G
    E --> G'''
            }
        ]
    },
    "retrieval": {
        "query_strategy": [
            {
                "id": "direct_query",
                "name": "Direct Query",
                "number": 7,
                "description": "Uses your question exactly as typed for vector search.",
                "benefit": "Fast, preserves your exact intent",
                "when_to_use": "Clear, well-formed questions",
                "config_key": "query_strategy",
                "config_value": "direct",
                "pros": ["Fastest option", "No transformation errors", "Predictable"],
                "cons": ["Fails on typos", "No semantic expansion", "Exact match only"],
                "code": '''def direct_query(question):
    return vector_db.search(question, n=3)''',
                "diagram": '''graph LR
    A[Question] --> B[(Vector DB)]
    B --> C[Top 3 Chunks]
    C --> D[LLM]
    D --> E[Answer]'''
            },
            {
                "id": "query_rewrite",
                "name": "Query Rewrite",
                "number": 7,
                "description": "AI rewrites your question to be clearer and more searchable.",
                "benefit": "Improves retrieval for ambiguous or informal questions",
                "when_to_use": "Vague questions, conversational queries",
                "config_key": "query_strategy",
                "config_value": "query_rewrite",
                "pros": ["Fixes ambiguity", "Handles typos", "More searchable"],
                "cons": ["Extra LLM call", "May change intent", "Added latency"],
                "code": '''def query_rewrite(question):
    prompt = "Rewrite for search: " + question
    better_query = llm.rewrite(prompt)
    return vector_db.search(better_query, n=3)''',
                "diagram": '''graph LR
    A[Vague Question] --> B[LLM Rewrites]
    B --> C[Clear Question]
    C --> D[(Vector DB)]
    D --> E[Better Results]'''
            },
            {
                "id": "multi_query",
                "name": "Multi-Query",
                "number": 7,
                "description": "Generates 3 paraphrases to search from multiple angles.",
                "benefit": "Higher recall, finds more relevant documents",
                "when_to_use": "Complex topics, when single query misses results",
                "config_key": "query_strategy",
                "config_value": "multi_query",
                "pros": ["Higher recall", "Multiple perspectives", "Robust"],
                "cons": ["3x search cost", "Need deduplication", "Slower"],
                "code": '''def multi_query(question):
    queries = llm.generate_paraphrases(question, n=3)
    all_results = []
    for q in queries:
        all_results.extend(vector_db.search(q))
    return deduplicate(all_results)''',
                "diagram": '''graph TB
    A[Question] --> B[LLM Paraphrases]
    B --> C[Query 1]
    B --> D[Query 2]
    B --> E[Query 3]
    C --> F[(Vector DB)]
    D --> F
    E --> F
    F --> G[Merge & Dedupe]
    G --> H[Combined Results]'''
            },
            {
                "id": "hyde",
                "name": "HyDE",
                "number": 19,
                "description": "Generate a hypothetical answer, embed that, search for similar real documents.",
                "benefit": "Matches semantic intent even with completely different keywords",
                "when_to_use": "When questions use different vocabulary than documents",
                "config_key": "query_strategy",
                "config_value": "hyde",
                "pros": ["Semantic matching", "Vocabulary mismatch solved", "Novel approach"],
                "cons": ["Hallucinated answer", "Extra LLM call", "May mislead"],
                "code": '''def hyde_query(question):
    # Generate hypothetical perfect answer
    fake_answer = llm.hallucinate_answer(question)
    # Search for docs similar to this answer
    return vector_db.search(fake_answer, n=3)''',
                "diagram": '''graph LR
    A[Question] --> B[LLM Generates<br/>Hypothetical Answer]
    B --> C[Fake Answer]
    C --> D[Embed Answer]
    D --> E[(Vector DB)]
    E --> F[Find Similar<br/>Real Documents]'''
            }
        ],
        "post_retrieval": [
            {
                "id": "reranker",
                "name": "Reranker",
                "number": 8,
                "description": "Uses a cross-encoder model to re-score results by true relevance.",
                "benefit": "Much more accurate ranking than embedding similarity alone",
                "when_to_use": "When precision matters more than speed",
                "config_key": "enable_reranker",
                "config_value": True,
                "pros": ["High precision", "Cross-attention", "Better than embeddings"],
                "cons": ["Slower", "Requires model", "N^2 comparisons"],
                "code": '''def rerank(question, chunks, top_k=3):
    pairs = [[question, chunk] for chunk in chunks]
    scores = cross_encoder.predict(pairs)
    ranked = sorted(zip(chunks, scores),
                   key=lambda x: x[1], reverse=True)
    return ranked[:top_k]''',
                "diagram": '''graph TB
    A[Question] --> B[(Vector DB)]
    B --> C[Top 20 Chunks]
    C --> D[CrossEncoder<br/>Scores Each]
    D --> E[Reranked<br/>Top 3]
    E --> F[LLM]'''
            },
            {
                "id": "fusion_rag",
                "name": "Fusion RAG (RRF)",
                "number": 16,
                "description": "Combines multiple search result lists using Reciprocal Rank Fusion.",
                "benefit": "Best results from multiple retrieval strategies",
                "when_to_use": "With Multi-Query or hybrid search",
                "config_key": "enable_fusion",
                "config_value": True,
                "pros": ["Combines strategies", "Robust ranking", "No training needed"],
                "cons": ["Needs multiple lists", "Extra computation", "Complex"],
                "code": '''def reciprocal_rank_fusion(result_lists, k=60):
    scores = {}
    for results in result_lists:
        for rank, doc in enumerate(results):
            scores[doc] += 1.0 / (k + rank + 1)
    return sorted(scores, key=scores.get, reverse=True)''',
                "diagram": '''graph TB
    A[Query 1 Results] --> D[RRF Algorithm]
    B[Query 2 Results] --> D
    C[Query 3 Results] --> D
    D --> E[Combined Ranking]
    E --> F[Final Top K]'''
            },
            {
                "id": "context_compression",
                "name": "Context Compression",
                "number": 10,
                "description": "AI removes irrelevant parts from retrieved text before answering.",
                "benefit": "Cleaner context, reduces noise in final answer",
                "when_to_use": "Long chunks with mixed relevance",
                "config_key": "compress_context",
                "config_value": True,
                "pros": ["Less noise", "Focused context", "Better answers"],
                "cons": ["Extra LLM call", "May remove useful info", "Latency"],
                "code": '''def compress_context(question, chunks):
    prompt = f"Extract only relevant parts for: {question}"
    compressed = llm.extract_relevant(chunks, prompt)
    return compressed''',
                "diagram": '''graph LR
    A[Retrieved Chunks] --> B[LLM Filters]
    B --> C[Relevant Parts Only]
    C --> D[Compressed Context]
    D --> E[Final LLM]'''
            }
        ],
        "agentic": [
            {
                "id": "adaptive_rag",
                "name": "Adaptive RAG",
                "number": 12,
                "description": "Classify query complexity and route to appropriate strategy.",
                "benefit": "Skip RAG for simple questions, use advanced RAG for complex ones",
                "when_to_use": "Mixed query types, optimize for speed and accuracy",
                "config_key": "enable_adaptive",
                "config_value": True,
                "pros": ["Smart routing", "Saves resources", "Optimized"],
                "cons": ["Classification errors", "Extra step", "Complexity"],
                "code": '''def adaptive_rag(question):
    complexity = llm.classify(question)  # simple/specific/complex
    if complexity == "simple":
        return llm.answer_directly(question)
    elif complexity == "complex":
        return advanced_rag(question)
    else:
        return standard_rag(question)''',
                "diagram": '''graph TB
    A[Question] --> B{Classify<br/>Complexity}
    B -->|Simple| C[LLM Direct]
    B -->|Specific| D[Standard RAG]
    B -->|Complex| E[Advanced RAG]
    C --> F[Answer]
    D --> F
    E --> F'''
            },
            {
                "id": "self_rag",
                "name": "Self-RAG",
                "number": 13,
                "description": "LLM critiques its own retrieval and decides if results are relevant.",
                "benefit": "Catches bad retrievals before generating wrong answers",
                "when_to_use": "High-stakes applications, quality over speed",
                "config_key": "enable_self_rag",
                "config_value": True,
                "pros": ["Quality control", "Catches errors", "Self-aware"],
                "cons": ["Extra LLM call", "May reject good results", "Slower"],
                "code": '''def self_rag(question, chunks):
    relevance = llm.evaluate(
        f"Is this relevant to '{question}'? {chunks}"
    )
    if relevance == "NOT_RELEVANT":
        return retry_with_different_strategy()
    return generate_answer(chunks)''',
                "diagram": '''graph TB
    A[Retrieved Chunks] --> B{LLM Evaluates<br/>Relevance}
    B -->|Relevant| C[Generate Answer]
    B -->|Not Relevant| D[Retry/Warn User]
    C --> E[Answer]
    D --> F[Different Strategy]'''
            },
            {
                "id": "crag",
                "name": "CRAG (Corrective)",
                "number": 20,
                "description": "Evaluate answer quality and suggest corrections or external search.",
                "benefit": "Catches wrong answers before showing to user",
                "when_to_use": "When accuracy is critical",
                "config_key": "enable_crag",
                "config_value": True,
                "pros": ["Error detection", "Suggests fixes", "Quality assurance"],
                "cons": ["Post-generation check", "May need web search", "Complex"],
                "code": '''def corrective_rag(question, answer, chunks):
    evaluation = llm.evaluate_answer(question, answer)
    if evaluation == "WRONG":
        return web_search_fallback(question)
    elif evaluation == "AMBIGUOUS":
        return f"{answer}\\n[May be incomplete]"
    return answer''',
                "diagram": '''graph TB
    A[Generated Answer] --> B{LLM Evaluates<br/>Correctness}
    B -->|Correct| C[Return Answer]
    B -->|Ambiguous| D[Add Warning]
    B -->|Wrong| E[Web Search<br/>Fallback]
    D --> F[Final Answer]
    C --> F
    E --> F'''
            }
        ]
    }
}
