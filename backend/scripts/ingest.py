"""Production ingestion boundary: parse transcript Markdown into 700-token chunks with 100-token overlap.
This demo ships sample_transcripts.md so it works offline; replace Retriever with pgvector embeddings in deployment."""
from pathlib import Path
def chunk(text,size=700,overlap=100):
 words=text.split()
 for i in range(0,len(words),size-overlap): yield ' '.join(words[i:i+size])
if __name__=='__main__': print('Prepared',sum(1 for _ in chunk(Path('../data/sample_transcripts.md').read_text())),'chunks')
