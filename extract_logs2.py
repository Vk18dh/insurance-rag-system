import sys
with open('backend_logs_post.txt', 'r', encoding='utf-8', errors='ignore') as f:
    text = f.read()

# Grab the last "=== NEW QUERY ===" or something
lines = text.split('\n')
transaction = []
recording = False
for line in lines:
    if "Received query request" in line:
        transaction = []
        recording = True
    if recording:
        transaction.append(line)

with open("transaction2.txt", "w", encoding='utf-8') as tf:
    tf.write('\n'.join(transaction))
