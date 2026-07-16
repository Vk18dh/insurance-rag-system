import subprocess
import sys

def main():
    print("Running integration check...")
    result = subprocess.run(
        [
            ".venv\\Scripts\\python.exe", 
            "phase2_part2_integration_check.py"
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace"
    )
    with open("integration_out_utf8.txt", "w", encoding="utf-8") as f:
        f.write(str(result.stdout or ""))
        if result.stderr:
            f.write("\n### STDERR ###\n")
            f.write(str(result.stderr))
    print("Done")

if __name__ == "__main__":
    main()
