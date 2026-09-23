import os
import sys
from dotenv import load_dotenv

load_dotenv()

# Add project root to PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__))))

from backend.app.dependencies.agents import get_agent_orchestrator

def main():
    print("Loading Orchestrator...")
    orchestrator = get_agent_orchestrator()
    print("Orchestrator loaded successfully.")
    
    # Just to verify timeouts, let's print the actual values from settings
    print(f"agent_timeout_ms = {orchestrator._execution_manager._timeout_ms}")
    print(f"max_workflow_timeout_ms = {orchestrator._workflow_timeout_ms}")
    
    query = "Does LIC Bima Jyoti cover alien abduction?"
    print("\nExecuting query:")
    print(query)
    
    import time
    start = time.time()
    try:
        result = orchestrator.orchestrate(query, conversation_id="test-conversation-123")
        elapsed = time.time() - start
        
        print(f"\nExecution completed in {elapsed:.2f}s")
        print(f"Status: {result.overall_status}")
        print(f"Errors: {result.errors}")
        print(f"Warnings: {result.warnings}")
        if result.shared_context and result.shared_context.final_response:
            print(f"Response: {result.shared_context.final_response.direct_answer}")
    except Exception as e:
        print(f"\nExecution failed with exception: {e}")

if __name__ == "__main__":
    main()
