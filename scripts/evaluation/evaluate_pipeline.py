"""
Offline Evaluation Pipeline using Ragas.
Hits the locally running FastAPI instance to collect answers and retrieved contexts, 
then runs mathematical assessment for Faithfulness, Relevance, and Precision.
"""

import sys
import types

# Create dummy modules for the Ragas VertexAI legacy import bug
dummy_vertexai = types.ModuleType('langchain_community.chat_models.vertexai')
dummy_vertexai.ChatVertexAI = type('ChatVertexAI', (object,), {})
sys.modules['langchain_community.chat_models.vertexai'] = dummy_vertexai

import json
import urllib.request
import os
from dotenv import load_dotenv
load_dotenv(dotenv_path=".env")
os.environ["OPENAI_API_KEY"] = os.environ.get("OPENROUTER_API_KEY", "mock-key")

import pandas as pd
from datasets import Dataset
from ragas import evaluate
from ragas.metrics import (
    faithfulness,
    answer_relevancy,
    context_precision,
    context_recall
)
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_openai import ChatOpenAI
import os

def load_golden_dataset(path="scripts/evaluation/test_dataset.json"):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def run_evaluation():
    dataset = load_golden_dataset()
    
    questions = []
    answers = []
    contexts = []
    ground_truths = []
    
    api_url = "http://localhost:8000/api/v1/query"
    auth_url = "http://localhost:8000/api/v1/auth/login"
    
    # 1. Login to get token
    import urllib.parse
    auth_data = urllib.parse.urlencode({"username": "guest", "password": "guest_password"}).encode("utf-8")
    try:
        auth_req = urllib.request.Request(auth_url, data=auth_data)
        auth_resp = urllib.request.urlopen(auth_req)
        token_data = json.loads(auth_resp.read())
        token = token_data.get("access_token")
    except Exception as e:
        # If guest doesn't exist, try to register it
        try:
            reg_url = "http://localhost:8000/api/v1/auth/register"
            reg_data = json.dumps({
                "username": "guest", "password": "guest_password",
                "email": "guest@example.com", "full_name": "Guest", "role": "user"
            }).encode("utf-8")
            reg_req = urllib.request.Request(reg_url, data=reg_data, headers={"Content-Type": "application/json"})
            urllib.request.urlopen(reg_req)
            # Try login again
            auth_req = urllib.request.Request(auth_url, data=auth_data)
            auth_resp = urllib.request.urlopen(auth_req)
            token_data = json.loads(auth_resp.read())
            token = token_data.get("access_token")
        except Exception as e2:
            print(f"Failed to authenticate: {e2}")
            return
    
    print(f"Running {len(dataset)} evaluations against {api_url}...\n")
    
    for item in dataset:
        q = item["question"]
        print(f"Testing Query: {q}")
        
        # Prepare API Call
        payload = json.dumps({"query": q}).encode("utf-8")
        req = urllib.request.Request(
            api_url, 
            data=payload, 
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {token}"}
        )
        
        try:
            resp = urllib.request.urlopen(req)
            d = json.loads(resp.read())
            
            final_answer = d.get("final_answer", "")
            
            # Extract texts from retrieved sources
            sources = d.get("sources", [])
            retrieved_texts = [s.get("content_snippet", "") for s in sources]
            
            # Ragas expects context to not be completely empty list if ground_truth expects something
            # So if nothing is retrieved we pass empty string array
            if not retrieved_texts:
                retrieved_texts = [""]
                
            questions.append(q)
            answers.append(final_answer)
            contexts.append(retrieved_texts)
            ground_truths.append(item["ground_truth"])
            
            print(f"✅ Received Answer (Conf: {d.get('confidence_score', 0)})")
            
        except Exception as e:
            print(f"❌ Failed to reach API for query: {q}. Error: {e}")
            return
            
    # Compile HuggingFace Dataset
    print("\nCompiling Dataset for Ragas Metrics...")
    data_dict = {
        "question": questions,
        "answer": answers,
        "contexts": contexts,
        "ground_truth": ground_truths
    }
    
    hf_dataset = Dataset.from_dict(data_dict)
    
    print("Initiating Ragas Evaluation (this may take a minute)...")
    
    # Ragas will automatically use environment variables for OpenAI/Anthropic/Google keys
    # Let's import the load_dotenv to pull the OPENROUTER_API_KEY from .env
    from dotenv import load_dotenv
    load_dotenv(dotenv_path=".env")
    
    # Ragas locally checks this env variable during import and execution! 
    # Must map the OpenRouter key to it explicitly before processing.
    os.environ["OPENAI_API_KEY"] = os.environ.get("OPENROUTER_API_KEY", "mock-key")
    os.environ["OPENAI_BASE_URL"] = "https://openrouter.ai/api/v1"
    
    try:
        # Use Local Ollama model to bypass all API rate limits!
        evaluator_llm = ChatOpenAI(
            model_name="qwen2.5:3b",
            openai_api_key="ollama",
            openai_api_base="http://localhost:11434/v1"
        )
        
        # OpenRouter DOES NOT support embeddings. We must use a free local model to do the vector math!
        print("Loading local embedding model for Ragas vector math...")
        evaluator_embeddings = HuggingFaceEmbeddings(model_name="BAAI/bge-small-en-v1.5")
        
        # Explicitly wire each individual metric to Google AI Studio to prevent Ragas from falling back to OpenRouter
        metrics_list = [
            context_precision,
            context_recall,
            faithfulness,
            answer_relevancy,
        ]
        for m in metrics_list:
            m.llm = evaluator_llm
            if hasattr(m, 'embeddings'):
                m.embeddings = evaluator_embeddings
                
        result = evaluate(
            dataset=hf_dataset,
            metrics=metrics_list,
            raise_exceptions=False
        )
        
        print("\n=== EVALUATION RESULTS ===")
        print(result)
        
        # Export
        df = result.to_pandas()
        os.makedirs("scripts/evaluation/reports", exist_ok=True)
        df.to_csv("scripts/evaluation/reports/ragas_scorecard.csv", index=False)
        print("\nScorecard saved to scripts/evaluation/reports/ragas_scorecard.csv")
        
    except Exception as e:
        import traceback
        print(f"\nRagas Evaluation Exception: {e}")
        traceback.print_exc()
        print("Note: Ragas typically requires OPENAI_API_KEY for embedding limits implicitly unless OpenAI is mocked or explicitly mapped.")

if __name__ == "__main__":
    run_evaluation()
