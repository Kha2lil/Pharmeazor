from src.reconciliation.detect import reconcilier


def test_source_officielle_retenue():
    r = reconcilier([{"source": "anpp", "autorite": 1, "valeur": "A", "doc_id": "1"},
                     {"source": "sites_pro", "autorite": 4, "valeur": "B", "doc_id": "2"}])
    assert r["statut"] == "desaccord" and r["retenue"]["valeur"] == "A"
