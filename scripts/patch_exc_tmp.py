import os

def patch_file(path, old, new):
    if not os.path.exists(path):
        return
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()
    if old in text:
        text = text.replace(old, new)
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)

# 1. Update exceptions/__init__.py
patch_file(
    "phase2/exceptions/__init__.py",
    "from phase2.exceptions.verification_exception import (",
    """from phase2.exceptions.reasoning_exception import (
    ReasoningException,
    InvalidVerificationException,
    ClauseInterpretationException,
    ExplanationException,
    ReasoningTimeoutException
)

from phase2.exceptions.verification_exception import ("""
)

patch_file(
    "phase2/exceptions/__init__.py",
    "    \"VerificationException\",",
    """    "VerificationException",
    
    # Part 4
    "ReasoningException",
    "InvalidVerificationException",
    "ClauseInterpretationException",
    "ExplanationException",
    "ReasoningTimeoutException","""
)

# 2. Update ReasoningAgent to use genuine Exceptions instead of ValueError
patch_file(
    "phase2/agents/reasoning_agent.py",
    "from phase2.models.reasoning_metrics import ReasoningMetrics\nfrom phase2.exceptions.handlers import safe_agent_call",
    "from phase2.models.reasoning_metrics import ReasoningMetrics\nfrom phase2.exceptions.handlers import safe_agent_call\nfrom phase2.exceptions.reasoning_exception import InvalidVerificationException"
)
patch_file(
    "phase2/agents/reasoning_agent.py",
    "raise ValueError(\"VerificationResult failed upstream constraints. Reasoning aborted.\")",
    "raise InvalidVerificationException(\"VerificationResult failed QA upstream constraints. Reasoning Sequence aborted directly.\")"
)

# 3. Update task.md
task_path = r"C:\Users\dhyan\.gemini\antigravity\brain\584ba751-5e43-46df-8a97-637351132281\task.md"
with open(task_path, "r", encoding="utf-8") as f:
    text = f.read()

text = text.replace(
    "## Stage 8 — Exception Handling\n- [ ] `reasoning_exception.py` with typed subclauses",
    "## Stage 8 — Exception Handling\n- [x] `reasoning_exception.py` with typed subclauses"
)

with open(task_path, "w", encoding="utf-8") as f:
    f.write(text)

print("Exception Patches applied.")
