# PolicyOracle - AI Powered Insurance Claim Intelligence
PolicyOracle is an advanced RAG (Retrieval-Augmented Generation) framework designed to automate the lifecycle of insurance claim processing—from raw data ingestion to final audit reporting.

## Problem Statement: 
Traditional insurance claim processing in the finance and banking sectors is often hindered by extreme complexity and massive volumes of unstructured data. These manual workflows are notoriously time-consuming and prone to human error, directly impacting operational costs, regulatory compliance, and customer trust.

## Solution: 
PolicyOracle addresses these challenges by providing a seamless, automated claims processing pipeline. It leverages advanced Generative AI to extract critical information from policy documents, analyze claim validity, and generate accurate settlement recommendations. By automating these complex workflows, PolicyOracle significantly reduces manual effort, ensures consistency, and maintains high standards of regulatory compliance.

## Features: 
- Policy Document Analysis: Extracts relevant information from policy documents using advanced AI algorithms.
- Claim Analysis: Analyzes claims and provides accurate settlement recommendations.
- Streamlined Workflow: Streamlines the claims process, reduces manual effort, and ensures consistent and reliable claim settlements.

## Architecture:
```mermaid
graph TD
%% Global Settings
accTitle: AI Insurance Claims Flow Chart with FAISS
accDescr: Updated flow chart utilizing FAISS as the local vector database for RAG.

%% Data Processing & Storage Branch
Dataset[("<b>Dataset</b><br/>Policies, Claims,<br/>Regulations")] --> EDA
EDA{{"<b>EDA</b><br/>Anomalies Detection"}} --> Embeddings
Embeddings["<b>Embeddings</b><br/>Semantic Vectorization"] --> FAISS

subgraph Storage ["Knowledge Base"]
    FAISS[("<b>FAISS Index</b><br/>Local Vector Storage<br/>(Similarity Search)")]
end

%% User Input Branch
User_Query(["<b>User Inquiry</b><br/>Claim Details"]) --> API
API[["<b>API Gateway</b><br/>FastAPI Entry"]]

%% Main Logic Container
subgraph Processing_Logic ["LLM Orchestration (LangChain)"]
    direction TB
    
    API --> Retriever
    FAISS -.->|Vector Search| Retriever
    
    Retriever["<b>Retriever</b><br/>Context Fetching"] --> Prompt_Template
    Prompt_Template["<b>Prompt Engine</b><br/>Context Injection"] --> LLM_Chain
    
    LLM_Provider(["<b>Groq AI</b>"]) -.-> LLM_Chain
    LLM_Chain["<b>LangChain</b><br/>Fraud & Coverage Eval"] --> Output_Parsing
    Output_Parsing["<b>Output Parser</b><br/>Structured Insights"]
end

%% Final Output
Output_Parsing --> Final_Report[/<b>Final Audit Report</b><br/>Settlement Decision/]

%% Styling and Aesthetics for High Visibility
classDef default font-family:Arial,font-size:14px,stroke-width:2px;

%% Specific Colors
classDef data fill:#082f49,stroke:#0ea5e9,stroke-width:2px,color:#f0f9ff;
classDef vdb fill:#1e1b4b,stroke:#6366f1,stroke-width:3px,color:#e0e7ff;
classDef input fill:#451a03,stroke:#f59e0b,stroke-width:2px,color:#fffbeb;
classDef logic fill:#2e1065,stroke:#8b5cf6,stroke-width:2px,color:#f5f3ff;
classDef external fill:#0f172a,stroke:#94a3b8,stroke-width:1px,stroke-dasharray: 5 5,color:#cbd5e1;
classDef output fill:#064e3b,stroke:#10b981,stroke-width:2px,color:#ecfdf5;

%% Apply Classes
class Dataset,EDA,Embeddings data;
class FAISS vdb;
class User_Query,API input;
class Prompt_Template,LLM_Chain,Output_Parsing,Retriever logic;
class LLM_Provider external;
class Final_Report output;

%% Subgraph and Global Arrow Styling
style Processing_Logic fill:#020617,stroke:#8b5cf6,stroke-width:2px,stroke-dasharray: 8 4,color:#8b5cf6;
style Storage fill:#0f172a,stroke:#6366f1,stroke-width:2px,color:#6366f1;

%% Optimized arrow visibility
linkStyle default stroke:#94a3b8,stroke-width:2px;
linkStyle 3,5 stroke:#6366f1,stroke-width:3px,stroke-dasharray: 5 5;
```

### 🛠 Workflow Deep Dive

#### 🛰 1. Data Ingestion & EDA
PolicyOracle aggregates customer, medical, and regulatory datasets, performing automated **Exploratory Data Analysis (EDA)** to validate integrity and identify anomalies. This ensures the AI operates on high-context, verified, and clean data.

#### 🧬 2. Embedding & Local Storage (FAISS)
Textual data is converted into high-dimensional **Vector Embeddings** to capture complex semantic nuances. These vectors are indexed in a local **FAISS (Facebook AI Similarity Search)** database, creating a high-performance knowledge base for similarity-based retrieval.

#### 🧠 3. LangChain Retrieval & Orchestration
When a user submits a claim via the **FastAPI Gateway**, the system triggers a **LangChain Retriever**. This component performs a vector search against the FAISS index to fetch the most relevant policy context. High-performance **Groq AI** LLMs then evaluate the claim using:
*   **Contextual Reasoning**: Merging user queries with fetched policy snippets.
*   **Fraud Detection**: Identifying inconsistent patterns across dataset history.
*   **Coverage Verification**: Automatically mapping claims to specific policy limits and terms.

#### 📝 4. Structured Parsing & Final Reporting
The raw LLM output is refined through **Structured Parsing** (Pydantic validation) to ensure actionable insights and zero-hallucination results. This culminates in a **Final Audit Report** with automated settlement decisions, drastically reducing total processing time.
