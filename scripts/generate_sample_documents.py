"""
Generates the synthetic PDF documents used by this project:

- data/contracts/sample-vendor-agreement.pdf
- data/knowledge_base/vendor-contract-policy.pdf
- data/knowledge_base/data-privacy-requirements.pdf
- data/knowledge_base/information-security-policy.pdf
- data/knowledge_base/legal-compliance-guidelines.pdf
- data/knowledge_base/approved-contract-template.pdf

All documents are fictional and created only for this educational capstone
project. Every generated PDF is stamped with the disclaimer:

    "Synthetic educational document created for project demonstration."

Run with:
    python scripts/generate_sample_documents.py
"""

from pathlib import Path

from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

ROOT = Path(__file__).resolve().parent.parent
CONTRACTS_DIR = ROOT / "data" / "contracts"
KB_DIR = ROOT / "data" / "knowledge_base"

DISCLAIMER = "Synthetic educational document created for project demonstration."

styles = getSampleStyleSheet()
TITLE = ParagraphStyle("TitleStyle", parent=styles["Title"], fontSize=16, spaceAfter=10)
HEADING = ParagraphStyle("HeadingStyle", parent=styles["Heading2"], spaceBefore=14, spaceAfter=6)
BODY = ParagraphStyle("BodyStyle", parent=styles["BodyText"], spaceAfter=8, leading=14)
DISCLAIMER_STYLE = ParagraphStyle(
    "DisclaimerStyle",
    parent=styles["Italic"],
    fontSize=9,
    textColor="#b00020",
    spaceAfter=16,
)


def build_pdf(path: Path, title: str, sections: list[tuple[str, list[str]]]) -> None:
    """Build a simple PDF with a title, disclaimer banner, and headed sections."""
    path.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(
        str(path),
        pagesize=LETTER,
        topMargin=0.9 * inch,
        bottomMargin=0.9 * inch,
        leftMargin=0.9 * inch,
        rightMargin=0.9 * inch,
        title=title,
    )
    story = [
        Paragraph(title, TITLE),
        Paragraph(DISCLAIMER, DISCLAIMER_STYLE),
    ]
    for heading, paragraphs in sections:
        story.append(Paragraph(heading, HEADING))
        for para in paragraphs:
            story.append(Paragraph(para, BODY))
    story.append(Spacer(1, 12))
    story.append(Paragraph(DISCLAIMER, DISCLAIMER_STYLE))
    doc.build(story)
    print(f"Created: {path.relative_to(ROOT)}")


# ---------------------------------------------------------------------------
# 1. Sample contract to review
# ---------------------------------------------------------------------------
# Deliberately includes some complete clauses, one incomplete clause
# (Data Privacy), and some missing clauses (Information Security,
# Intellectual Property, Dispute Resolution) so the Clause Extraction and
# Compliance Validation agents have real scenarios to detect during testing.
CONTRACT_SECTIONS = [
    (
        "1. Parties",
        [
            "This Vendor Services Agreement (\u201cAgreement\u201d) is entered into between "
            "Northwind Trading Co. (\u201cClient\u201d), a company located at 100 Market Street, "
            "Springfield, and Blue Harbor Logistics LLC (\u201cVendor\u201d), a company located at "
            "22 Harbor Road, Rivertown, effective as of January 15, 2025."
        ],
    ),
    (
        "2. Scope of Work",
        [
            "Vendor shall provide warehousing, inventory management, and last-mile delivery "
            "services for Client's retail products as described in Exhibit A, including "
            "weekly inventory reconciliation reports."
        ],
    ),
    (
        "3. Payment Terms",
        [
            "Client shall pay Vendor a monthly service fee of $18,500, invoiced on the first "
            "business day of each month, payable within 30 days of receipt. Late payments "
            "accrue interest at 1.5% per month."
        ],
    ),
    (
        "4. Deliverables",
        [
            "Vendor shall deliver monthly performance reports, quarterly inventory audits, "
            "and an annual service review summary to Client's operations team."
        ],
    ),
    (
        "5. Confidentiality",
        [
            "Each party agrees to protect the other's confidential information using the "
            "same degree of care it uses for its own confidential information, and shall not "
            "disclose such information to third parties without prior written consent, for a "
            "period of three (3) years following termination of this Agreement."
        ],
    ),
    (
        "6. Data Privacy",
        [
            "Vendor will handle any personal data it encounters in connection with this "
            "Agreement appropriately."
        ],
    ),
    (
        "7. Liability",
        [
            "Vendor's total liability under this Agreement shall not exceed the total fees "
            "paid by Client in the twelve (12) months preceding the claim, except in cases of "
            "gross negligence or willful misconduct."
        ],
    ),
    (
        "8. Termination",
        [
            "Either party may terminate this Agreement for convenience with sixty (60) days "
            "written notice, or immediately upon a material breach that remains uncured for "
            "fifteen (15) days after written notice."
        ],
    ),
    (
        "9. Governing Law",
        [
            "This Agreement shall be governed by and construed in accordance with the laws "
            "of the State of Illinois, without regard to its conflict of laws principles."
        ],
    ),
]

