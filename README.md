# Research Workbench: Digital Humanities Knowledge Graph & Analytics Engine

A local-first data engineering and analytics system designed to model complex, ambiguous, and multi-modal scholarly domains. It ingests thousands of PDFs and years of research logs to produce an interactive knowledge graph and reflexive inquiry dashboard.

**[🌐 Live Portal: https://vileos.github.io/esoteric-studies-database/](https://vileos.github.io/esoteric-studies-database/)**

## Portfolio Narrative
**The Problem**: Humanities research archives are typically unstructured "urban traffic"—PDFs, disparate notes, and sprawling chat transcripts.
**The Solution**: I designed a system that treats this material as a structured database, modeling documents, scholars, iconographic symbols, and inquiry patterns as data frames with typed relationships. The workbench demonstrates mastery of ETL pipelines, relational schema design, inverted indexing, and multimodal data modeling.

---

## Data Science Skills Matrix

### I. Data Engineering & Pipeline Design
- **ETL Architecture**: Ingests heterogeneous sources (PDFs, HTML chat logs, JSON). Demonstrates parsing, text normalization, and handling missing metadata.
- **Relational Modeling**: 3NF-style schema for documents, entities, images, and typed relationships. Implements stable SHA256 identifiers and many-to-many join tables.
- **Data Integrity**: Built-in redaction layers for privacy-aware deployment and deterministic versioning for reproducibility.

### II. Information Retrieval & Indexing
- **Inverted Indexing**: Implemented **SQLite FTS5** for sub-second full-text search across milions of words.
- **Analytical Aggregation**: Dashboard metrics powered by complex SQL joins and GROUP-BY operations (e.g., Scholar Prominence, Inquiry Velocity).

### III. Graph Modeling & Knowledge Representation
- **Entity Resolution**: Canonical management of historical figures and concepts (e.g., entity merging and alias resolution).
- **Ontology Construction**: Formalized taxonomies for alchemical iconography (symbol vs. substance vs. theory) and investigative "moves."

### IV. Applied NLP & Hybrid ML
- **Feature Engineering**: Computing question density, topic distribution, and longitudinal inquiry patterns.
- **Hybrid Pipelines**: Using strict JSON-guarded LLM extraction only where deterministic rules fail, with caching and rationale tracking.

### V. Reflexive Analytics (The "Desire Profile")
- **Knowledge Gap Detection**: Detects "Desire Gaps" by cross-referencing high question density against low document availability in specific topic clusters.
- **Trajectory Mapping**: Visualizes the evolution of research methodologies over time.

---

## 🏛 V9.1: Narrative & Interface Evolution

This release focuses on unifying the research experience through structured data contracts and immersive narrative layers.

### 🔍 Omni Search & Universal Navigation
- **Command Palette (`Ctrl+K`)**: A system-wide search interface that indexes documents, dictionary entries, entities, and navigation commands.
- **Shared Routing Contract**: Universal support for deep linking via query parameters across all portal pages.

### ⛓ The "Golden Chain" Visualizer
- **Lineage Gallery**: An interactive DAG-based tree in the Hermetic Workbench tracing the transmission of Hermetic thought across historical epochs.
- **Epoch Milestone Banners**: Narrative summaries that provide context for major shifts in the tradition (Late Antiquity, Medieval, Renaissance).

### 🔄 Discovery Loops & Quick Actions
- **Dictionary Loops**: Data-driven recommendations that link alchemical terms to their primary source documents and related scholarship.
- **Library Quick Actions**: Contextual sidebar in the document viewer allowing users to pivot instantly to the Knowledge Graph or Dictionary.

### ✨ Ambient Discovery
- **Feature Glows**: System-generated visual cues that highlight new data insights and metrics gaps, guiding the user toward under-utilized research paths.

---

## Technical Stack
- **Languages**: Python (Core Pipeline), SQL (SQLite / FTS5), Javascript (SPA Frontend)
- **Libraries**: `pypdf`, `beautifulsoup4`, `PyMuPDF`, `Alpine.js`, `TailwindCSS`
- **Architecture**: Local-first SQLite source of truth with redacted JSON snapshot exports for public showcase.

## Use the Workbench
### Local Mode (Research)
1. Install dependencies: `pip install -r requirements.txt`
2. Run pipeline: `python ingest_chats.py; python mine_images.py; python scan.py`
3. Open `docs/index.html` via any local server.

### Static Mode (Exhibition)
Run `python scan.py --static` to produce a redacted, privacy-preserving snapshot in the `docs/` folder, ready for GitHub Pages deployment.
