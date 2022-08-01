import streamlit as st

with open('local.css') as f:
    content = f.read()

def local_css(file):
    with open(file) as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)