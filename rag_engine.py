import os
import re
import json
import fitz  # PyMuPDF
import chromadb
import ollama
from typing import List, Dict, Optional, Tuple, Any
from chromadb.utils import embedding_functions
from collections import defaultdict

# ===========================
# Configuration Defaults
# ===========================

DEFAULT_INGESTION_CONFIG = {
    "chunking_strategy": "fixed",  # "fixed", "semantic", "sentence_window", "proposition"
    "chunk_size": 1000,
    "enrich_context": False,
    "add_headers": False,
    "augment_qa": False,
    "overlap": 200,
    "sentence_window_size": 5,  # For sentence window: sentences before + after
}

DEFAULT_RETRIEVAL_CONFIG = {
    "query_strategy": "direct",  # "direct", "query_rewrite", "multi_query", "hyde"
    "enable_reranker": False,
    "context_logic": "standard",  # "standard" or "sentence_window"
    "compress_context": False,
    "enable_fusion": False,  # Technique 16: Fusion RAG with RRF
    "enable_adaptive": False,  # Technique 12: Adaptive RAG
    "enable_self_rag": False,  # Technique 13: Self-RAG
    "enable_crag": False,  # Technique 20: Corrective RAG
    "n_results": 3,
}

# Feedback storage path
FEEDBACK_FILE = "feedback_data.json"


