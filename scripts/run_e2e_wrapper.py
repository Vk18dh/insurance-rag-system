import subprocess

result = subprocess.run(
    [".venv\\Scripts\\python.exe", "run_pipeline_part4.py"],
    capture_output=True,
    text=True,
    encoding="utf-8"
)
with open("e2e_out.txt", "w", encoding="utf-8") as f:
    f.write(result.stdout)
    if result.stderr:
        f.write("\n\n### STDERR ###\n\n")
        f.write(result.stderr)
print("Saved")
