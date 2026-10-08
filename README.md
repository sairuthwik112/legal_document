# AI-Powered Legal Document Review

A small command-line workflow that reviews a text-based legal PDF using
Microsoft Foundry agents and local retrieval-augmented generation (RAG).

The application:

1. Extracts contract text and page numbers locally.
2. Invokes the existing Microsoft Foundry Clause Extraction Agent.
3. Chunks the five local policy PDFs.
4. Uses the deployed Foundry embedding model to retrieve relevant policy
   passages for every extracted clause.
5. Sends the clauses and retrieved source passages to the existing Compliance
   Validation Agent.
6. Writes a grounded JSON report.

The application does not require Foundry IQ or Azure AI Search. The Compliance
Validation Agent must not have the inaccessible knowledge-base tool attached.

> This is an AI-assisted preliminary document review. Final legal decisions
> must be made by an authorized legal professional.

## Repository structure

```text
legal_document/
|-- data/
|   |-- contracts/
|   |   `-- sample-vendor-agreement.pdf
|   `-- knowledge_base/
|       |-- approved-contract-template.pdf
|       |-- data-privacy-requirements.pdf
|       |-- information-security-policy.pdf
|       |-- legal-compliance-guidelines.pdf
|       `-- vendor-contract-policy.pdf
|-- orchestration/
|   |-- __init__.py
|   `-- workflow.py
|-- rag/
|   |-- __init__.py
|   `-- local_retrieval.py
|-- scripts/
|   `-- generate_sample_documents.py
|-- tests/
|   `-- test_workflow.py
|-- memory/                  # Generated report; JSON files are ignored by Git
|-- .env.example
|-- .gitignore
|-- requirements.txt
`-- README.md
```

## Required Foundry resources

The workflow expects these existing resources:

- Foundry project: `hakunamatata-new`
- Clause agent: `Clause-Extraction-Agent-sk`
- Compliance agent: `compliance-validation-agent-sk`
- Embedding deployment: `text-embedding-ada-002`

The agent names are case-sensitive.

## VM setup

### 1. Clone the repository

```powershell
git clone https://github.com/sairuthwik112/legal_document.git
Set-Location legal_document
```

### 2. Create a virtual environment

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### 3. Configure the project

Copy the example environment file:

```powershell
Copy-Item .env.example .env
```

Confirm that `.env` contains the correct project endpoint, agent names, and
embedding endpoint/deployment. Copy the Azure OpenAI key from the Foundry
project Models page into the private `.env` file:

```env
AZURE_AI_FOUNDRY_PROJECT_ENDPOINT=https://hakunamata.services.ai.azure.com/api/projects/hakunamatata-new
AZURE_OPENAI_ENDPOINT=https://hakunamata.openai.azure.com/openai/v1
AZURE_OPENAI_API_KEY=<current Azure OpenAI key>
CLAUSE_EXTRACTION_AGENT_NAME=Clause-Extraction-Agent-sk
COMPLIANCE_VALIDATION_AGENT_NAME=compliance-validation-agent-sk
AZURE_OPENAI_EMBEDDING_DEPLOYMENT=text-embedding-ada-002
```

Do not add secrets to `.env.example`. The private `.env` file is ignored by
Git. Rotate any key that has previously appeared in chat or screenshots before
using it.

### 4. Authenticate

The `azure-ai-projects` SDK uses Microsoft Entra authentication for Foundry
agent access. Local RAG uses the direct Azure OpenAI v1 endpoint and API key
only for the embedding deployment.

On a development VM with Azure CLI:

```powershell
az login
az account show
```

Alternatively, run the VM with a managed identity that has permission to use
the Foundry project. `DefaultAzureCredential` automatically tries managed
identity and other supported Entra credentials.

### 5. Run the sample

```powershell
python -m orchestration.workflow
```

The report is written to:

```text
memory/latest-review.json
```

Review a different PDF:

```powershell
python -m orchestration.workflow C:\path\to\contract.pdf --output C:\path\to\review.json
```

Only text-based PDFs are supported. Scanned/image-only PDFs require OCR, which
is intentionally outside this simple project.

## Testing

```powershell
python -m pytest tests -q
python -m ruff check orchestration rag tests
```

The tests validate PDF extraction, page preservation, JSON parsing, policy PDF
loading, chunking, embedding result ordering, cosine similarity, and grounded
source retrieval without making live Azure calls.

## Synthetic data

All included PDFs are synthetic educational documents. Regenerate them with:

```powershell
python scripts\generate_sample_documents.py
```