class RAGEngine:
    def __init__(self, collection_name="mba_cases_v1", persistence_path="./chroma_db"):
        self.client = chromadb.PersistentClient(path=persistence_path)
        self.embedding_fn = self.ollama_embedding_fn

        # Main collection for standard chunks
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"}
        )

        # Separate collection for sentence-level indexing (Technique 9)
        self.sentence_collection = self.client.get_or_create_collection(
            name=f"{collection_name}_sentences",
            metadata={"hnsw:space": "cosine"}
        )

        self.sentence_collection = self.client.get_or_create_collection(
            name=f"{collection_name}_sentences",
            metadata={"hnsw:space": "cosine"}
        )

        self.llm_model = None # User must select model to start
        self.reranker = None  # Lazy load CrossEncoder when needed
        self.feedback_data = self._load_feedback()

    AVAILABLE_MODELS = {
        "deepseek-r1:8b": {
            "name": "DeepSeek R1",
            "role": "Reasoning Engine",
            "pros": "Excellent chain-of-thought logic, great for complex cases.",
            "cons": "Slower due to thinking process. Can be verbose.",
            "icon": "🧠"
        },
        "llama3.1:latest": {
            "name": "Llama 3.1 8B",
            "role": "Balanced All-Rounder",
            "pros": "Fast, reliable, industry standard. Good general capabilities.",
            "cons": "Less 'deep reasoning' capability than R1.",
            "icon": "⚖️"
        },
        "qwen2.5:latest": {
            "name": "Qwen 2.5 7B",
            "role": "Logic & Math Specialist",
            "pros": "Often beats Llama in pure logic/math benchmarks. Very snappy.",
            "cons": "Can be drier in tone.",
            "icon": "🧮"
        }
    }

    def ollama_embedding_fn(self, texts):
        """Custom embedding function using Ollama."""
        embeddings = []
        for text in texts:
            response = ollama.embeddings(model="nomic-embed-text", prompt=text)
            embeddings.append(response["embedding"])
        return embeddings

    # ===========================
    # MODEL MANAGEMENT (New)
    # ===========================

    def unload_model(self):
        """Unload the current model from memory."""
        if self.llm_model:
            try:
                # Send empty request with keep_alive=0 to unload
                print(f"Unloading model: {self.llm_model}")
                ollama.generate(model=self.llm_model, prompt="", keep_alive=0)
            except Exception as e:
                print(f"Error unloading model {self.llm_model}: {e}")

    def switch_model(self, new_model_id: str):
        """
        Switch to a new model.
        Unloads proper model first to ensure exclusive memory usage.
        """
        if new_model_id not in self.AVAILABLE_MODELS:
            raise ValueError(f"Unknown model: {new_model_id}")

        if self.llm_model == new_model_id:
            return  # Already running

        # Unload previous model
        if self.llm_model:
            self.unload_model()

        # Set new model
        self.llm_model = new_model_id
        print(f"Switched to model: {self.llm_model}")
        
        # We generally don't need to 'start' it explicitly, 
        # Ollama loads it on first request. But we could do a dummy ping if needed.


    # ===========================
    # FEEDBACK SYSTEM (Technique 11)
    # ===========================

    def _load_feedback(self) -> List[Dict]:
        """Load feedback data from file."""
        if os.path.exists(FEEDBACK_FILE):
            try:
                with open(FEEDBACK_FILE, 'r') as f:
                    return json.load(f)
            except:
                return []
        return []

    def _save_feedback(self):
        """Save feedback data to file."""
        with open(FEEDBACK_FILE, 'w') as f:
            json.dump(self.feedback_data, f, indent=2)

    def record_feedback(self, query: str, response: str, chunks: List[str], rating: int, comment: str = ""):
        """
        Technique 11: Feedback Loop RAG
        Record user feedback for future fine-tuning and analysis.
        """
        feedback_entry = {
            "timestamp": str(os.popen('date').read().strip()),
            "query": query,
            "response": response[:500],  # Truncate for storage
            "chunks": [c[:200] for c in chunks[:3]],  # Store first 3 chunks, truncated
            "rating": rating,  # 1-5 scale or thumbs up/down
            "comment": comment,
        }
        self.feedback_data.append(feedback_entry)
        self._save_feedback()
        return True

    def get_feedback_stats(self) -> Dict:
        """Get statistics from feedback data."""
        if not self.feedback_data:
            return {"total": 0, "avg_rating": 0, "positive": 0, "negative": 0}

        ratings = [f["rating"] for f in self.feedback_data]
        return {
            "total": len(ratings),
            "avg_rating": sum(ratings) / len(ratings) if ratings else 0,
            "positive": sum(1 for r in ratings if r >= 4),
            "negative": sum(1 for r in ratings if r <= 2),
        }

    # ===========================
    # INGESTION TECHNIQUES (2-6, 9, 14)
    # ===========================

    def split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences for sentence window retrieval."""
        # Simple sentence splitting (can be improved with spaCy/NLTK)
        sentences = re.split(r'(?<=[.!?])\s+', text)
        return [s.strip() for s in sentences if s.strip()]

    def sentence_window_chunking(self, text: str, window_size: int = 5) -> List[Tuple[str, str]]:
        """
        Technique 9: Sentence Window Retrieval
        Returns list of (sentence_for_embedding, window_for_context) tuples.
        """
        sentences = self.split_into_sentences(text)
        results = []

        for i, sentence in enumerate(sentences):
            # Get window: sentences before and after
            start = max(0, i - window_size)
            end = min(len(sentences), i + window_size + 1)
            window = " ".join(sentences[start:end])

            results.append({
                "sentence": sentence,
                "window": window,
                "sentence_idx": i,
                "window_start": start,
                "window_end": end,
            })

        return results

    def proposition_chunking(self, text: str) -> List[str]:
        """
        Technique 14: Proposition Chunking
        Break complex sentences into atomic propositions (simple facts).
        """
        prompt = f"""Break down the following text into atomic propositions (simple, standalone facts).
Each proposition should:
1. Be a complete, self-contained statement
2. Express exactly one fact
3. Be understandable without context

TEXT:
{text[:3000]}

Return ONLY the propositions, one per line, no numbering or bullets."""

        try:
            response = ollama.chat(
                model=self.llm_model,
                messages=[{'role': 'user', 'content': prompt}],
                stream=False
            )

            propositions = response['message']['content'].strip().split('\n')
            propositions = [p.strip() for p in propositions if p.strip() and len(p.strip()) > 10]

            return propositions if propositions else [text]

        except Exception as e:
            print(f"Proposition chunking failed: {e}")
            return self.fixed_chunk(text, 500, 100)

    def semantic_chunk_with_llm(self, text: str, max_chunk_size: int = 1000) -> List[str]:
        """
        Technique 2: Semantic Chunking
        Use LLM to identify semantic boundaries and split text accordingly.
        """
        prompt = f"""Analyze the following text and identify natural semantic boundaries where topics change.
