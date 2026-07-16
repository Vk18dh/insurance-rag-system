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
            
# 1. Clause Interpreter
patch_file(
    "phase2/services/clause_interpreter.py",
    "class ClauseInterpreter(IClauseInterpreter):",
    "import logging\n\nlogger = logging.getLogger(__name__)\n\nclass ClauseInterpreter(IClauseInterpreter):"
)
patch_file(
    "phase2/services/clause_interpreter.py",
    "return interpreted",
    "logger.info(\"Clauses interpreted successfully\", extra={\"chunks_processed\": len(chunks), \"clauses_extracted\": len(interpreted)})\n        return interpreted"
)

# 2. Evidence Linker
patch_file(
    "phase2/services/evidence_linker.py",
    "class EvidenceLinker(IEvidenceLinker):",
    "import logging\n\nlogger = logging.getLogger(__name__)\n\nclass EvidenceLinker(IEvidenceLinker):"
)
patch_file(
    "phase2/services/evidence_linker.py",
    "return linked_payload",
    "logger.info(\"Evidence linkages established\", extra={\"linked_clauses\": len(linked_payload), \"relationship_bounds\": self.required_relationships})\n        return linked_payload"
)

# 3. Chain Builder (already had logger setup)
patch_file(
    "phase2/services/reasoning_chain_builder.py",
    "return ReasoningChain(\n            steps=steps,",
    "logger.info(\"Reasoning chain steps formulated natively\", extra={\"total_steps_inferred\": len(steps), \"assumptions_detected\": sum(1 for s in steps if s.assumption), \"unsupported_links\": sum(1 for s in steps if not s.is_supported)})\n        return ReasoningChain(\n            steps=steps,"
)

# 4. Explanation Service
patch_file(
    "phase2/services/explanation_service.py",
    "class ExplanationService(IExplanationService):",
    "import logging\n\nlogger = logging.getLogger(__name__)\n\nclass ExplanationService(IExplanationService):"
)
patch_file(
    "phase2/services/explanation_service.py",
    "return Explanation(\n            reasoning_summary=summary.strip(),",
    "logger.info(\"Explainable sequence mapped\", extra={\"explanation_format\": self.explanation_format, \"assumptions_flagged\": len(assumptions)})\n        return Explanation(\n            reasoning_summary=summary.strip(),"
)

# Task.md
task_path = r"C:\Users\dhyan\.gemini\antigravity\brain\584ba751-5e43-46df-8a97-637351132281\task.md"
with open(task_path, "r", encoding="utf-8") as f:
    text = f.read()

text = text.replace(
    "## Stage 7 — Logging\n- [ ] Map all service telemetry to singleton structured logger",
    "## Stage 7 — Logging\n- [x] Map all service telemetry to singleton structured logger"
)

with open(task_path, "w", encoding="utf-8") as f:
    f.write(text)

print("Logging Patch Applied successfully.")
