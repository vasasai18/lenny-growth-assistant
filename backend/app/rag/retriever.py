from dataclasses import dataclass
from pathlib import Path
import re
@dataclass
class Chunk: title:str; guest:str; timestamp:str; text:str; url:str
def load_chunks():
    path=Path(__file__).parents[2]/"data"/"sample_transcripts.md"
    raw=path.read_text() if path.exists() else ""
    chunks=[]
    for part in raw.split("\n---\n"):
        lines=part.strip().splitlines()
        if len(lines)<2: continue
        meta={}
        for field in lines[0].split("|"):
            key, _, value = field.strip().partition(":")
            if key and value: meta[key.strip()] = value.strip()
        chunks.append(Chunk(meta.get("title","Lenny's Podcast"),meta.get("guest",""),meta.get("timestamp",""),"\n".join(lines[1:]),meta.get("url","")))
    return chunks
CHUNKS=load_chunks()
def retrieve(query:str, top_k:int=5):
    terms=set(re.findall(r"\w+",query.lower()))
    scored=[]
    for c in CHUNKS:
        tokens=set(re.findall(r"\w+",c.text.lower()))
        score=len(terms & tokens)/max(len(terms),1)
        scored.append((score,c))
    return [(s,c) for s,c in sorted(scored, reverse=True,key=lambda x:x[0])[:top_k] if s>0]
