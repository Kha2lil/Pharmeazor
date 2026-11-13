"""F4 - Contrôle déterministe des chiffres : chaque nombre de la réponse doit figurer tel quel dans un passage cité."""
import re

NOMBRE = re.compile(r"\d+(?:[.,]\d+)?")


def _n(s: str) -> str:
    return s.replace(",", ".")


def nombres(texte: str) -> list[str]:
    return [_n(m) for m in NOMBRE.findall(texte)]


def verifier(reponse: str, passages_cites: list[str]) -> dict:
    """Renvoie {ok: bool, introuvables: [...]}. Un chiffre introuvable est bloqué et signalé."""
    presents = set(nombres(" ".join(passages_cites)))
    manquants = sorted({n for n in nombres(reponse) if n not in presents})
    return {"ok": not manquants, "introuvables": manquants}
