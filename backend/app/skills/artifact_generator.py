def prompt(context:str):
 return f"""Create either a polished Markdown brief or a self-contained HTML/CSS artifact based only on the sources below. No scripts, external URLs, forms, iframes, or event handlers. Return only artifact content after a one-sentence explanation.\n\nSOURCES:\n{context}"""