Return ONLY the character positions (as integers) where the text should be split, separated by commas.
Each chunk should be roughly {max_chunk_size} characters, but prioritize semantic coherence.
Do not include any explanation, just the numbers.

TEXT:
{text[:10000]}

Example output: 450,1200,2300"""

        try:
            response = ollama.chat(
                model=self.llm_model,
                messages=[{'role': 'user', 'content': prompt}],
                stream=False
            )

            split_positions_str = response['message']['content'].strip()
            # Extract numbers from response
            split_positions = [int(x.strip()) for x in re.findall(r'\d+', split_positions_str)]

            # Create chunks based on positions
            chunks = []
            prev_pos = 0
            for pos in sorted(split_positions):
                if pos < len(text) and pos > prev_pos:
                    chunks.append(text[prev_pos:pos].strip())
                    prev_pos = pos

            # Add final chunk
            if prev_pos < len(text):
                chunks.append(text[prev_pos:].strip())

            # Fallback to fixed if no valid splits
            if not chunks or len(chunks) == 1:
                return self.fixed_chunk(text, max_chunk_size, 200)

            return [c for c in chunks if c]

        except Exception as e:
            print(f"Semantic chunking failed: {e}. Falling back to fixed chunking.")
            return self.fixed_chunk(text, max_chunk_size, 200)

    def fixed_chunk(self, text: str, chunk_size: int, overlap: int) -> List[str]:
        """Technique 3: Fixed chunking with configurable size."""
        chunks = []
        for i in range(0, len(text), chunk_size - overlap):
            chunks.append(text[i: i + chunk_size])
        return chunks

    def enrich_chunk_with_context(self, chunk: str, surrounding_text: str, chunk_idx: int, total_chunks: int) -> str:
        """
        Technique 4: Context Enriched RAG
        Generate a summary of surrounding section and prepend to chunk.
        """
        context_window = surrounding_text[:2000]

        prompt = f"""Summarize the main topic and context of this document section in 1-2 sentences.
This is chunk {chunk_idx + 1} of {total_chunks}.

SECTION:
{context_window}

Provide ONLY the summary, no preamble."""

        try:
            response = ollama.chat(
                model=self.llm_model,
                messages=[{'role': 'user', 'content': prompt}],
                stream=False
            )

            summary = response['message']['content'].strip()
            # Remove any <think> tags from the response
            summary = re.sub(r'<think>.*?</think>', '', summary, flags=re.DOTALL).strip()
            enriched = f"[CONTEXT: {summary}]\n\n{chunk}"
            return enriched

        except Exception as e:
            print(f"Context enrichment failed: {e}")
            return chunk

    def extract_document_structure(self, text: str) -> Dict[int, str]:
        """
        Technique 5: Contextual Chunk Headers
        Extract document structure (headers) and map to character positions.
        """
        header_pattern = r'^(#{1,3})\s+(.+)$'

        headers_map = {}
        current_headers = ["", "", ""]

        lines = text.split('\n')
        char_pos = 0

        for line in lines:
            match = re.match(header_pattern, line, re.MULTILINE)
            if match:
                level = len(match.group(1))
                header_text = match.group(2).strip()

                current_headers[level - 1] = header_text
                for i in range(level, 3):
                    current_headers[i] = ""

                header_path = " > ".join([h for h in current_headers if h])
                headers_map[char_pos] = header_path

            char_pos += len(line) + 1

        return headers_map

    def get_header_for_position(self, position: int, headers_map: Dict[int, str]) -> str:
        """Find the most recent header for a given text position."""
        if not headers_map:
            return ""

        relevant_positions = [pos for pos in headers_map.keys() if pos <= position]
        if not relevant_positions:
            return ""

        closest_pos = max(relevant_positions)
        return headers_map[closest_pos]

    def generate_qa_augmentation(self, chunk: str, subject: str, chunk_id: str) -> List[Tuple[str, Dict]]:
        """
        Technique 6: Document Augmentation
        Generate Q&A pairs from chunk to increase retrieval surface area.
        """
        prompt = f"""Generate 3 questions that could be answered using the following text from a {subject} case study.
