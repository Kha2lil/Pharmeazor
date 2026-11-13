"""F6 - Interface Streamlit : question, réponse, sources avec passage exact."""
import streamlit as st

st.set_page_config(page_title="Pharmeazor", page_icon="💊")
st.title("Pharmeazor")
st.caption("Aide à la vérification d'informations médicamenteuses — ne remplace pas l'avis du professionnel.")

q = st.text_input("Question du pharmacien")
if st.button("Chercher") and q:
    st.info("TODO : normalisation → recherche → réponse LLM → contrôle des chiffres → affichage (a)(b)(c)(d).")
