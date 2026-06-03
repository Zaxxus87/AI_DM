# GCP setup — scoped to current needs

Goal: a working Google Cloud project that supports the **vertical slice** (Gemini via Vertex AI) and the **data-layer phase** right after it (Firestore + Cloud Storage), with everything related to deployment and CI/CD intentionally left for later. Commands are CLI-first; console equivalents are noted where useful.

Throughout, replace the placeholders: `PROJECT_ID` (globally unique, lowercase, e.g. `agentic-dm-<your-suffix>`), `BILLING_ACCOUNT_ID`, and `REGION` (this guide uses **`us-central1`** — broad Gemini + Firestore support and US-based for your latency).

---

## Tier 1 — Required before the slice

### 1. Verify the gcloud CLI

```bash
gcloud --version
```

If it's missing, install the Google Cloud CLI, then continue. (You likely already have it from prior Vertex work.)

### 2. Log in (your user account)

```bash
gcloud auth login
```

### 3. Create the project and make it your default

```bash
gcloud projects create PROJECT_ID --name="Agentic DM"
gcloud config set project PROJECT_ID
```

Project IDs are permanent and globally unique (6–30 chars, lowercase letters/digits/hyphens).

### 4. Link a billing account

Vertex AI requires billing enabled, even though slice-stage usage costs pennies. New Google Cloud accounts typically get free trial credits.

```bash
gcloud billing accounts list
gcloud billing projects link PROJECT_ID --billing-account=BILLING_ACCOUNT_ID
```

If you have no billing account yet, create one in the console (Billing → Create account), then run the `link` command.

### 5. Enable the Vertex AI API

```bash
gcloud services enable aiplatform.googleapis.com
```

Enablement can take a minute to propagate.

### 6. Confirm Gemini model access and capture the model IDs

In the console: **Vertex AI → Model Garden**. Confirm **Gemini 3 Pro** and **Gemini 3 Flash** are available in `REGION` (a preview model like 3.1 Pro may need a one-click enable/accept). **Copy the exact model ID strings shown** — they vary by region and version, so don't guess; use what Model Garden lists. These go into `.env` in step 9.

### 7. Set up Application Default Credentials (ADC) for local dev

This is what the `google-genai` SDK uses when running against Vertex (`vertexai=True`).

```bash
gcloud auth application-default login
gcloud auth application-default set-quota-project PROJECT_ID
```

### 8. Verify the whole path works

Confirm billing + API + auth + model access end-to-end before you build the slice.

```bash
pip install google-genai
```

Create `verify_vertex.py` (delete it afterward):

```python
from google import genai

client = genai.Client(vertexai=True, project="PROJECT_ID", location="REGION")
resp = client.models.generate_content(
    model="<the Gemini 3 Pro ID from Model Garden>",
    contents="Reply with exactly: Vertex is reachable.",
)
print(resp.text)
```

```bash
python verify_vertex.py
```

If it prints the line, your Vertex path is good and the slice will work. If you hit an auth error, re-run step 7; a 403/permission error usually means the API (step 5) or billing (step 4) hasn't propagated yet.

---

## Tier 2 — Set up now to avoid a second trip (the data-layer phase is next)

Not needed for the slice itself, but the very next prompts build the `game-state`, `session-memory`, and `world-lore` servers on Firestore and start handling uploads, so enabling these now saves a context switch later.

### 9. Enable the imminent APIs

```bash
gcloud services enable firestore.googleapis.com storage.googleapis.com secretmanager.googleapis.com
```

### 10. Create the Firestore database (Native mode)

Native mode is required for the vector (KNN) search the memory/lore servers use. **The location is permanent**, so match your region.

```bash
gcloud firestore databases create --location=REGION
```

### 11. Create one asset bucket (with prefixes for the four asset types)

A single bucket with folders is simpler than four buckets. Bucket names are globally unique.

```bash
gcloud storage buckets create gs://PROJECT_ID-assets --location=REGION --uniform-bucket-level-access
```

You'll write objects under `rulebooks/`, `modules/`, `maps/`, and `transcripts/` prefixes.

### 12. Fill in `.env`

Copy the template the foundations prompt created and fill the GCP values:

```bash
cp .env.example .env
```

Set:

- `GCP_PROJECT=PROJECT_ID`
- `VERTEX_REGION=REGION`
- `GEMINI_PRO_MODEL=` and `GEMINI_FLASH_MODEL=` — the IDs from step 6
- `EMBEDDING_MODEL=` — leave blank until the RAG phase, then use the current Vertex text-embedding model ID
- the asset bucket name (`gs://PROJECT_ID-assets`)
- keep `VITE_DM_CLIENT=mock`

> Tip: the SDK also reads `GOOGLE_GENAI_USE_VERTEXAI=true`, `GOOGLE_CLOUD_PROJECT`, and `GOOGLE_CLOUD_LOCATION` from the environment, so in app code you can construct `genai.Client()` with no arguments and let `.env` drive it.

---

## Intentionally deferred (do NOT set up now)

These belong to later phases; setting them up now would be premature and is easy to get wrong before you know the shapes:

- **Cloud Run, Cloud Build / GitHub Actions, Workload Identity Federation** — deployment & CI/CD phase.
- **A dedicated service account** — for local dev, ADC (step 7) is sufficient; you'll create a least-privilege service account when you deploy.
- **Eventarc** — only when you wire the RAG ingestion trigger.
- **Vertex AI Vector Search** — only if Firestore vectors prove insufficient at scale.

---

## What you have when done

A billing-linked project with Vertex AI reachable from your machine via ADC, confirmed Gemini model IDs in `.env`, and a Firestore database plus an asset bucket ready for the data-layer phase. That's the complete footprint the slice needs, plus a head start on what immediately follows — and nothing more. Idle cost at this stage is effectively zero: Vertex bills per call, Firestore and Storage sit in the free tier, and no compute is running.
