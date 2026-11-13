"""Groq initialization and structured outputs from the notebook."""

from dotenv import load_dotenv
from langchain_groq import ChatGroq

from .schemas import ComparisonResult, JobDescriptionData, ResumeSections

load_dotenv()

llm = ChatGroq(
    model="openai/gpt-oss-20b",
    temperature=0,
    max_tokens=16384,
    reasoning_effort="low"
)

resume_llm = llm.with_structured_output(
    ResumeSections,
    method="json_schema",
    strict=False
)

jd_llm = llm.with_structured_output(
    JobDescriptionData,
    method="json_schema",
    strict=True
)

structured_compare_llm = llm.with_structured_output(
    ComparisonResult,
    method="json_schema",
    strict=True
)
