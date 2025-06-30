def get_html_text(links):
    html_text = '<div style="display: flex; gap: 30px; flex-wrap: wrap;">'
    for link in links:
        favorite_star = "⭐" if link["is_favorite"] else ""
        html_text += f"""
  <div style="
    text-align: center;
    border: 1px solid #ddd;
    border-radius: 8px;
    padding: 12px;
    width: 110px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    background-color: white;
">
    <a href="{link['url']}" target="_blank" style="text-decoration: none; color: black;">
      <img src="{link['icon_url'] or 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQO5kCepNdhZvDKJtmPAIWnloSdTal7N1CQaA&s'}" alt="{link['title']}" width="64" height="64" style="object-fit: contain; display: inline-block;">
      <div>{link['title']}</div>
      <div style="font-size:14px; color: #f39c12;">{favorite_star}</div>
    </a>
  </div>
"""
    html_text += """
</div>
"""
    return html_text


def get_links(conn, selected_tags):
    # --- Build query with optional filtering ---
    query = """
    SELECT 
        links.id,
        links.title,
        links.url,
        links.is_favorite,
        links.sort_order,
        links.icon_url,
        GROUP_CONCAT(tags.name, ', ')
    FROM links
    LEFT JOIN link_tags ON links.id = link_tags.link_id
    LEFT JOIN tags ON link_tags.tag_id = tags.id
    """
    params = []

    if selected_tags:
        placeholders = ",".join("?" * len(selected_tags))
        query += f"""
        WHERE links.id IN (
            SELECT link_id FROM link_tags
            JOIN tags ON link_tags.tag_id = tags.id
            WHERE tags.name IN ({placeholders})
            GROUP BY link_id
            HAVING COUNT(DISTINCT tags.name) = ?
        )
        """
        params = selected_tags + [len(selected_tags)]

    query += """
    GROUP BY links.id
    ORDER BY links.sort_order ASC, links.id DESC
    """

    conn.execute(query, params)
    rows = conn.fetchall()

    # --- Convert rows to dicts ---
    links = []
    for row in rows:
        link_id, title, url, is_favorite, sort_order, icon_url, tags_csv = row
        links.append({
            "id": link_id,
            "title": title,
            "url": url,
            "is_favorite": is_favorite,
            "icon_url": icon_url,
            "tags": tags_csv or "",
            "sort_order": sort_order
        })
    return links
