"""F2 : détection des rubriques, quels que soient les titres."""
from src.extraction.rubriques import OBLIGATOIRES, extraire_rubriques


def test_rcp_titres_numerotes():
    texte = """ANNEXE I RESUME DES CARACTERISTIQUES DU PRODUIT

4.1. Indications thérapeutiques
Traitement symptomatique des douleurs légères à modérées et de la fièvre chez l'adulte.

4.2. Posologie et mode d'administration
La dose recommandée est de un gramme jusqu'à trois fois par jour, espacées d'au moins quatre heures.

4.3. Contre-indications
Hypersensibilité à la substance active ou à l'un des excipients mentionnés en rubrique 6.1.

4.5. Interactions avec d'autres médicaments et autres formes d'interactions
Association à prendre en compte avec les anticoagulants oraux et les anti-inflammatoires.
"""
    r = extraire_rubriques(texte)
    assert all(r[k]["trouve"] for k in OBLIGATOIRES)
    assert "Traitement symptomatique des douleurs" in r["indications"]["passage"]
    assert "Hypersensibilité à la substance active" in r["contre_indications"]["passage"]


def test_notice_avec_sommaire():
    """Le titre du sommaire ne doit pas être pris pour la vraie section."""
    tik = "1. QU’EST-CE QUE DOLIPRANE ET DANS QUELS CAS EST-IL UTILISE ?"
    texte = f"""Sommaire de la notice
{tik}
2. QUELLES SONT LES INFORMATIONS A CONNAITRE AVANT DE PRENDRE DOLIPRANE ?

Notice patient
{tik}
Le paracétamol est un antalgique et un antipyrétique utilisé chez l'adulte et l'enfant
pour traiter la fièvre et les douleurs légères à modérées.

2. QUELLES SONT LES INFORMATIONS A CONNAITRE AVANT DE PRENDRE DOLIPRANE ?
Ne prenez jamais DOLIPRANE en cas d'hypersensibilité au paracétamol ou à un excipient.

3. COMMENT PRENDRE DOLIPRANE ?
Chez l'adulte, la posologie est de 500 mg à 1 g par prise, jusqu'à trois fois par jour.

Autres médicaments et DOLIPRANE
Demandez conseil à votre médecin avant d'associer ce médicament à un autre traitement.
"""
    r = extraire_rubriques(texte)
    assert all(r[k]["trouve"] for k in OBLIGATOIRES)
    assert "Le paracétamol est un antalgique" in r["indications"]["passage"]
    assert len(r["indications"]["passage"]) > 100


def test_titres_anglais():
    texte = """Drug Facts
Indications and Usage
Temporarily relieves minor aches and pains due to the common cold, headache and backache.

Contraindications
Do not use
if you have ever had liver disease or severe allergy to acetaminophen.

Directions
Adults: take 2 tablets every 4 to 6 hours, do not exceed 10 tablets in 24 hours.

Drug Interactions
Ask a doctor or pharmacist before use if you are taking other medicines.
"""
    r = extraire_rubriques(texte)
    for rubrique in OBLIGATOIRES:
        assert r[rubrique]["trouve"], rubrique
    assert "Temporarily relieves" in r["indications"]["passage"]


def test_titre_rcp_suivi_dun_sous_titre():
    """Un sous-titre juste après 4.5 ne doit pas faire écarter le vrai 4.5."""
    texte = """4.1. Indications thérapeutiques
Traitement symptomatique des douleurs légères à modérées et de la fièvre chez l'adulte et l'enfant.

4.2. Posologie et mode d'administration
Posologie
La dose recommandée est de 1 g jusqu'à trois fois par jour chez l'adulte.

4.3. Contre-indications
Hypersensibilité au paracétamol ou à l'un des excipients mentionnés en rubrique 6.1.

4.5. Interactions avec d'autres médicaments et autres formes d'interactions
Associations à prendre en compte avec les anticoagulants oraux et les anti-inflammatoires non stéroïdiens.

Interactions avec les examens paracliniques
La prise de paracétamol peut fausser le dosage de la glycémie.

4.8. Effets indésirables
Les effets indésirables sont classés par système-organe et par fréquence.
"""
    r = extraire_rubriques(texte)
    assert r["interactions"]["trouve"]
    assert r["interactions"]["titre"].startswith("4.5.")
    assert "anticoagulants oraux" in r["interactions"]["passage"]
    assert r["posologie"]["titre"].startswith("4.2.")


def test_rubrique_absente():
    r = extraire_rubriques("Document sans aucune rubrique identifiable.\n")
    for rubrique in OBLIGATOIRES:
        assert not r[rubrique]["trouve"]
        assert r[rubrique]["raison"]
        assert r[rubrique]["passage"] == ""
