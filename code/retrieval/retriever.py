import os
import re
import pickle
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

model = SentenceTransformer("all-MiniLM-L6-v2")

chunks = []
index = None

INDEX_PATH = "data/index/faiss.index"
META_PATH = "data/index/chunks.pkl"


def clean_text(text):
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def chunk_text(text, size=400, overlap=50):
    res = []
    start = 0
    while start < len(text):
        res.append(text[start:start + size])
        start += size - overlap
    return res


def load_data():
    base = "data"

    for domain in ["claude", "hackerrank", "visa"]:
        folder = os.path.join(base, domain)

        for file in os.listdir(folder):
            path = os.path.join(folder, file)

            try:
                with open(path, "r", encoding="utf-8") as f:
                    text = f.read()
            except:
                continue

            text = clean_text(text)

            for c in chunk_text(text):
                chunks.append({
                    "text": c,
                    "domain": domain
                })


def build_index():
    global index

    # if cached index exists, load it
    if os.path.exists(INDEX_PATH) and os.path.exists(META_PATH):
        index = faiss.read_index(INDEX_PATH)

        with open(META_PATH, "rb") as f:
            stored_chunks = pickle.load(f)

        chunks.clear()
        chunks.extend(stored_chunks)
        return

    # otherwise build fresh
    texts = [c["text"] for c in chunks]
    embeddings = model.encode(texts)

    index = faiss.IndexFlatL2(embeddings.shape[1])
    index.add(np.array(embeddings).astype("float32"))

    # save to disk
    os.makedirs("data/index", exist_ok=True)
    faiss.write_index(index, INDEX_PATH)

    with open(META_PATH, "wb") as f:
        pickle.dump(chunks, f)


def search(query, k=5, domain=None):
    qv = model.encode([query])
    scores, ids = index.search(np.array(qv).astype("float32"), k * 3)

    results = []

    for score, i in zip(scores[0], ids[0]):
        c = chunks[i]

        if domain and c["domain"] != domain:
            continue

        results.append({
            "text": c["text"],
            "domain": c["domain"],
            "score": float(score)
        })

        if len(results) == k:
            break

    return results