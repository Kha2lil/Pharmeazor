"""F2 - Découpage en rubriques (indications, contre-indications, posologie, interactions, effets)."""
import re

TITRES = {
    "indications": r"indications?(?: th[ée]rapeutiques?)?",
    "contre_indications": r"contre[\s-]*indications?",
    "posologie": r"posologie(?: et mode d'administration)?|mode d'emploi",
    "interactions": r"interactions?(?: m[ée]dicamenteuses?)?",
    "effets_indesirables": r"effets? ind[ée]sirables?",
}


def decouper(texte: str) -> dict[str, str]:
    """Retourne {rubrique: passage}, phrases d'origine conservées."""
    motif = "|".join(f"(?P<{k}>{v})" for k, v in TITRES.items())
    reperes = [(m.start(), m.lastgroup)
               for m in re.finditer(rf"(?im)^\s*(?:\d+[\.\)]\s*)?(?:{motif})\s*:?\s*$", texte)]
    out = {}
    for i, (debut, nom) in enumerate(reperes):
        fin = reperes[i + 1][0] if i + 1 < len(reperes) else len(texte)
        out.setdefault(nom, texte[debut:fin].strip())
    return out
