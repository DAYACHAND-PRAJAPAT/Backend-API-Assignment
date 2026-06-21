# AI-Powered Transaction Processing Pipeline

An asynchronous backend processing engine designed to securely ingest, clean, programmatically audit, and intelligently summarize financial transaction data. This pipeline leverages an event-driven decoupled architecture to offload heavy programmatic calculations and network-bound LLM tasks away from the client-facing HTTP thread pool, ensuring resilient execution even under high dataset loads.

---

## 🏗️ System Architecture & Data Flow

The system is constructed with a decoupled containerized topology. The flow of information across application boundaries follows a predictable request-response lifecycle:

1. **Ingestion Layer**: A client pushes a raw `transactions.csv` multi-part form-data payload via an HTTP client to the FastAPI application gateway.
2. **Instant Response**: The API gateway validates the file format, saves the entry state as `pending` to the relational PostgreSQL ledger, ships the file payload to Redis, and returns an immediate status tracking token (`job_id`) back to the client in under 50ms.
3. **Queue Distribution**: Redis acts as the task broker, holding execution payloads in memory until an available worker thread consumes the job.
4. **Programmatic Pipeline (Celery Worker)**:
   - **Step A: Data Cleaning**: Parses the file bytes into a Pandas DataFrame, drops broken rows, strips malformed spaces, formats dates dynamically, and calculates standard currency codes.
   - **Step B: Anomaly Detection**: Runs programmatic filtering algorithms to instantly flag 3x median statistical outliers per account and cross-border domestic merchant billing currency mismatches.
5. **Generative Intelligence (Gemini Client)**:
   - **Step C: Batch Classification**: Gathers all rows marked as `Uncategorised`, compresses them into an indexed dictionary matrix, and fulfills the classifications using **exactly one batch call** via the official `google-genai` SDK and Gemini 1.5 Flash.
   - **Step D: Narrative Report Generation**: Summarizes total spent metrics, isolates top merchants, evaluates risk ratios, and writes a structural narrative JSON response.
6. **State Synchronization**: The worker writes the cleaned, classified transactions and summary metadata to the PostgreSQL database, marking the core tracking state as `completed`.

---

## 🛠️ Infrastructure Prerequisites
To execute this microservices stack, you only need to install the following container runtime manager on your host machine:
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (includes Docker Engine and the Docker Compose orchestration layer tool binary)

---

## ⚙️ Quick Start Installation & Boot

### Step 1: Clone the Project Directory
Open your terminal environment (e.g., Git Bash on Windows) and map the repository locally:
```bash
git clone [https://github.com/YOUR_USERNAME/ai-transaction-pipeline.git](https://github.com/YOUR_USERNAME/ai-transaction-pipeline.git)
cd ai-transaction-pipeline