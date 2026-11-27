# Journal robots.txt et conditions d'utilisation

## ANPP (anpp.dz) et ANPP RCP (rcp.anpp.dz)
- Date de vérification : 15/11/2026
- robots.txt anpp.dz : seul /wp-admin/ est interdit
- robots.txt rcp.anpp.dz : aucune restriction (Disallow vide)
- CGU / mentions légales : non trouvées sur les deux sites (seulement un "Recueil des exigences légales", qui ne concerne pas l'usage du site)
- Particularités : recherche via une requête Livewire (POST /livewire/update) ; PDF avec vrai texte, pas d'OCR nécessaire
- Décision : collecte automatique, délai de 3 s entre requêtes, uniquement les RCP des 40 médicaments de la liste
- À signaler à l'enseignant : absence de CGU explicite
- Précision : pour retrouver les 40 médicaments (la recherche par DCI étant peu fiable), on lit la liste des résultats (marque, DCI, laboratoire, lien) pour des lettres isolées ; seuls les PDF des 40 médicaments sont téléchargés.

## AFMPS / FAMHP (famhp.be)
- Date de vérification : 27/11/2026 (vérification faite **après** la collecte du 15/11/2026 ; limite à signaler à l'enseignant)
- robots.txt : https://www.famhp.be/robots.txt — `User-agent: *` ; `Allow` pour les CSS/JS/images sous `/core/` et `/profiles/` ; `Disallow` pour `/core/`, `/profiles/`, `/admin/`, `/search/`, `/user/register`, `/user/login`, `/user/logout`, `/node/add/`, `/comment/reply/`
- CGU / disclaimer : https://www.famhp.be/en/disclaimer — « Exception is made for non-commercial academic or educational uses » ; « Any reproduction of the site must cite the source » ; toute autre reproduction nécessite une autorisation écrite préalable ; les traductions doivent porter la mention « translation not the work of the author of the text ». Page mise à jour le 04/11/2026.
- Décision : usage pédagogique non commercial conforme ; mention de la source obligatoire dans le rapport ; aucun contournement des chemins interdits.
- Les PDF collectés (notices, RCP, DHPC) possèdent un vrai calque de texte : aucun OCR nécessaire.