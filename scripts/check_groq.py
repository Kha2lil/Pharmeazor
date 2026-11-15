"""Premier test : réponse « Connected successfully » attendue. 401 = clé fausse, 429 = trop d'appels.
Lancer depuis la racine : python -m scripts.test_groq  (ou F5 dans VS Code)"""
from src.llm.client import chat
print(chat([{"role": "user", "content": "Réponds juste : OK"}], objet="test_groq", use_cache=False))
