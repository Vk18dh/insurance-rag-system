import subprocess
import json

try:
    # Run pytest and capture output natively in Python
    result = subprocess.run(
        ["python", "-m", "pytest", "backend/app/tests/"], 
        capture_output=True, 
        text=True
    )
    
    # Process output for errors
    issues = set()
    for i, line in enumerate(result.stdout.split('\n') + result.stderr.split('\n')):
        if "ERROR:" in line or "FAIL" in line or "Error" in line or "Exception" in line:
            issues.add(line.strip())
            
    with open("short_out.json", "w") as f:
        json.dump({
            "exit_code": result.returncode,
            "issues": list(issues)[:15],
            "raw_tail": "\\n".join((result.stdout + result.stderr).split("\\n")[-20:])
        }, f, indent=2)
except Exception as e:
    with open("short_out.json", "w") as f:
        json.dump([str(e)], f)
