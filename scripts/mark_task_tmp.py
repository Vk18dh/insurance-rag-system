import os

task_path = r"C:\Users\dhyan\.gemini\antigravity\brain\584ba751-5e43-46df-8a97-637351132281\task.md"

with open(task_path, "r", encoding="utf-8") as f:
    text = f.read()

text = text.replace("## Stage 6 — Configuration\n- [ ] Update `Phase2Settings` (`settings.py`)\n- [ ] Update `phase2_config.yaml`", "## Stage 6 — Configuration\n- [x] Update `Phase2Settings` (`settings.py`)\n- [x] Update `phase2_config.yaml`")

with open(task_path, "w", encoding="utf-8") as f:
    f.write(text)

print("Updated Task.md")
