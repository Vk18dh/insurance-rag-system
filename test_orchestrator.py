import asyncio
from backend.app.dependencies.agents import get_agent_orchestrator

async def main():
    orchestrator = get_agent_orchestrator()
    result = await orchestrator.orchestrate('What is the death benefit of the LIC Bima Jyoti policy?', conversation_id='test-conv')
    print('ANSWER:', result.shared_context.final_response.direct_answer)

asyncio.run(main())
