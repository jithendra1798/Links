import streamlit as st
import sqlite3

DB_PATH = "links.db"

# Connect to the SQLite database (creates it if it doesn't exist)
conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

# Create tables if they don't exist
c.execute("""
CREATE TABLE IF NOT EXISTS links (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT,
    url TEXT,
    is_favorite INTEGER,
    sort_order INTEGER DEFAULT 0,
    icon_url TEXT
)
""")

c.execute("""
CREATE TABLE IF NOT EXISTS tags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE
)
""")

c.execute("""
CREATE TABLE IF NOT EXISTS link_tags (
    link_id INTEGER,
    tag_id INTEGER,
    FOREIGN KEY (link_id) REFERENCES links(id),
    FOREIGN KEY (tag_id) REFERENCES tags(id),
    PRIMARY KEY (link_id, tag_id)
)
""")
# c.execute('ALTER TABLE links RENAME COLUMN icon TO icon_url;')
conn.commit()

# st.title("Step 1: Database Initialized")
# st.write("Your SQLite database and tables are ready.")
#
#
# st.title("Step 2: Add a New Link")

# Get existing tags from the database to show as options
c.execute("SELECT name FROM tags ORDER BY name")
existing_tags = [row[0] for row in c.fetchall()]

# Form to enter link details
with st.form("add_link_form"):
    title = st.text_input("Title")
    url = st.text_input("URL")
    icon_url = st.text_input("Icon URL (optional)", help="URL of an image to display as icon.")
    selected_tags = st.multiselect(
        "Tags (select existing)",
        options=existing_tags
    )
    new_tags = st.text_input(
        "New tags (comma separated)",
        help="If you want to add tags that don't exist yet, type them here separated by commas."
    )
    is_favorite = st.checkbox("Mark as favorite")
    submitted = st.form_submit_button("Submit")

if submitted:
    if not url.strip():
        st.error("URL is required.")
    else:
        # Save the link to the database
        c.execute(
            "INSERT INTO links (title, url, is_favorite, icon_url) VALUES (?, ?, ?, ?)",
            (title.strip(), url.strip(), int(is_favorite), icon_url.strip())
        )
        link_id = c.lastrowid

        # Process all tags
        all_tags = set(tag.strip() for tag in selected_tags)

        if new_tags.strip():
            all_tags.update(tag.strip() for tag in new_tags.split(",") if tag.strip())

        for tag in all_tags:
            # Insert the tag if not exists
            c.execute("INSERT OR IGNORE INTO tags (name) VALUES (?)", (tag,))
            # Get the tag id
            c.execute("SELECT id FROM tags WHERE name=?", (tag,))
            tag_id = c.fetchone()[0]
            # Link tag to link
            c.execute("INSERT INTO link_tags (link_id, tag_id) VALUES (?, ?)", (link_id, tag_id))

        conn.commit()

        st.success("✅ Link and tags saved!")
        st.write("**Title:**", title)
        st.write("**URL:**", url)
        st.write("**Favorite:**", "Yes" if is_favorite else "No")
        st.write("**Tags:**", ", ".join(all_tags) if all_tags else "(none)")


st.header("📋 All Saved Links")

# Query to get all links with their tags
c.execute("""
SELECT 
    links.id,
    links.title,
    links.url,
    links.icon_url,
    links.is_favorite,
    GROUP_CONCAT(tags.name, ', ')
FROM links
LEFT JOIN link_tags ON links.id = link_tags.link_id
LEFT JOIN tags ON link_tags.tag_id = tags.id
GROUP BY links.id
ORDER BY links.id DESC
""")
rows = c.fetchall()

