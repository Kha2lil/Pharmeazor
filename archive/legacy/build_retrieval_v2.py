"""Reconstruit l'index de recherche (chunks propres + BM25 + Chroma v2)."""
import pickle
import re
import time
import unicodedata
from pathlib import Path

import chromadb
import numpy as np
import pandas as pd
import pymupdf
from fastembed import TextEmbedding
from rank_bm25 import BM25Okapi

ROOT = Path(__file__).resolve().parent.parent
MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
INDEX = ROOT / "data" / "index"
CHROMA_DIR = INDEX / "chroma_v2"

BOILER = re.compile(r"résumé des caractéristiques|resume des caracteristiques", re.I)
SECTION = re.compile(r"(?m)^\s*(\d+(?:\.\d+)*)\.?\s+[A-ZÀ-ÝÉÈÀÇ]")


def norm_tok(text):
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    return re.findall(r"[a-z0-9]+", text.lower())


def split_sections(text):
    """Découpe un texte PDF en sections numérotées ; garde l'en-tête seulement s'il est substantiel."""
    marks = [(m.start(), m.group(1)) for m in SECTION.finditer(text)]
    if not marks:
        # pas de sections numérotées (ex. Thésaurus) -> garder tel quel
        return [("", text)] if len(norm_tok(text)) >= 40 else []
    out = []
    # ignorer tout ce qui précède la première section (en-têtes laboratoire/adresse)
    for i, (start, num) in enumerate(marks):
        end = marks[i + 1][0] if i + 1 < len(marks) else len(text)
        part = text[start:end].strip()
        if len(norm_tok(part)) >= 40:
            out.append((num, part))
    return out


def main():
    df = pd.read_csv(ROOT / "data" / "metadata" / "documents.csv", encoding="utf-8")
    chunks = []
    dropped = {"intro": 0, "short": 0, "boiler_header": 0}

    for _, row in df.iterrows():
        path = ROOT / Path(row["chemin"])
        meta_common = {"doc_id": row["doc_id"], "medicament": row["medicament"],
                       "source": row["source"], "autorite": int(row["autorite"]),
                       "date_collecte": row["date_collecte"], "url": row["url"],
                       "marque_brute": str(row.get("marque_brute", "") or "")}

        if row["source"] == "bdpm":
            import json
            j = json.loads(path.read_text(encoding="utf-8"))
            title = j.get("titre", "")
            for sec, txt in j.get("sections", {}).items():
                if sec == "intro":
                    dropped["intro"] += 1
                    continue
                if len(norm_tok(txt)) < 40:
                    dropped["short"] += 1
                    continue
                chunks.append({**meta_common, "chunk_id": f"{row['doc_id']}__{sec}",
                               "section": sec, "text": f"{title}\n§{sec}\n{txt}"})
        else:
            doc = pymupdf.open(path)
            for pg, page in enumerate(doc, 1):
                text = page.get_text()
                for sec, part in split_sections(text):
                    if BOILER.search(part) and len(norm_tok(part)) < 60:
                        dropped["boiler_header"] += 1
                        continue
                    chunks.append({**meta_common, "chunk_id": f"{row['doc_id']}__p{pg}_{sec or 'x'}",
                                   "section": f"p{pg}.{sec}" if sec else f"p{pg}",
                                   "text": part})
            doc.close()

    print(f"chunks v2: {len(chunks)} (dropped: {dropped})")

    # BM25
    corpus = [norm_tok(c["text"]) for c in chunks]
    bm25 = BM25Okapi(corpus)
    with open(INDEX / "bm25_chunks_v2.pkl", "wb") as f:
        pickle.dump({"chunks": chunks, "bm25": bm25}, f)

    # embeddings
    print("loading model", MODEL)
    emb = TextEmbedding(model_name=MODEL)
    t0 = time.time()
    vectors = np.array(list(emb.embed([c["text"] for c in chunks], batch_size=64)), dtype="float32")
    print(f"embedded {len(vectors)} in {time.time()-t0:.1f}s")
    np.save(INDEX / "embeddings_v2.npy", vectors)

    # Chroma v2
    import shutil
    if CHROMA_DIR.exists():
        shutil.rmtree(CHROMA_DIR)
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    coll = client.create_collection("pharmeazor_v2", metadata={"hnsw:space": "cosine"})
    ids = [c["chunk_id"] for c in chunks]
    metas = [{k: c[k] for k in ("doc_id", "medicament", "source", "autorite", "date_collecte", "section", "marque_brute")}
             for c in chunks]
    for s in range(0, len(chunks), 5000):
        e = s + 5000
        coll.add(ids=ids[s:e], documents=[c["text"] for c in chunks[s:e]],
                 embeddings=vectors[s:e].tolist(), metadatas=metas[s:e])
    print("collection count:", coll.count())
    print("saved v2 index to", INDEX)


if __name__ == "__main__":
    main()
