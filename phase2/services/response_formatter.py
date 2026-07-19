"""
phase2.services.response_formatter

Constructs short form direct answers configuring zero-hallucination policies accurately efficiently securely securely.
"""
from phase2.interfaces.response_builder_interface import IResponseFormatter
from phase2.models.reasoning_result import ReasoningResult

class ResponseFormatter(IResponseFormatter):
    """
    Transfers reasoning conclusions securely smoothly handling fallbacks neutrally implicitly stably explicitly explicitly properly safely cleanly.
    """
    
    def __init__(self, fallback_answer: str, llm_analyzer=None):
        self._fallback_answer = fallback_answer
        self._llm_analyzer = llm_analyzer

    def format_answer(self, reasoning_result: ReasoningResult) -> str:
        if not reasoning_result or not getattr(reasoning_result, 'reasoning_chain', None):
            return self._fallback_answer
            
        if not reasoning_result.reasoning_chain.is_complete:
            return self._fallback_answer
            
        steps = reasoning_result.reasoning_chain.steps
        if not steps:
            return self._fallback_answer
            
        final_deduction = steps[-1].conclusion
        
        if self._llm_analyzer and hasattr(self._llm_analyzer, 'analyse_text'):
            prompt = f"""You are a professional Insurance AI Knowledge Assistant. 
Convert the following logical deduction into a highly detailed, professional conversational response. You MUST use the exact Markdown skeleton provided below.

CRITICAL RULE: If the Raw Deduction states 'I could not find this information in the provided documents.' (or substantially similar), you MUST IGNORE the markdown skeleton completely and output EXACTLY the phrase 'I could not find this information in the provided documents.' and nothing else.

Raw Deduction: {final_deduction}
Internal Logic Trace: {getattr(reasoning_result.explanation, 'reasoning_summary', '')}

REQUIRED MARKDOWN SKELETON:
### 🔎 Analysis
[Provide a clear, 2-to-3 sentence explanation summarizing the deduction]

### 💡 Policy Findings
* **Existence:** [Explain if the policy mentions the requested concept]
* **Details:** [State the explicit rules, or explicitly state if the details are missing/unavailable in the documents]

### 📝 Conclusion
[A polished final takeaway sentence]

Polished Conversational Markdown:"""
            try:
                synthetic_answer = self._llm_analyzer.analyse_text(prompt)
                if synthetic_answer and len(synthetic_answer) > 10:
                    return synthetic_answer
            except Exception as e:
                pass
                
        return final_deduction if final_deduction else self._fallback_answer
