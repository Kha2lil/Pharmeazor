"""F4 - Recherche par mots-clés (BM25). À comparer avec les embeddings (mesure : bon passage dans le top-3 ?)."""
import re
from rank_bm25 import BM25Okapi


def tokeniser(t: str) -> list[str]:
    return re.findall(r"\w+", t.lower())


class BM25Index:
    def __init__(self, passages: list[dict]):
        """passages : [{"doc_id":..., "texte":..., ...}]"""
        self.passages = passages
        self.bm25 = BM25Okapi([tokeniser(p["texte"]) for p in passages])

    def search(self, question: str, k: int = 3) -> list[dict]:
        scores = self.bm25.get_scores(tokeniser(question))
        top = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:k]
        return [{**self.passages[i], "score": float(scores[i])} for i in top]
