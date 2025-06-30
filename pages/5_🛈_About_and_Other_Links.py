import streamlit as st
import streamlit as st

st.title("🔗 My Useful Links")
st.write("""
Welcome to my multi-page app containing links to educational resources, university sites, job boards, and other useful websites.
Use the navigation menu on the left to explore each section.
""")

st.title("🌐 Other Useful Links")

other_links = {
    "GitHub": "https://github.com/",
    "Stack Overflow": "https://stackoverflow.com/",
    "Reddit": "https://www.reddit.com/",
    "Wikipedia": "https://www.wikipedia.org/"
}

for name, url in other_links.items():
    st.markdown(f"- [{name}]({url})")
