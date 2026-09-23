import os
import glob
import re

docs_dir = 'docs'
all_mds = glob.glob(os.path.join(docs_dir, '*.md'))

candidates = [
    f for f in all_mds 
    if any(k in os.path.basename(f) for k in ['STAGE_', 'AUDIT_', 'VERIFICATION', 'PLAN.md'])
    and not f.endswith('06_IMPLEMENTATION_PLAN_FINAL.md')
]

# Specifically include the _AUDIT files, except the ones we just made
new_ones = ["COMPLETE_ARCHITECTURE_AUDIT.md", "COMPLETE_SYSTEM_AUDIT_REPORT.md", "DOCUMENTATION_CLEANUP_AUDIT.md", "REPOSITORY_CLEANUP_EXECUTION.md"]
audit_files = glob.glob(os.path.join(docs_dir, '*AUDIT.md'))
for f in audit_files:
    b = os.path.basename(f)
    if b not in new_ones and f not in candidates:
        candidates.append(f)

# Look for references across the whole repo
references = {}
for root, dirs, files in os.walk('.'):
    if '.git' in root or 'node_modules' in root or '.next' in root or 'venv' in root or '.pytest_cache' in root:
        continue
    for fname in files:
        if fname.endswith(('.py', '.md', '.ts', '.tsx', '.json', '.yml', '.yaml')):
            path = os.path.join(root, fname)
            try:
                with open(path, 'r', encoding='utf-8', errors='ignore') as f_read:
                    content = f_read.read()
                    for cand in candidates:
                        b = os.path.basename(cand)
                        if b in content and path != cand:
                            if b not in references:
                                references[b] = []
                            references[b].append(path)
            except:
                pass

with open('docs/DOCUMENTATION_CLEANUP_AUDIT.md', 'w') as out:
    out.write("# Documentation Cleanup Audit\n\n")
    out.write("| File | References | Action | Reason |\n")
    out.write("|---|---|---|---|\n")
    for cand in candidates:
        b = os.path.basename(cand)
        refs = references.get(b, [])
        action = "DELETE"
        reason = "Superseded by COMPLETE_SYSTEM_AUDIT_REPORT.md, no authoritative references found outside of itself."
        if len(refs) > 0:
            # check if referenced by PRD or TRD
            if any('01_PRD' in r or '02_TRD' in r for r in refs):
                action = "KEEP"
                reason = "Referenced by authoritative documentation (PRD/TRD)."
            else:
                action = "DELETE"
                reason = f"Only referenced by other temporary documents: {refs[:2]}"
                
        # Hard check for some things that might be authoritative
        if "FINAL_REQUIREMENTS_COMPLIANCE_MATRIX" in b:
            action = "KEEP"
            reason = "Preserving compliance matrix as a reference artifact just in case."
            
        out.write(f"| {b} | {len(refs)} | {action} | {reason} |\n")

print("Created DOCUMENTATION_CLEANUP_AUDIT.md")