Format: Return ONLY the questions, one per line, no numbering.

TEXT:
{chunk[:1500]}

Example output:
What is the main challenge?
How did the company respond?
What were the financial implications?"""

        try:
            response = ollama.chat(
                model=self.llm_model,
                messages=[{'role': 'user', 'content': prompt}],
                stream=False
            )

            content = response['message']['content'].strip()
            # Remove think tags
            content = re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL).strip()

            questions = content.split('\n')
            questions = [q.strip() for q in questions if q.strip() and '?' in q][:3]

            qa_chunks = []
            for i, question in enumerate(questions):
                qa_text = f"Q: {question}\nA: {chunk[:500]}"
                qa_metadata = {
                    "type": "augmented_qa",
                    "original_chunk_id": chunk_id,
                    "question": question,
                }
                qa_chunks.append((qa_text, qa_metadata))

            return qa_chunks

        except Exception as e:
            print(f"Q&A augmentation failed: {e}")
            return []

    def _ingest_sentence_window(self, full_text: str, config: Dict, subject_name: str, base_filename: str) -> int:
        """Video 9: Sentence Window Retrieval Ingestion"""
        sentence_data = self.sentence_window_chunking(full_text, config["sentence_window_size"])
        
        texts, metadatas, ids = [], [], []
        
        for i, data in enumerate(sentence_data):
            texts.append(data["sentence"])
            metadatas.append({
                "subject": subject_name,
                "source": base_filename,
                "sentence_idx": data["sentence_idx"],
                "window": data["window"],
                "window_start": data["window_start"],
                "window_end": data["window_end"],
                "type": "sentence_window",
            })
            ids.append(f"{subject_name}_{base_filename}_sent_{i}")
            
        if texts:
            print(f"Storing {len(texts)} sentences with windows...")
            self.sentence_collection.add(documents=texts, metadatas=metadatas, ids=ids)
            
        return len(texts)

    def _get_raw_chunks(self, full_text: str, config: Dict) -> List[str]:
        """Techniques 2, 3, 14: Get chunks based on strategy"""
        strategy = config["chunking_strategy"]
        
        if strategy == "proposition":
            initial_chunks = self.fixed_chunk(full_text, config["chunk_size"], config["overlap"])
            propositions = []
            for chunk in initial_chunks:
                propositions.extend(self.proposition_chunking(chunk))
            return propositions
            
        elif strategy == "semantic":
            return self.semantic_chunk_with_llm(full_text, config["chunk_size"])
            
        return self.fixed_chunk(full_text, config["chunk_size"], config["overlap"])

    def _process_and_store(self, chunks: List[str], full_text: str, config: Dict, subject_name: str, base_filename: str, headers_map: Dict):
        """Techniques 4, 5, 6: Process chunks (headers, enrichment, QA) and store"""
        processed_docs, metadatas, ids = [], [], []
        
        for i, chunk in enumerate(chunks):
            # Process chunk content
            final_chunk = chunk
            if config["add_headers"] and headers_map:
                header = self.get_header_for_position(full_text.find(chunk[:100]), headers_map)
                if header: final_chunk = f"[SECTION: {header}]\n\n{final_chunk}"
                
            if config["enrich_context"]:
                final_chunk = self.enrich_chunk_with_context(final_chunk, full_text, i, len(chunks))
                
            # Add main chunk
            chunk_id = f"{subject_name}_{base_filename}_{i}"
            processed_docs.append(final_chunk)
            metadatas.append({
                "subject": subject_name, "source": base_filename, "chunk_id": i,
                "type": "main", "chunking_strategy": config["chunking_strategy"],
                "chunk_size": config["chunk_size"]
            })
            ids.append(chunk_id)
            
            # Add QA chunks
            if config["augment_qa"]:
                for j, (q_text, q_meta) in enumerate(self.generate_qa_augmentation(final_chunk, subject_name, chunk_id)):
                    processed_docs.append(q_text)
                    metadatas.append({"subject": subject_name, "source": base_filename, "chunk_id": i, **q_meta})
                    ids.append(f"{chunk_id}_qa_{j}")
                    
        print(f"Storing {len(processed_docs)} chunks...")
        self.collection.add(documents=processed_docs, metadatas=metadatas, ids=ids)

    def ingest_file(self, file_path: str, subject_name: str, config: Optional[Dict] = None):
        """Ingest a file using configured strategy pipeline"""
        cfg = {**DEFAULT_INGESTION_CONFIG, **(config or {})}
        
        # Read file
        try:
            if file_path.endswith('.pdf'):
                doc = fitz.open(file_path)
                full_text = "".join([page.get_text() for page in doc])
            else:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    full_text = f.read()
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
            return 0
            
        if not full_text.strip(): return 0
        base_filename = os.path.basename(file_path)

        # Structure
        headers_map = self.extract_document_structure(full_text) if cfg["add_headers"] else {}

        # Strategy Execution
        if cfg["chunking_strategy"] == "sentence_window":
            return self._ingest_sentence_window(full_text, cfg, subject_name, base_filename)
            
        chunks = self._get_raw_chunks(full_text, cfg)
        if not chunks: return 0
        
        self._process_and_store(chunks, full_text, cfg, subject_name, base_filename, headers_map)
        return len(chunks)

    # ===========================
    # RETRIEVAL TECHNIQUES (7-10, 12, 13, 16, 19, 20)
    # ===========================

    def classify_query_complexity(self, question: str) -> str:
        """
        Technique 12: Adaptive RAG - Classify query to route appropriately.
        Returns: "simple" (use LLM directly), "specific" (use RAG), "complex" (use advanced RAG)
        """
        prompt = f"""Classify this question into one of three categories:
