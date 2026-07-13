from enum import Enum

class ContradictionType(str, Enum):
    LOGICAL = "Logical"
    REGULATORY = "Regulatory"
    CLAUSE = "Clause"
    COVERAGE = "Coverage"
    ELIGIBILITY = "Eligibility"
    BENEFIT = "Benefit"
    EXCLUSION = "Exclusion"
