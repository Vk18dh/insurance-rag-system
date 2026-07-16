import subprocess

def main():
    result = subprocess.run(
        [".venv\\Scripts\\python.exe", "phase2_e2e_pipeline_check.py"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace"
    )
    with open("e2e_out.txt", "w", encoding="utf-8") as f:
        f.write(result.stdout)
        if result.stderr:
            f.write("\n### STDERR ###\n")
            f.write(result.stderr)
    print("Done")

if __name__ == "__main__":
    main()
