import sys
import types
dummy_vertexai = types.ModuleType('langchain_community.chat_models.vertexai')
dummy_vertexai.ChatVertexAI = type('ChatVertexAI', (object,), {})
sys.modules['langchain_community.chat_models.vertexai'] = dummy_vertexai

import ragas
from ragas import evaluate
print("SUCCESS!")
