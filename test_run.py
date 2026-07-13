import subprocess
r = subprocess.run(['pytest', 'phase2/tests/test_response_builder.py', '-v'], capture_output=True, text=True)
with open('pytest_out_8.txt', 'w', encoding='utf-8') as f:
    f.write(r.stdout)
    f.write(r.stderr)
