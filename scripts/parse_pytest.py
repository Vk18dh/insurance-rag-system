import json

try:
    with open("pytest_out.txt", "r", encoding="utf-16le") as f:
        text = f.read()
    
    issues = set()
    for i, line in enumerate(text.split('\n')):
        if "ERROR" in line or "FAIL" in line or "Error" in line or "Exception" in line:
            issues.add(line.strip())
            
    with open("short_out.json", "w") as f:
        json.dump(list(issues), f, indent=2)
except Exception as e:
    with open("short_out.json", "w") as f:
        json.dump([str(e)], f)
