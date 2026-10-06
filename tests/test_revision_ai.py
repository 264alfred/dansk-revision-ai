from fastapi import FastAPI
from pydantic import BaseModel
from typing import List

from app.services.revision_ai import JournalEntry, analyze_journal

app = FastAPI(title="dansk-revision-ai", version="0.1.0")


class AuditRequest(BaseModel):
    journal: List[JournalEntry]


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "dansk-revision-ai"}


@app.post("/audit")
def audit_journal(request: AuditRequest):
    result = analyze_journal(request.journal)
    return result.model_dump()


@app.get("/")
def root():
    return {"message": "Velkommen til dansk-revision-ai"}
