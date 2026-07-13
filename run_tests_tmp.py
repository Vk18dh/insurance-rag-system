import subprocess
import sys

def main():
    print("Running pytest...")
    result = subprocess.run(
        [
            ".venv\\Scripts\\pytest.exe", 
            "--color=no",
            "-q",
            "phase2/tests/test_ranking.py", 
            "phase2/tests/test_validation.py", 
            "phase2/tests/test_retrieval_agent.py", 
        ],
        capture_output=True,
        text=True,
        encoding="utf-8"
    )
    with open("pytest_out_utf8.txt", "w", encoding="utf-8") as f:
        f.write(result.stdout)
        if result.stderr:
            f.write("\n### STDERR ###\n")
            f.write(result.stderr)
    print("Done")

if __name__ == "__main__":
    main()
