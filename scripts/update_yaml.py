import os

config_append = """
response_builder:
  fallback_explanation: "Unable to trace logical limits firmly enough to provide a certain explanation."
  fallback_answer: "Insufficient verified context available to answer accurately."
  timeout_seconds: 2.0
  retry_policy: 1
  language_options:
    - "en"
"""
with open(r"c:\Users\dhyan\Desktop\majorcode\phase2_config.yaml", "a", encoding="utf-8") as f:
    f.write(config_append)

print("YAML appended successfully.")
