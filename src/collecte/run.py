"""F1 - Collecte. TODO : lire robots.txt/CGU et les consigner AVANT toute collecte automatique.
Nomenclature officielle : téléchargement MANUEL uniquement."""
DELAI_S = 3  # délai poli entre requêtes


def robots_autorise(base_url: str, chemin: str) -> bool:
    from urllib.robotparser import RobotFileParser
    rp = RobotFileParser(base_url.rstrip("/") + "/robots.txt")
    rp.read()
    return rp.can_fetch("*", base_url.rstrip("/") + chemin)


def main():
    print("TODO : implémenter la collecte par source (voir data/metadata/sources.csv).")


if __name__ == "__main__":
    main()
