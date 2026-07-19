import sys

target_id = "168acbbc-5e3e-41d1-9c92-0da2bdf8ea2c"
with open('full_backend.log', 'r', encoding='utf-8', errors='ignore') as f:
    lines = f.readlines()

output = []
for line in lines:
    if target_id in line or "EVIDENCE_BLOCK" in line or "Raw Deduction" in line or "Top 5" in line:
        output.append(line.strip())

with open("debug_transaction.txt", "w", encoding='utf-8') as f:
    f.write('\n'.join(output))