1. SIMPLE - General knowledge question that doesn't need specific document retrieval
2. SPECIFIC - Question about specific facts/details that needs document lookup
3. COMPLEX - Multi-part question requiring deep analysis across multiple sources

Question: "{question}"

Return ONLY one word: SIMPLE, SPECIFIC, or COMPLEX"""

        try:
            response = ollama.chat(
                model=self.llm_model,
                messages=[{'role': 'user', 'content': prompt}],
                stream=False
            )

            content = response['message']['content'].strip().upper()
            # Remove think tags and extract classification
            content = re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL).strip().upper()

            if "SIMPLE" in content:
                return "simple"
            elif "COMPLEX" in content:
                return "complex"
            else:
                return "specific"

        except:
            return "specific"  # Default to RAG

    def generate_hyde_document(self, question: str) -> str:
        """
        Technique 19: HyDE (Hypothetical Document Embeddings)
        Generate a hypothetical answer to embed for better semantic matching.
        """
        prompt = f"""Write a detailed paragraph that would perfectly answer this question.
Write as if you're quoting from an authoritative document.
Do not say "I don't know" - generate a plausible, detailed answer.

Question: {question}

Hypothetical Answer:"""

        try:
            response = ollama.chat(
                model=self.llm_model,
                messages=[{'role': 'user', 'content': prompt}],
                stream=False
            )

            content = response['message']['content'].strip()
            # Remove think tags
            content = re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL).strip()
            return content

        except Exception as e:
            print(f"HyDE generation failed: {e}")
            return question

    def transform_query(self, question: str, strategy: str) -> List[str]:
        """
        Technique 7: Query Transformation (including HyDE)
        Rewrite or expand user query for better retrieval.
        """
        if strategy == "direct":
            return [question]

        elif strategy == "hyde":
            # Technique 19: HyDE
            hyde_doc = self.generate_hyde_document(question)
            return [hyde_doc]

        elif strategy == "query_rewrite":
            prompt = f"""Rewrite the following question to be clearer and more specific for searching a business case study database.
Return ONLY the rewritten question, no explanation.

