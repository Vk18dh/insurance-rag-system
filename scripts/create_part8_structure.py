import os

files = {
    r"phase2\agents\response_builder.py": '"""\nphase2.agents.response_builder\n\nEntry point for combining all intermediate agent outputs into a well-formatted FinalResponse.\n"""\n',
    r"phase2\services\response_composer.py": '"""\nphase2.services.response_composer\n\nTransforms objects into standard UI-agnostic Response payloads.\n"""\n',
    r"phase2\services\citation_service.py": '"""\nphase2.services.citation_service\n\nConstructs valid citations linking explicitly back to the original VerificationResult documents.\n"""\n',
    r"phase2\services\warning_service.py": '"""\nphase2.services.warning_service\n\nTransforms Agent exceptions, risks, and contradictions into user-facing Alert warnings.\n"""\n',
    r"phase2\services\explanation_formatter.py": '"""\nphase2.services.explanation_formatter\n\nFormats explanation payloads based on configuring markdown styles.\n"""\n',
    r"phase2\services\response_formatter.py": '"""\nphase2.services.response_formatter\n\nHandles natural language assembly and grammar configuration for the resulting components.\n"""\n',
    r"phase2\services\response_validator.py": '"""\nphase2.services.response_validator\n\nChecks internal logic preventing null fields or omitted citations.\n"""\n',
    r"phase2\models\final_response.py": '"""\nphase2.models.final_response\n\nDefines FinalResponse Pydantic boundaries.\n"""\n',
    r"phase2\models\response_section.py": '"""\nphase2.models.response_section\n\nDefines subsection structures tracking modular domain components.\n"""\n',
    r"phase2\models\citation.py": '"""\nphase2.models.citation\n\nDefines Citation and Reference schemas.\n"""\n',
    r"phase2\models\warning.py": '"""\nphase2.models.warning\n\nDefines user Warning structs tracking severity.\n"""\n',
    r"phase2\models\response_metadata.py": '"""\nphase2.models.response_metadata\n\nTracks agent latency, confidence, and system identifiers.\n"""\n',
    r"phase2\interfaces\response_builder_interface.py": '"""\nphase2.interfaces.response_builder_interface\n\nDefines base Abstract interfaces for all Response Builder components.\n"""\n',
    r"phase2\exceptions\response_exception.py": '"""\nphase2.exceptions.response_exception\n\nDefines boundaries for formatting and validation errors inside the composer limits.\n"""\n'
}

for path, content in files.items():
    full_path = os.path.join(r"c:\Users\dhyan\Desktop\majorcode", path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content)

print("Files created successfully.")
