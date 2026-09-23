"""
phase2.services.response_formatter

Constructs short form direct answers configuring zero-hallucination policies accurately efficiently securely securely.
"""
from typing import List
from phase2.interfaces.response_builder_interface import IResponseFormatter
from phase2.models.reasoning_result import ReasoningResult
from phase2.models.citation import Citation
import re

class ResponseFormatter(IResponseFormatter):
    """
    Transfers reasoning conclusions securely smoothly handling fallbacks neutrally implicitly stably explicitly explicitly properly safely cleanly.
    """
    
    def __init__(self, fallback_answer: str, llm_analyzer=None):
        self._fallback_answer = fallback_answer
        self._llm_analyzer = llm_analyzer

    def format_answer(self, reasoning_result: ReasoningResult, citations: List[Citation] = None) -> str:
        if not reasoning_result or not getattr(reasoning_result, 'reasoning_chain', None):
            return self._fallback_answer
            
        if not reasoning_result.reasoning_chain.is_complete:
            return self._fallback_answer
            
        steps = reasoning_result.reasoning_chain.steps
        if not steps:
            return self._fallback_answer
            
        final_deduction = steps[-1].conclusion
        
        if self._llm_analyzer and hasattr(self._llm_analyzer, 'analyse_text'):
            sources_text = ""
            valid_citation_ids = []
            if citations:
                sources_list = []
                for c in citations:
                    snippet = c.snippet.replace("\n", " ") if c.snippet else "No snippet available."
                    sources_list.append(f"{c.citation_id} {c.source_document} (Page {c.page_number}) - Snippet: {snippet}")
                    valid_citation_ids.append(c.citation_id)
                sources_text = "\n".join(sources_list)
            else:
                sources_text = "No sources available."
            
            prompt = f"""You are a premium, professional Insurance AI Knowledge Assistant. 
Convert the following logical deduction into a clear, professional conversational response. 

CRITICAL GROUNDING RULES:
1. ONLY state factual claims supported by the provided sources and internal logic trace.
2. DO NOT use parametric/world knowledge to fill missing evidence.
3. DO NOT infer unsupported policy facts.
4. DO NOT add surrounding factual context merely to make the response more complete.
5. If the upstream deduction is a refusal/clarification, preserve that behavior exactly. Do not transform a refusal into an informative factual answer.

Raw Deduction: {final_deduction}
Internal Logic Trace: {getattr(reasoning_result.explanation, 'reasoning_summary', '')}

Available Sources:
{sources_text}

INSTRUCTIONS:
1. Provide a highly readable answer elegantly formatted using Markdown. Use **bold text** for key terms, use bullet points for lists, and write in engaging paragraphs.
2. DO NOT use rigid headings like 'Analysis', 'Policy Findings', or 'Conclusion'.
3. DO NOT invent or fabricate any citations or numbers.
4. You MUST place the exact citation markers (e.g., [1], [2]) directly inline immediately after the factual claims they support.
5. DO NOT create a separate 'References' or 'Sources' list at the bottom of your response. The system will handle that automatically.

Polished Conversational Answer:"""
            try:
                synthetic_answer = self._llm_analyzer.analyse_text(prompt)
                if synthetic_answer and len(synthetic_answer) > 10:
                    # Post-Processing: Validate Citations
                    # Find all [N] references in the text.
                    matches = re.findall(r'\[\d+\]', synthetic_answer)
                    for match in set(matches):
                        if match not in valid_citation_ids:
                            # Safely remove hallucinated citations
                            synthetic_answer = synthetic_answer.replace(f" {match}", "")
                            synthetic_answer = synthetic_answer.replace(match, "")
                    return synthetic_answer.strip()
            except Exception as e:
                pass
                
        return final_deduction if final_deduction else self._fallback_answer
