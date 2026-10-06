from app.services.revision_ai import JournalEntry, analyze_journal


def test_duplicate_document_detection():
    entries = [
        JournalEntry(date="2024-09-03", account="1000", amount=25000, vendor="Nordic A/S", description="Indbetaling", document_id="INV-1001", vat_rate=25),
        JournalEntry(date="2024-09-03", account="1000", amount=25000, vendor="Nordic A/S", description="Indbetaling", document_id="INV-1001", vat_rate=25),
    ]

    result = analyze_journal(entries)
    assert result.overall_risk_score >= 30
    assert any("Duplikat dokument" in finding.title for finding in result.findings)


def test_round_amount_risk():
    entries = [
        JournalEntry(date="2024-09-04", account="6210", amount=125000, vendor="Mærsk", description="Feriepenge", document_id="DOC-995", vat_rate=0),
    ]

    result = analyze_journal(entries)
    assert any("Stort rundt beløb" in finding.title for finding in result.findings)
