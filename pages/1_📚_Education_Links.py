selected_tags=['Education']

import streamlit as st
import sqlite3
from utils import get_links

DB_PATH = "links.db"
conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

st.title("📚 Education Links")
links = get_links(c, selected_tags)
from utils import get_html_text

if links:
    st.markdown(get_html_text(links), unsafe_allow_html=True)
else:
    st.info("No links to display.")
