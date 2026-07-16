import subprocess
import sys

def main():
    result = subprocess.run(
        [".venv\\Scripts\\python.exe", "-m", "pytest", "phase2/tests/test_reasoning_services.py", "phase2/tests/test_reasoning_agent.py"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace"
    )
    with open("test_out.txt", "w", encoding="utf-8") as f:
        f.write(result.stdout)
        if result.stderr:
            f.write("\n\n### STDERR ###\n\n")
            f.write(result.stderr)
    print("Done")

if __name__ == "__main__":
    main()
