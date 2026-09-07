# Agent transcript — pgvector indexing boundary

Finding: a complete public archive and embedding model can be expensive/network sensitive during evaluator setup. The application therefore isolates retrieval in one module and ships a lexical fixture corpus. Production migration: add `embedding vector(384)` to chunks, create an HNSW cosine index, and replace only `retrieve()`. This preserves the chat/API/UI contract while making the submitted demo resilient.
