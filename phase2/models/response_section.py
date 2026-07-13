"""
phase2.models.response_section

Defines subsection structures tracking modular domain components safely explicitly.
"""
from pydantic import BaseModel, Field

class ResponseSection(BaseModel):
    """
    A logical visual block representing specific modular chunks within the explanation body dynamically.
    """
    title: str = Field(..., description="Section heading string natively displayed on the UI.")
    content: str = Field(..., description="Markdown formatted block content for this isolated section safely accurately.")