if rows:
    if rows:
        for row in rows:
            link_id, title, url, icon_url, is_favorite, tags_csv = row
            with st.expander(f"{title or url}"):
                st.write("🔗 [Open Link](%s)" % url)
                st.write("⭐ **Favorite:**", "Yes" if is_favorite else "No")
                st.write("🏷️ **Tags:**", tags_csv or "(none)")
                col1, col2 = st.columns(2)

                # Delete button
                if col1.button("❌ Delete", key=f"delete_{link_id}"):
                    c.execute("DELETE FROM link_tags WHERE link_id=?", (link_id,))
                    c.execute("DELETE FROM links WHERE id=?", (link_id,))
                    conn.commit()
                    st.success("Deleted successfully.")
                    st.rerun()

                # Edit button
                edit_clicked = col2.button("✏️ Edit", key=f"edit_{link_id}")

                if edit_clicked:
                    st.session_state[f"editing_{link_id}"] = True

                if st.session_state.get(f"editing_{link_id}", False):
                    # Fetch all existing tags to pick from
                    c.execute("SELECT name FROM tags ORDER BY name")
                    all_tags = [r[0] for r in c.fetchall()]

                    # Fetch current tags assigned to this link
                    c.execute("""
                    SELECT tags.name
                    FROM link_tags
                    JOIN tags ON link_tags.tag_id = tags.id
                    WHERE link_tags.link_id = ?
                    """, (link_id,))
                    current_tags = [r[0] for r in c.fetchall()]

                    # Edit form
                    with st.form(f"edit_form_{link_id}"):
                        new_title = st.text_input("Title", value=title or "")
                        new_url = st.text_input("URL", value=url)
                        new_icon_url = st.text_input("Icon URL (optional)", value=icon_url)
                        new_selected_tags = st.multiselect(
                            "Tags (select existing)",
                            options=all_tags,
                            default=current_tags
                        )
                        new_tags_input = st.text_input(
                            "New tags (comma separated)"
                        )
                        new_favorite = st.checkbox("Mark as favorite", value=bool(is_favorite))
                        save_button = st.form_submit_button("Save Changes")

                        if save_button:
                            if not new_url.strip():
                                st.error("URL is required.")
                            else:
                                # Update link info
                                c.execute(
                                    "UPDATE links SET title=?, url=?, icon_url=?, is_favorite=? WHERE id=?",
                                    (new_title.strip(), new_url.strip(), new_icon_url.strip(), int(new_favorite), link_id)
                                )

                                # Remove old tag associations
                                c.execute("DELETE FROM link_tags WHERE link_id=?", (link_id,))

                                # Combine selected + new tags
                                combined_tags = set(t.strip() for t in new_selected_tags)
                                if new_tags_input.strip():
                                    combined_tags.update(
                                        t.strip() for t in new_tags_input.split(",") if t.strip()
                                    )

                                # Re-insert associations
                                for tag in combined_tags:
                                    c.execute("INSERT OR IGNORE INTO tags (name) VALUES (?)", (tag,))
                                    c.execute("SELECT id FROM tags WHERE name=?", (tag,))
                                    tag_id = c.fetchone()[0]
                                    c.execute("INSERT INTO link_tags (link_id, tag_id) VALUES (?, ?)",
                                              (link_id, tag_id))

                                conn.commit()
                                st.success("Changes saved.")
                                st.session_state[f"editing_{link_id}"] = False
                                st.rerun()


else:
    st.info("No links saved yet.")


st.header("🏷️ Manage Tags")
# Add Tags independently
with st.form("add_tag_form"):
    new_tag_name = st.text_input("Add a new tag")
    add_tag = st.form_submit_button("Add Tag")
    if add_tag:
        if not new_tag_name.strip():
            st.error("Tag name cannot be empty.")
        else:
            try:
                c.execute("INSERT INTO tags (name) VALUES (?)", (new_tag_name.strip(),))
                conn.commit()
                st.success(f"Tag '{new_tag_name.strip()}' added.")
                st.rerun()
            except sqlite3.IntegrityError:
                st.error("A tag with this name already exists.")

# Fetch all tags
c.execute("""
SELECT tags.id, tags.name, COUNT(link_tags.tag_id) as usage_count
FROM tags
LEFT JOIN link_tags ON tags.id = link_tags.tag_id
GROUP BY tags.id
ORDER BY usage_count DESC, tags.name
""")

tags = c.fetchall()

if tags:
    for tag_id, tag_name, count in tags:
        col1, col2, col3, col4 = st.columns([3, 1, 1, 1])

        # Show tag name
        col1.write(f"**{tag_name}**")

        # Edit button
        if col2.button(f"Count: {count}", key=f"count_tag_{tag_id}"):
            pass

        # Edit button
        if col3.button("✏️ Edit", key=f"edit_tag_{tag_id}"):
            st.session_state[f"editing_tag_{tag_id}"] = True

        # Delete button
        if col4.button("❌ Delete", key=f"delete_tag_{tag_id}"):
            c.execute("DELETE FROM link_tags WHERE tag_id=?", (tag_id,))
            c.execute("DELETE FROM tags WHERE id=?", (tag_id,))
            conn.commit()
            st.success(f"Tag '{tag_name}' deleted.")
            st.rerun()

        # If editing, show input box
        if st.session_state.get(f"editing_tag_{tag_id}", False):
            with st.form(f"edit_tag_form_{tag_id}"):
                new_tag_name = st.text_input("New tag name", value=tag_name)
                save = st.form_submit_button("Save")
                cancel = st.form_submit_button("Cancel")
                if save:
                    try:
                        c.execute("UPDATE tags SET name=? WHERE id=?", (new_tag_name.strip(), tag_id))
                        conn.commit()
                        st.success("Tag renamed.")
                        st.session_state[f"editing_tag_{tag_id}"] = False
                        st.rerun()
                    except sqlite3.IntegrityError:
                        st.error("A tag with this name already exists.")
                if cancel:
                    st.session_state[f"editing_tag_{tag_id}"] = False
else:
    st.info("No tags available.")