# ---------------------------------------------------------------------------
# 2. Vendor contract policy (knowledge base)
# ---------------------------------------------------------------------------
VENDOR_POLICY_SECTIONS = [
    (
        "Purpose",
        [
            "This policy defines the clauses that must appear in every vendor services "
            "agreement before it may be approved by the Legal and Procurement teams."
        ],
    ),
    (
        "Mandatory Clauses",
        [
            "Every vendor contract must include, at minimum: Parties, Scope of Work, "
            "Payment Terms, Deliverables, Confidentiality, Data Privacy, Information "
            "Security, Liability, Intellectual Property, Termination, Governing Law, and "
            "Dispute Resolution."
        ],
    ),
    (
        "Payment Terms Requirements",
        [
            "Payment terms must specify the fee amount, invoicing cadence, payment due "
            "period (not to exceed 45 days), and any late payment interest rate."
        ],
    ),
    (
        "Termination Requirements",
        [
            "Contracts must allow termination for convenience with no more than 90 days "
            "notice and termination for cause with a cure period of no more than 30 days."
        ],
    ),
    (
        "Liability Requirements",
        [
            "Liability caps must be clearly stated and must carve out exceptions for gross "
            "negligence, willful misconduct, and breach of confidentiality obligations."
        ],
    ),
    (
        "Dispute Resolution Requirements",
        [
            "Contracts must specify a dispute resolution mechanism, such as mediation or "
            "binding arbitration, prior to litigation, including the venue and administering "
            "body."
        ],
    ),
    (
        "Intellectual Property Requirements",
        [
            "Contracts must state ownership of pre-existing intellectual property and any "
            "work product created during the engagement, including license grants if "
            "applicable."
        ],
    ),
]

# ---------------------------------------------------------------------------
# 3. Data privacy requirements (knowledge base)
# ---------------------------------------------------------------------------
DATA_PRIVACY_SECTIONS = [
    (
        "Purpose",
        [
            "This document defines the minimum data privacy requirements for any vendor "
            "that processes personal data on behalf of the company."
        ],
    ),
    (
        "Required Contractual Language",
        [
            "Vendor contracts must explicitly define: the categories of personal data "
            "processed, the purpose of processing, data retention periods, data subject "
            "rights handling procedures, and breach notification timelines (no later than "
            "72 hours after discovery)."
        ],
    ),
    (
        "Sub-processors",
        [
            "Any use of sub-processors to handle personal data must be disclosed and "
            "pre-approved in writing by the Client."
        ],
    ),
    (
        "Cross-Border Transfers",
        [
            "If personal data is transferred across borders, the contract must reference an "
            "approved transfer mechanism such as Standard Contractual Clauses."
        ],
    ),
    (
        "Non-Compliant Language",
        [
            "Generic statements such as 'Vendor will handle personal data appropriately' do "
            "not satisfy this policy and must be flagged as incomplete."
        ],
    ),
]

# ---------------------------------------------------------------------------
# 4. Information security policy (knowledge base)
# ---------------------------------------------------------------------------
INFOSEC_SECTIONS = [
    (
        "Purpose",
        [
            "This policy defines the information security obligations required in vendor "
            "contracts that involve access to company systems or data."
        ],
    ),
    (
        "Required Security Controls",
        [
            "Vendor contracts must require encryption of data at rest and in transit, "
            "role-based access controls, annual security assessments, and prompt "
            "notification of security incidents within 48 hours of discovery."
        ],
    ),
    (
        "Audit Rights",
        [
            "Client must retain the right to audit Vendor's security controls at least "
            "once per year, or upon reasonable suspicion of a security incident."
        ],
    ),
    (
        "Missing Clause Guidance",
        [
            "If a vendor contract does not contain an Information Security clause, it must "
            "be treated as non-compliant and flagged as high risk, since there is no "
            "contractual basis for enforcing security controls."
        ],
    ),
]