ORIGINAL: {question}"""

            try:
                response = ollama.chat(
                    model=self.llm_model,
                    messages=[{'role': 'user', 'content': prompt}],
                    stream=False
                )
                content = response['message']['content'].strip()
                content = re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL).strip()
                return [content] if content else [question]
            except:
                return [question]

        elif strategy == "multi_query":
            prompt = f"""Generate 3 different paraphrases of the following question to search from multiple angles.
Return ONLY the 3 questions, one per line, no numbering.

ORIGINAL: {question}"""

            try:
                response = ollama.chat(
                    model=self.llm_model,
                    messages=[{'role': 'user', 'content': prompt}],
                    stream=False
                )
                content = response['message']['content'].strip()
                content = re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL).strip()

                queries = content.split('\n')
                queries = [q.strip() for q in queries if q.strip()][:3]
                return queries if queries else [question]
            except:
                return [question]

        return [question]

    def reciprocal_rank_fusion(self, results_lists: List[List[Tuple[str, Dict, float]]], k: int = 60) -> List[Tuple[str, Dict]]:
        """
        Technique 16: Fusion RAG with Reciprocal Rank Fusion (RRF)
        Combines multiple ranked lists into a single ranking.
        """
        scores = defaultdict(float)
        doc_map = {}

        for results in results_lists:
            for rank, (doc, metadata, _) in enumerate(results):
                doc_hash = hash(doc[:100])
                scores[doc_hash] += 1.0 / (k + rank + 1)
                doc_map[doc_hash] = (doc, metadata)

        # Sort by RRF score
        sorted_docs = sorted(scores.items(), key=lambda x: x[1], reverse=True)

        return [(doc_map[doc_hash][0], doc_map[doc_hash][1]) for doc_hash, _ in sorted_docs]

    def check_retrieval_relevance(self, question: str, chunks: List[str]) -> Tuple[bool, str]:
        """
        Technique 13: Self-RAG - Check if retrieved content is relevant.
        Returns (is_relevant, explanation)
        """
        context = "\n---\n".join(chunks[:3])

        prompt = f"""Evaluate if the following retrieved content is relevant to answer the question.

Question: {question}

Retrieved Content:
{context[:2000]}

Is this content relevant and sufficient to answer the question?
Return ONLY: RELEVANT or NOT_RELEVANT followed by a brief reason."""

        try:
            response = ollama.chat(
                model=self.llm_model,
                messages=[{'role': 'user', 'content': prompt}],
                stream=False
            )

            content = response['message']['content'].strip()
            content = re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL).strip()

            is_relevant = "NOT_RELEVANT" not in content.upper()
            return is_relevant, content

        except:
            return True, "Evaluation skipped"

    def evaluate_and_correct(self, question: str, chunks: List[str], answer: str) -> Tuple[str, bool]:
        """
        Technique 20: CRAG (Corrective RAG)
        Evaluate answer quality and suggest if web search is needed.
        """
        prompt = f"""Evaluate if this answer adequately addresses the question based on the retrieved context.

Question: {question}
Answer: {answer[:500]}

Rate the answer:
- CORRECT: Answer fully addresses the question with supported facts
- AMBIGUOUS: Answer is partially correct but missing key details
- WRONG: Answer doesn't address the question or contradicts the context

Return ONLY: CORRECT, AMBIGUOUS, or WRONG"""

        try:
            response = ollama.chat(
                model=self.llm_model,
                messages=[{'role': 'user', 'content': prompt}],
                stream=False
            )

            content = response['message']['content'].strip().upper()
            content = re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL).strip().upper()

            if "WRONG" in content:
                return "Answer may be incorrect. Consider searching external sources.", True
            elif "AMBIGUOUS" in content:
                return "Answer may be incomplete. Additional context might help.", False
            else:
                return "Answer appears well-supported by the documents.", False

        except:
            return "", False

    def rerank_results(self, question: str, chunks: List[str], metadatas: List[Dict], top_k: int = 3) -> Tuple[List[str], List[Dict]]:
        """
        Technique 8: Reranker
        Use CrossEncoder to rerank retrieved chunks by relevance.
        """
        try:
            if self.reranker is None:
                from sentence_transformers import CrossEncoder
                print("Loading CrossEncoder model...")
                self.reranker = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')

            pairs = [[question, chunk] for chunk in chunks]
            scores = self.reranker.predict(pairs)

            ranked_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)

            reranked_chunks = [chunks[i] for i in ranked_indices[:top_k]]
            reranked_metadata = [metadatas[i] for i in ranked_indices[:top_k]]

            return reranked_chunks, reranked_metadata

        except Exception as e:
            print(f"Reranking failed: {e}")
            return chunks[:top_k], metadatas[:top_k]

    def compress_context(self, chunks: List[str], question: str) -> str:
        """
        Technique 10: Contextual Compression
        Use LLM to remove irrelevant parts from retrieved chunks.
        """
        context = "\n\n---\n\n".join(chunks)

        prompt = f"""Extract ONLY the parts of the following text that are relevant to answering this question:
