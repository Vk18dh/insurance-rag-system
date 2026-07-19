import sys
with open('backend_logs2.txt', 'r', encoding='utf-16le', errors='ignore') as f:
    lines = f.readlines()
# If utf-16 fails (if it was an ansi text), let's fall back to reading bytes directly and cleaning it
with open('backend_logs2.txt', 'rb') as f:
    text = f.read().decode('utf-16le', errors='ignore')
    if "ef6aff46-a323-43b2-86df-b42a8f83d057" not in text:
        text = open('backend_logs2.txt', 'r', encoding='utf-8', errors='ignore').read()

lines = text.split('\n')
target_id = "ef6aff46-a323-43b2-86df-b42a8f83d057"

transaction = []
recording = False
for line in lines:
    if target_id in line:
        recording = True
    if recording:
        transaction.append(line)
        # Assuming one request finishes within a reasonable time, or if we hit the end
        if "FinalAnswer:" in line or "Pipeline failed" in line or "Completed request" in line:
            recording = False

with open("transaction.txt", "w", encoding='utf-8') as tf:
    tf.write('\n'.join(transaction))
