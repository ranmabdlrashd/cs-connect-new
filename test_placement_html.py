import urllib.request
try:
    with urllib.request.urlopen("http://127.0.0.1:5000/placements") as response:
        html = response.read().decode('utf-8')
        print("CSS Link:", "placement.css" in html)
        print("CSS Link (Plural):", "placements.css" in html)
        print("JS Link:", "placement.js" in html)
        print("JS Link (Plural):", "placements.js" in html)
        # Find the line with the CSS link
        for line in html.split('\n'):
            if "placement" in line:
                print(line.strip())
except Exception as e:
    print(f"Error: {e}")