# ---------------------------------------------------------------------------
# 5. Legal compliance guidelines (knowledge base)
# ---------------------------------------------------------------------------
LEGAL_GUIDELINES_SECTIONS = [
    (
        "Purpose",
        [
            "This document provides general legal compliance guidance for reviewing "
            "vendor agreements."
        ],
    ),
    (
        "Governing Law",
        [
            "Contracts should specify a governing law consistent with the jurisdictions in "
            "which the company operates. Governing law clauses referencing an approved "
            "jurisdiction (for example, Illinois, Delaware, or New York) are considered "
            "compliant."
        ],
    ),
    (
        "Dispute Resolution",
        [
            "Company policy favors mediation followed by binding arbitration over direct "
            "litigation, in order to reduce legal costs and resolution time."
        ],
    ),
    (
        "Confidentiality Survival",
        [
            "Confidentiality obligations should survive termination of the agreement for a "
            "minimum of two years, and three years is preferred for sensitive engagements."
        ],
    ),
    (
        "Risk Rating Guidance",
        [
            "A missing mandatory clause should generally be rated as High risk. An "
            "incomplete or ambiguous clause should generally be rated as Medium risk, "
            "unless it relates to data privacy or security, in which case it should also be "
            "rated High risk."
        ],
    ),
]

# ---------------------------------------------------------------------------
# 6. Approved contract template (knowledge base)
# ---------------------------------------------------------------------------
TEMPLATE_SECTIONS = [
    (
        "Purpose",
        [
            "This is an approved contract template showing acceptable clause language for "
            "reference during compliance review. It is not a real contract."
        ],
    ),
    (
        "Sample Data Privacy Clause",
        [
            "\u201cVendor shall process personal data only for the purposes of providing the "
            "Services, shall retain personal data no longer than 24 months after "
            "termination, shall notify Client within 72 hours of any confirmed data breach, "
            "and shall not engage sub-processors without Client's prior written consent.\u201d"
        ],
    ),
    (
        "Sample Information Security Clause",
        [
            "\u201cVendor shall maintain industry-standard security controls, including "
            "encryption of data at rest and in transit, role-based access control, and "
            "annual third-party security assessments, and shall notify Client of any "
            "security incident within 48 hours of discovery.\u201d"
        ],
    ),
    (
        "Sample Dispute Resolution Clause",
        [
            "\u201cThe parties shall first attempt to resolve any dispute through good-faith "
            "mediation. If mediation fails within 30 days, the dispute shall be resolved by "
            "binding arbitration administered by the American Arbitration Association in "
            "the state of the Client's principal place of business.\u201d"
        ],
    ),
    (
        "Sample Intellectual Property Clause",
        [
            "\u201cEach party retains ownership of its pre-existing intellectual property. Any "
            "work product created specifically for Client under this Agreement shall be "
            "owned by Client upon full payment, subject to a limited license back to Vendor "
            "for internal business purposes.\u201d"
        ],
    ),
]


def main() -> None:
    build_pdf(
        CONTRACTS_DIR / "sample-vendor-agreement.pdf",
        "Sample Vendor Services Agreement",
        CONTRACT_SECTIONS,
    )
    build_pdf(
        KB_DIR / "vendor-contract-policy.pdf",
        "Vendor Contract Policy",
        VENDOR_POLICY_SECTIONS,
    )
    build_pdf(
        KB_DIR / "data-privacy-requirements.pdf",
        "Data Privacy Requirements",
        DATA_PRIVACY_SECTIONS,
    )
    build_pdf(
        KB_DIR / "information-security-policy.pdf",
        "Information Security Policy",
        INFOSEC_SECTIONS,
    )
    build_pdf(
        KB_DIR / "legal-compliance-guidelines.pdf",
        "Legal Compliance Guidelines",
        LEGAL_GUIDELINES_SECTIONS,
    )
    build_pdf(
        KB_DIR / "approved-contract-template.pdf",
        "Approved Contract Template",
        TEMPLATE_SECTIONS,
    )


if __name__ == "__main__":
    main()
