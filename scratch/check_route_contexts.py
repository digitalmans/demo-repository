with open(r"c:\Users\Asus\Desktop\gooduse\start\app.py", "r", encoding="utf-8", errors="ignore") as f:
    lines = f.readlines()

def print_route(name):
    print(f"=== Route: {name} ===")
    found = False
    count = 0
    for i, line in enumerate(lines):
        if f"def {name}(" in line or found:
            found = True
            print(f"{i+1}: {line.strip()}")
            count += 1
            if "return render_template" in line or count > 30:
                found = False
                count = 0

print_route("qa_robot")
print_route("digital_human")
print_route("feature_experience")
print_route("settings")
print_route("qa_discussion")
print_route("user_profile_page")
