from app.rag.retriever import retrieve
def test_retrieves_growth_loop():
 assert retrieve('How do I improve a growth loop?')[0][1].guest == 'Brian Balfour'
def test_out_of_domain_returns_empty():
 assert retrieve('Explain quantum entanglement') == []
