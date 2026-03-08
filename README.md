# Clinical Evidence Drift & Consensus Monitoring System

## Overview

Medical research is expanding rapidly, with thousands of new papers published every month. These studies are written in unstructured natural language, making it difficult for clinicians and researchers to quickly understand the overall scientific consensus.

This project presents an **AI-powered Clinical Evidence Monitoring System** that automatically analyzes medical research papers from PubMed and converts them into structured insights. The system detects research trends, identifies contradictions between studies, and visualizes scientific consensus through an interactive dashboard.

The platform uses **Amazon Bedrock (Claude 3)** to extract structured evidence from research abstracts and provide meaningful insights to users.

---

## Live Prototype

Dashboard:
http://clinical-evidence-dashboard.s3-website.ap-south-1.amazonaws.com/

---

## Key Features

* Search medical **condition and treatment pairs**
* Automatically fetch research papers from **PubMed**
* Extract structured evidence using **AI (Claude 3 via Amazon Bedrock)**
* Detect **supporting, contradicting, or neutral research**
* Compute **evidence stability and contradiction scores**
* Interactive dashboard with **visual research insights**

---

## Technology Stack

### Frontend

* HTML
* JavaScript
* Chart.js
* Static website hosted on Amazon S3

### Backend

* AWS Lambda
* Amazon API Gateway

### AI Layer

* Amazon Bedrock
* Claude 3 Haiku model

### Data Pipeline

* Amazon S3 – raw research storage
* Amazon DynamoDB – research metadata and evidence storage
* Amazon SQS – asynchronous AI processing pipeline

---

## System Architecture

High-level architecture flow:

User Dashboard
→ API Gateway
→ Clinical Query Lambda
→ PubMed Ingestion Lambda
→ PubMed API
→ S3 (Raw Research Storage)
→ SQS Processing Queue
→ Bedrock Processor Lambda
→ Amazon Bedrock (Claude 3)
→ DynamoDB (Structured Findings)
→ Evidence Scoring Lambda
→ Dashboard Analytics

---

## AI Layer Contribution

Traditional software cannot reliably interpret medical research abstracts written in natural language. The AI layer enables the system to:

* Understand complex medical research language
* Extract structured evidence from abstracts
* Identify treatment outcomes
* Detect contradictions between studies
* Estimate evidence strength
* Summarize scientific consensus across research papers

Amazon Bedrock (Claude 3) converts unstructured research abstracts into structured medical evidence used by the dashboard.

---

## Data Processing Pipeline

1. User searches for a **condition and treatment** in the dashboard.
2. API Gateway sends the request to the **Clinical Query Lambda**.
3. If research data does not exist, the **PubMed Ingestion Lambda** retrieves research papers.
4. Raw research XML is stored in **Amazon S3**.
5. Research metadata is stored in **DynamoDB (Findings Table)**.
6. Each research paper is sent to **Amazon SQS** for processing.
7. The **Bedrock Processor Lambda** sends abstracts to **Amazon Bedrock**.
8. AI extracts structured evidence including:

   * conclusion summary
   * direction of effect
   * confidence level
   * evidence strength score
9. Structured evidence is stored in **DynamoDB (StructuredFindings)**.
10. The **Clinical Scoring Lambda** calculates consensus metrics.
11. Results are visualized in the dashboard.

---

## Repository Structure

```
clinical-evidence-monitoring-system
│
├── frontend-dashboard
│   ├── index.html
│   ├── app.js
│   ├── styles.css
│
├── lambda-clinical-query
│   └── lambda_function.py
│
├── lambda-pubmed-ingest
│   └── lambda_function.py
│
├── lambda-bedrock-processor
│   └── lambda_function.py
│
├── lambda-clinical-scoring
│   └── lambda_function.py
│
├── architecture
│   └── architecture-diagram.png
│
├── requirements.md
│
└── README.md
```

---

## Example Query

Condition
Type 2 Diabetes

Treatment
Metformin

The system retrieves research papers and provides:

* evidence stability score
* supporting vs contradicting research
* AI-generated research summaries

---

## Future Improvements

* Evidence trend analysis over time
* Automatic detection of emerging medical consensus shifts
* Support for additional biomedical databases
* Improved clinical trial classification
* Advanced research recommendation engine

---

## Project Purpose

This system demonstrates how **AI can transform large volumes of scientific literature into structured, interpretable knowledge**, helping healthcare professionals quickly understand research trends and scientific consensus.

---

## Demo Video

[(https://drive.google.com/file/d/13_S9EbOBHWHVKbDnvuEGKuvVZ0xK_yfc/view?usp=sharing)]

---

## License

This project is for research and educational purposes.
