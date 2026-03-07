with open('app.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    # Only replace '?' in actual SQL query strings, excluding the docstring with '?search='
    if '?' in line:
        if 'SELECT' in line or 'INSERT' in line or 'UPDATE' in line or 'DELETE' in line or 'query +=' in line:
            lines[i] = line.replace('?', '%s')
        elif 'query +=' in line or 'conn.execute' in line or 'cursor.execute' in line:
            lines[i] = line.replace('?', '%s')

with open('app.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)
    
print("Replaced all remaining ? with %s")
