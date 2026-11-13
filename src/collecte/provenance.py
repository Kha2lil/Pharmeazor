"""Fiche de provenance par document (F1) : source, URL, date de collecte, langue, niveau d'autorité."""
import csv, hashlib
from dataclasses import dataclass, asdict, fields
from datetime import date
from pathlib import Path
from src.config import CFG, ROOT


@dataclass
class Fiche:
    doc_id: str
    medicament: str
    source: str
    url: str
    date_collecte: str
    langue: str
    autorite: int
    chemin: str
    sha256: str


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def index_path() -> Path:
    return ROOT / CFG["paths"]["metadata"] / "documents.csv"


def load_index() -> dict[str, dict]:
    p = index_path()
    if not p.exists():
        return {}
    with open(p, encoding="utf-8") as f:
        return {row["sha256"]: row for row in csv.DictReader(f)}


def register(medicament: str, source: str, url: str, langue: str, path: Path) -> Fiche | None:
    """Enregistre un document ; renvoie None s'il existe déjà (pas de doublon, collecte rejouable)."""
    digest = sha256_file(path)
    if digest in load_index():
        return None
    fiche = Fiche(doc_id=digest[:12], medicament=medicament, source=source, url=url,
                  date_collecte=date.today().isoformat(), langue=langue,
                  autorite=CFG["autorite"].get(source, 5), chemin=str(path), sha256=digest)
    p = index_path()
    new = not p.exists()
    with open(p, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=[x.name for x in fields(Fiche)])
        if new:
            w.writeheader()
        w.writerow(asdict(fiche))
    return fiche
