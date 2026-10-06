from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class JournalEntry(BaseModel):
    date: str
    account: str
    amount: float
    vendor: str = ""
    description: str = ""
    document_id: str = ""
    vat_rate: Optional[float] = None
    cost_center: str = ""


class Finding(BaseModel):
    severity: str
    title: str
    detail: str
    account: Optional[str] = None
    amount: Optional[float] = None


class AuditResult(BaseModel):
    overall_risk_score: int = Field(ge=0, le=100)
    total_entries: int
    findings: List[Finding]
    summary: str


def _is_duplicate_document(entries: List[JournalEntry]) -> Dict[str, Any]:
    seen: Dict[str, List[JournalEntry]] = {}
    for entry in entries:
        key = entry.document_id.strip()
        if key:
            seen.setdefault(key, []).append(entry)

    duplicates = []
    for document_id, items in seen.items():
        if len(items) > 1:
            duplicates.append((document_id, items))
    return {"duplicates": duplicates}


def _round_number_risk(entries: List[JournalEntry]) -> List[Finding]:
    findings = []
    for entry in entries:
        amount = abs(float(entry.amount))
        if amount >= 50000 and amount % 1000 == 0:
            findings.append(
                Finding(
                    severity="medium",
                    title="Stort rundt beløb",
                    detail=f"Beløbet {amount:,.2f} kr. på konto {entry.account} er et stort rundt tal, som ofte kræver ekstra kontrol.",
                    account=entry.account,
                    amount=amount,
                )
            )
    return findings


def _vat_checks(entries: List[JournalEntry]) -> List[Finding]:
    findings = []
    for entry in entries:
        if entry.amount == 0:
            continue
        if entry.vat_rate is not None and entry.vat_rate > 0 and entry.account.startswith("(" ):
            pass
        if entry.vat_rate is None and abs(entry.amount) >= 5000:
            findings.append(
                Finding(
                    severity="medium",
                    title="Manglende momsangivelse",
                    detail=f"Beløbet {entry.amount:,.2f} kr. på konto {entry.account} har ingen momsangivelse og bør kontrolleres.",
                    account=entry.account,
                    amount=float(entry.amount),
                )
            )
    return findings


def _suspicious_vendor(entries: List[JournalEntry]) -> List[Finding]:
    findings = []
    vendor_counts = {}
    for entry in entries:
        vendor = (entry.vendor or "").strip().lower()
        if vendor:
            vendor_counts[vendor] = vendor_counts.get(vendor, 0) + 1

    for entry in entries:
        vendor = (entry.vendor or "").strip().lower()
        if vendor and vendor_counts.get(vendor, 0) > 3:
            findings.append(
                Finding(
                    severity="low",
                    title="Gentagende leverandør",
                    detail=f"Leverandøren '{entry.vendor}' forekommer flere gange i journalen og bør verificeres for konsistent behandling.",
                    account=entry.account,
                    amount=float(entry.amount),
                )
            )
    return findings


def analyze_journal(entries: List[JournalEntry]) -> AuditResult:
    findings: List[Finding] = []

    duplicates = _is_duplicate_document(entries)
    for document_id, items in duplicates["duplicates"]:
        total = sum(abs(float(item.amount)) for item in items)
        findings.append(
            Finding(
                severity="high",
                title="Duplikat dokument",
                detail=f"Dokument '{document_id}' er registreret flere gange. Samlet værdi: {total:,.2f} kr.",
                amount=total,
            )
        )

    findings.extend(_round_number_risk(entries))
    findings.extend(_vat_checks(entries))
    findings.extend(_suspicious_vendor(entries))

    # Risk score based on number and severity of findings
    severity_weight = {"low": 10, "medium": 20, "high": 35}
    score = min(100, sum(severity_weight.get(f.severity, 10) for f in findings))

    summary = (
        f"Der blev analyseret {len(entries)} poster. "
        f"Der blev identificeret {len(findings)} potentielle revisionstemaer. "
        f"Generel risikoscore: {score}/100."
    )

    return AuditResult(
        overall_risk_score=score,
        total_entries=len(entries),
        findings=findings,
        summary=summary,
    )
