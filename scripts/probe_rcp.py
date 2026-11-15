"""Test : la page d'accueil de rcp.anpp.dz contient-elle le jeton et le snapshot Livewire ?"""
import requests

r = requests.get("https://rcp.anpp.dz/", timeout=20,
                 headers={"User-Agent": "PharmeazorStudentProject"})
html = r.text
print("Code :", r.status_code)
print("Taille de la page :", len(html), "caractères")
print("Jeton CSRF (meta) présent :", 'name="csrf-token"' in html)
print("Snapshot Livewire présent :", "wire:snapshot" in html)
print("Cookies reçus :", list(r.cookies.keys()))