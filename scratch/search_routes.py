import re

with open(r"c:\Users\Asus\Desktop\gooduse\start\app.py", "r", encoding="utf-8", errors="ignore") as f:
    content = f.read()

print("File size:", len(content))

routes = re.findall(r"@app\.route\([^)]+\)", content)
print("Found routes count:", len(routes))
for r in routes[:20]:
    print(r)

print("\nSearching for 'ppt' or 'outline' in app.py:")
for i, line in enumerate(content.splitlines()):
    if "ppt" in line.lower() or "outline" in line.lower() or "generate" in line.lower():
        print(f"Line {i+1}: {line}")
