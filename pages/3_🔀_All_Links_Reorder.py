import streamlit as st
import sqlite3

DB_PATH = "links.db"
conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

# st.title("🔗 All Links")

# --- Fetch all tags for filtering ---
c.execute("SELECT name FROM tags ORDER BY name")
all_tags = [r[0] for r in c.fetchall()]

# --- Tag filter ---
selected_tags = st.multiselect(
    "Filter by tags",
    options=all_tags
)
from utils import get_links
links = get_links(c, selected_tags)

from utils import get_html_text

if links:
    st.markdown(get_html_text(links), unsafe_allow_html=True)
else:
    st.info("No links to display.")


import pandas as pd

# Create a DataFrame for ordering
df = pd.DataFrame([
    {
        "Order": link["sort_order"],
        "Title": link["title"] or link["url"],
        "URL": link["url"],
        "ID": link["id"]
    }
    for link in links
])

# Sort by Order
df = df.sort_values("Order").reset_index(drop=True)
st.subheader("🔀 Reorder Links")

edited_df = st.data_editor(
    df,
    use_container_width=True,
    hide_index=True,
    key="reorder_editor"
)

if st.button("💾 Save Order"):
    for idx, row in edited_df.iterrows():
        c.execute(
            "UPDATE links SET sort_order = ? WHERE id = ?",
            (row["Order"], row["ID"])
        )
    conn.commit()
    st.success("Order saved successfully!")
    st.rerun()

