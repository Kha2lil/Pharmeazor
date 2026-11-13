"""Chargement de la configuration (YAML) et des variables d'environnement (.env)."""
from pathlib import Path
import os
import yaml

ROOT = Path(__file__).resolve().parent.parent

try:
    from dotenv import load_dotenv
    load_dotenv(ROOT / ".env")
except ImportError:  # python-dotenv optionnel
    pass


def load_config() -> dict:
    with open(ROOT / "config" / "config.yaml", encoding="utf-8") as f:
        return yaml.safe_load(f)


CFG = load_config()


def get_api_key() -> str:
    key = os.environ.get("GROQ_API_KEY")
    if not key:
        raise RuntimeError("GROQ_API_KEY manquante : renseignez .env (voir .env.example).")
    return key
