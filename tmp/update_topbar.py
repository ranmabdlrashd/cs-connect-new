import os
import glob
import re

html_files = glob.glob(r"c:\Users\LENOVO\Desktop\Mini project\cs_connect\templates\**\*.html", recursive=True)

pattern = re.compile(r'[ \t]*<div class="dash-top-actions">\s*<div style="width:32px; height:32px; background:#F4F1EA; border-radius:50%; display:flex; align-items:center; justify-content:center; border:1px solid #E0DBCF; cursor:pointer;">\s*<i data-lucide="bell" style="width:16px; height:16px; color:var\(--accent-crimson\);"></i>\s*<\/div>\s*<\/div>', re.MULTILINE)

new_text = "      {% include 'partials/topbar_actions.html' %}"

count = 0
for filepath in html_files:
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    
    if pattern.search(content):
        new_content = pattern.sub(new_text, content)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(new_content)
        print(f"Updated {filepath}")
        count += 1

print(f"Total updated: {count}")
