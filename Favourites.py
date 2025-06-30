selected_tags=[]

import streamlit as st
import sqlite3
from utils import get_links

DB_PATH = "links.db"
conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

st.title("⭐ Favorite Links")
links = get_links(c, selected_tags)
favourite_links = []
for link in links:
    if link['is_favorite']:
        favourite_links.append(link)

from utils import get_html_text

if favourite_links:
    st.markdown(get_html_text(favourite_links), unsafe_allow_html=True)
else:
    st.info("No links to display.")