"{question}"

Remove any irrelevant details. Keep the relevant parts verbatim. If everything is relevant, return it all.

TEXT:
{context[:3000]}

Return ONLY the relevant extracted text."""

        try:
            response = ollama.chat(
                model=self.llm_model,
                messages=[{'role': 'user', 'content': prompt}],
                stream=False
            )
            content = response['message']['content'].strip()
            content = re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL).strip()
            return content if content else context

        except Exception as e:
            print(f"Context compression failed: {e}")
            return context

    def query(self, question: str, subject: Optional[str] = None, selected_case: Optional[str] = None,
              technique: str = "Simple RAG", retrieval_config: Optional[Dict] = None) -> Tuple[Any, List[str], Dict]:
        """
        Enhanced query with config-driven retrieval pipeline.
        Returns: (stream, chunks, pipeline_info)
        """
        cfg = {**DEFAULT_RETRIEVAL_CONFIG, **(retrieval_config or {})}

        # Track pipeline execution for educational display
        pipeline_info = {
            "steps": [],
            "query_complexity": None,
            "transformed_queries": [],
            "relevance_check": None,
            "correction_check": None,
        }

        # ===== Technique 12: Adaptive RAG =====
        if cfg.get("enable_adaptive"):
            complexity = self.classify_query_complexity(question)
            pipeline_info["query_complexity"] = complexity
            pipeline_info["steps"].append(f"Adaptive RAG: Classified as '{complexity}'")

            if complexity == "simple":
                # Skip RAG, answer directly
                prompt = f"Answer this question directly: {question}"
                stream = ollama.chat(
                    model=self.llm_model,
                    messages=[{'role': 'user', 'content': prompt}],
                    stream=True,
                    keep_alive="1h"
                )
                return stream, [], pipeline_info

        # ===== Technique 7/19: Query Transformation =====
        queries = self.transform_query(question, cfg["query_strategy"])
        pipeline_info["transformed_queries"] = queries
        pipeline_info["steps"].append(f"Query Transform ({cfg['query_strategy']}): {len(queries)} queries")

        # Build metadata filter
        where_filter = None
        conditions = []
        if subject:
            conditions.append({"subject": subject})
        if selected_case:
            conditions.append({"source": selected_case})

        if len(conditions) > 1:
            where_filter = {"$and": conditions}
        elif len(conditions) == 1:
            where_filter = conditions[0]

        # ===== Technique 9: Sentence Window Retrieval =====
        if cfg["context_logic"] == "sentence_window":
            pipeline_info["steps"].append("Using Sentence Window Retrieval")

            all_chunks = []
            all_metadatas = []

            for query_text in queries:
                results = self.sentence_collection.query(
                    query_texts=[query_text],
                    n_results=cfg["n_results"] * 2,
                    where=where_filter
                )

                if results['documents'][0]:
                    # Get the window (larger context) from metadata
                    for i, doc in enumerate(results['documents'][0]):
                        metadata = results['metadatas'][0][i]
                        window = metadata.get("window", doc)
                        all_chunks.append(window)
                        all_metadatas.append(metadata)

            # Deduplicate
            unique_chunks = []
            unique_metadatas = []
            seen = set()
            for chunk, meta in zip(all_chunks, all_metadatas):
                chunk_hash = hash(chunk[:100])
                if chunk_hash not in seen:
                    seen.add(chunk_hash)
                    unique_chunks.append(chunk)
                    unique_metadatas.append(meta)

            final_chunks = unique_chunks[:cfg["n_results"]]
            final_metadatas = unique_metadatas[:cfg["n_results"]]

        else:
            # Standard retrieval
            n_retrieve = 20 if cfg["enable_reranker"] or cfg.get("enable_fusion") else cfg["n_results"]

            all_results = []  # For fusion

            for query_text in queries:
                results = self.collection.query(
                    query_texts=[query_text],
                    n_results=n_retrieve,
                    where=where_filter
                )

                if results['documents'][0]:
                    # Store with distances for fusion
                    query_results = []
                    for i, doc in enumerate(results['documents'][0]):
                        meta = results['metadatas'][0][i]
                        dist = results['distances'][0][i] if results.get('distances') else 0
                        query_results.append((doc, meta, dist))
                    all_results.append(query_results)

            # ===== Technique 16: Fusion RAG =====
            if cfg.get("enable_fusion") and len(all_results) > 1:
                pipeline_info["steps"].append("Applying RRF Fusion")
                fused = self.reciprocal_rank_fusion(all_results)
                all_chunks = [doc for doc, _ in fused]
                all_metadatas = [meta for _, meta in fused]
            else:
                all_chunks = []
                all_metadatas = []
                for query_results in all_results:
                    for doc, meta, _ in query_results:
                        all_chunks.append(doc)
                        all_metadatas.append(meta)

            # Deduplicate
            unique_chunks = []
            unique_metadatas = []
            seen = set()
            for chunk, meta in zip(all_chunks, all_metadatas):
                chunk_hash = hash(chunk[:100])
                if chunk_hash not in seen:
                    seen.add(chunk_hash)
                    unique_chunks.append(chunk)
                    unique_metadatas.append(meta)

            # ===== Technique 8: Reranking =====
            if cfg["enable_reranker"] and unique_chunks:
                pipeline_info["steps"].append("Applying Reranker")
                final_chunks, final_metadatas = self.rerank_results(
                    question, unique_chunks, unique_metadatas, cfg["n_results"]
                )
            else:
                final_chunks = unique_chunks[:cfg["n_results"]]
                final_metadatas = unique_metadatas[:cfg["n_results"]]

        # ===== Technique 13: Self-RAG Relevance Check =====
        if cfg.get("enable_self_rag") and final_chunks:
            is_relevant, explanation = self.check_retrieval_relevance(question, final_chunks)
            pipeline_info["relevance_check"] = {"relevant": is_relevant, "explanation": explanation}
            pipeline_info["steps"].append(f"Self-RAG Check: {'Relevant' if is_relevant else 'Not Relevant'}")

            if not is_relevant:
                # Could retry with different strategy or inform user
                pass

        # ===== Technique 10: Contextual Compression =====
        if cfg["compress_context"] and final_chunks:
            pipeline_info["steps"].append("Applying Context Compression")
            context = self.compress_context(final_chunks, question)
        else:
            context = "\n\n".join(final_chunks)

        # Build final prompt
        prompt = f"""You are an expert assistant. Use the context below to answer the question.
Use clear reasoning to analyze the information.

CONTEXT:
{context}

QUESTION:
{question}
"""

        # Generate with streaming
        stream = ollama.chat(
            model=self.llm_model,
            messages=[{'role': 'user', 'content': prompt}],
            stream=True,
            keep_alive="1h"
        )

        return stream, final_chunks, pipeline_info

    def get_technique_stats(self) -> Dict:
        """Get statistics about stored documents by technique."""
        try:
            main_count = self.collection.count()
            sentence_count = self.sentence_collection.count()

            return {
                "main_chunks": main_count,
                "sentence_chunks": sentence_count,
                "total": main_count + sentence_count,
            }
        except:
            return {"main_chunks": 0, "sentence_chunks": 0, "total": 0}
