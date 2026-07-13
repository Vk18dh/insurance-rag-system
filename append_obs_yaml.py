with open('phase2_config.yaml', 'a', encoding='utf-8') as f:
    f.write("""
# ---------------------------------------------------------------------------
# Part 9 - Observability Layer
# ---------------------------------------------------------------------------
observability:
  enabled: true
  log_level: "INFO"
  log_dir: "logs"
  log_to_file: true
  log_to_console: true
  log_format: "json"
  audit_enabled: true
  audit_storage_backend: "json"
  audit_dir: "audit_logs"
  metrics_enabled: true
  tracing_enabled: true
  health_monitor_enabled: true
  alert_failure_rate_threshold: 0.3
  alert_avg_latency_ms_threshold: 5000.0
  query_hash_salt_env_var: "OBSERVABILITY_SALT"
  max_audit_retention_days: 30
""")
print("Observability YAML block appended.")
