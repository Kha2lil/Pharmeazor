"""F5 - Réconciliation : si deux sources divergent, retenir la plus fiable (autorité la plus basse) et le dire."""


def reconcilier(valeurs: list[dict]) -> dict:
    """valeurs : [{"source":..., "autorite": int, "valeur": ..., "doc_id":...}]"""
    if not valeurs:
        return {"statut": "aucune_donnee"}
    meilleur = min(valeurs, key=lambda v: v["autorite"])
    differentes = [v for v in valeurs if str(v["valeur"]).strip() != str(meilleur["valeur"]).strip()]
    if not differentes:
        return {"statut": "accord", "retenue": meilleur}
    return {"statut": "desaccord", "retenue": meilleur, "divergentes": differentes,
            "explication": f"Désaccord détecté : la source {meilleur['source']} (autorité {meilleur['autorite']}) est retenue ; "
                           f"{', '.join(v['source'] for v in differentes)} signalée(s) comme différente(s)."}
