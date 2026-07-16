import os
task_path = r"C:\Users\dhyan\.gemini\antigravity\brain\584ba751-5e43-46df-8a97-637351132281\task.md"

with open(task_path, "r", encoding="utf-8") as f:
    text = f.read()

text = text.replace(
    "## Stage 9 — Testing\n- [ ] Unit tests for services (Interpreter, Linker, Builder, Explanation)\n- [ ] Unit tests for agent\n- [ ] Fallback handling tests",
    "## Stage 9 — Testing\n- [x] Unit tests for services (Interpreter, Linker, Builder, Explanation)\n- [x] Unit tests for agent\n- [x] Fallback handling tests"
)

with open(task_path, "w", encoding="utf-8") as f:
    f.write(text)

print("Test tasks checked off")
