"""
phase2.models.citation

Defines Citation and Reference schemas natively.
"""
from typing import Optional
from pydantic import BaseModel, Field

class Citation(BaseModel):
    """
    Represents a specific structural citation linking generated claims back to explicitly retrieved policy evidence.
    """
    citation_id: str = Field(..., description="Unique inline reference ID mapping UI footnotes (e.g., [1]).")
    source_document: str = Field(..., description="The name of the source insurance document.")
    page_number: Optional[str] = Field(None, description="The page number or logical location in the source document.")
    clause_reference: Optional[str] = Field(None, description="Specific clause or section explicitly referenced natively.")
    snippet: Optional[str] = Field(None, description="A verifiable short extract from the document supporting the claim directly.")
