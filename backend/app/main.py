import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from .database import engine, Base, get_db
from .models.db_models import ChatSession, Message
from .models.schemas import CreateSession, ChatRequest
from .rag.retriever import retrieve
from .providers.cloud_provider import provider_for
from .config import settings
from .skills.ship30_writer import prompt as ship30_prompt
from .skills.artifact_generator import prompt as artifact_prompt
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger=logging.getLogger("lenny")
@asynccontextmanager
async def lifespan(app):
    async with engine.begin() as conn: await conn.run_sync(Base.metadata.create_all)
    yield
app=FastAPI(title="Lenny Growth Assistant",version="1.0.0",lifespan=lifespan)
app.add_middleware(CORSMiddleware,allow_origins=settings.cors_origins.split(','),allow_methods=['*'],allow_headers=['*'])
@app.get('/api/health')
async def health():
    import httpx
    ollama='unavailable'
    try:
      async with httpx.AsyncClient(timeout=2) as c: ollama='ready' if (await c.get(f'{settings.ollama_base_url}/api/tags')).status_code==200 else 'unavailable'
    except Exception: pass
    return {'status':'ok','database':'configured','ollama':ollama,'vector_index':'lexical-demo / pgvector-ready'}
@app.post('/api/sessions')
async def create_session(body:CreateSession, db:AsyncSession=Depends(get_db)):
    item=ChatSession(title=body.title);db.add(item);await db.commit();return {'id':item.id,'title':item.title}
@app.get('/api/sessions/{session_id}')
async def session(session_id:str,db:AsyncSession=Depends(get_db)):
    s=await db.get(ChatSession,session_id)
    if not s: raise HTTPException(404,'Session not found')
    rows=(await db.execute(select(Message).where(Message.session_id==session_id).order_by(Message.created_at))).scalars()
    return {'id':s.id,'title':s.title,'messages':[{'role':m.role,'content':m.content,'sources':m.sources} for m in rows]}
@app.post('/api/chat')
async def chat(body:ChatRequest,db:AsyncSession=Depends(get_db)):
    if not await db.get(ChatSession,body.session_id): raise HTTPException(404,'Session not found')
    matches=retrieve(body.message,settings.retrieval_top_k)
    db.add(Message(session_id=body.session_id,role='user',content=body.message)); await db.commit()
    if not matches:
      answer="I do not have sufficient information in Lenny's podcast archive to answer this. Try asking about a product or growth practice discussed in the loaded transcripts."
      sources=[]
    else:
      sources=[{'title':c.title,'guest':c.guest,'timestamp':c.timestamp,'url':c.url} for _,c in matches]
      context='\n\n'.join(f'[{c.title}: {c.guest}, {c.timestamp}]\n{c.text}' for _,c in matches)
      system=(ship30_prompt(context) if body.mode=='ship30' else artifact_prompt(context) if body.mode=='artifact' else f"You are The Lenny Growth Assistant. Answer strictly from the sources below. Cite every factual claim as [Episode: guest, timestamp]. If unsupported, say so. Be direct and practical.\n\n{context}")
      try: answer=await provider_for(body.provider or settings.default_llm_provider).complete(system,body.message)
      except Exception as e:
       logger.warning({'event':'llm_fallback','provider':body.provider or settings.default_llm_provider,'error':str(e)})
       answer='**Grounded source summary (model unavailable):**\n\n'+ '\n\n'.join(f"- {c.text[:500]} [{c.title}: {c.guest}, {c.timestamp}]" for _,c in matches)
    db.add(Message(session_id=body.session_id,role='assistant',content=answer,sources=sources));await db.commit()
    return {'answer':answer,'sources':sources,'provider':body.provider or settings.default_llm_provider,'mode':body.mode}
