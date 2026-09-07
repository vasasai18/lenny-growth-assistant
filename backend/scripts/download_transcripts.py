"""Downloads are intentionally explicit: clone the public Lenny transcript repository,
then point ingest.py at its Markdown files. This prevents silently scraping changing pages."""
import subprocess
subprocess.run(['git','clone','https://github.com/lennyrachitsky/podcast-transcripts.git','../data/transcripts'],check=True)
