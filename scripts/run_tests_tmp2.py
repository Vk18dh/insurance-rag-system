import subprocess

def main():
    result = subprocess.run(
        [
            ".venv\\Scripts\\pytest.exe", 
            "phase2/tests/test_query_processing.py",
            "phase2/tests/test_query_agent.py",
            "-v"
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace"
    )
    with open("test_out.txt", "w", encoding="utf-8") as f:
        f.write(result.stdout)
        if result.stderr:
            f.write("\n### STDERR ###\n")
            f.write(result.stderr)
    print("Done")

if __name__ == "__main__":
    main()
