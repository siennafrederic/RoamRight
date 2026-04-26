# ATTRIBUTION

This document records external sources, libraries, datasets, and AI-assisted development used in RoamRight.

## Project and Course Context

- Project: `RoamRight`
- Course: CS 372 (Spring '26 Final Project)

## Third-Party Libraries and Frameworks

- **FastAPI** - backend web API framework  
[https://fastapi.tiangolo.com/](https://fastapi.tiangolo.com/)
- **Uvicorn** - ASGI server for local deployment  
[https://www.uvicorn.org/](https://www.uvicorn.org/)
- **NumPy** - numerical operations  
[https://numpy.org/](https://numpy.org/)
- **FAISS (CPU)** - vector similarity search index  
[https://github.com/facebookresearch/faiss](https://github.com/facebookresearch/faiss)
- **sentence-transformers** - sentence embedding models  
[https://www.sbert.net/](https://www.sbert.net/)
- **OpenAI Python SDK (OpenAI-compatible client usage)**  
[https://github.com/openai/openai-python](https://github.com/openai/openai-python)
- **python-dotenv** - environment variable loading from `.env`  
[https://github.com/theskumar/python-dotenv](https://github.com/theskumar/python-dotenv)
- **httpx** - HTTP client support  
[https://www.python-httpx.org/](https://www.python-httpx.org/)
- **React** - frontend UI framework  
[https://react.dev/](https://react.dev/)
- **Vite** - frontend build/dev server toolchain  
[https://vitejs.dev/](https://vitejs.dev/)
- **TypeScript** - frontend type checking/tooling  
[https://www.typescriptlang.org/](https://www.typescriptlang.org/)

## Models and ML Components

- **Sentence embedding model**: `sentence-transformers/all-MiniLM-L6-v2`  
Used to generate semantic embeddings for retrieval over the activity dataset.
- **Primary LLM runtime (local)**: **Ollama** (default provider in config)  
RoamRight is configured to run a local Ollama model by default (configured via `LLM_PROVIDER=ollama`, `LLM_BASE_URL=http://localhost:11434/v1`, and `LLM_MODEL` in `.env`).
- **LLM client interface**: OpenAI-compatible chat completion API  
The app uses an OpenAI-compatible client interface to call the LLM endpoint. In this project, that interface is used with Ollama's local OpenAI-compatible endpoint for itinerary generation and itinerary repair/reformat logic in the generation pipeline.

## Data Sources and Data Construction

- Core activity data is stored in project `data/` artifacts (e.g., `EuropeAttractions.json`) and processed through project preprocessing scripts.
- Event augmentation uses live provider integration logic in `data/events.py` and scripts under `scripts/` where applicable.
- Dataset curation and transformation logic is implemented within this repository (`data/preprocess.py` and related scripts/modules).

## AI-Assisted Development Disclosure

AI tools (including Cursor and ChatGPT) were used as targeted support during different phases of development. Their role was to help me move from planning to implementation when I was stuck, not to replace my own design and coding decisions.

### Specific ways AI was used

- **Founding architecture at project start**: At the beginning of RoamRight, I used AI to help sketch the initial architecture for a RAG-based travel assistant. This included breaking the system into major components (data preparation, retrieval/indexing, generation, API layer, and UI flow) so I had a concrete starting structure.
- **Project planning and task breakdown**: I used AI to create an ordered implementation plan with specific tasks needed to get the RAG pipeline running end-to-end (what to build first, what dependencies to set up, and what should be validated at each milestone).
- **Research support when I did not know how to start coding**: When I was unsure how to begin a feature, I asked AI for technical resources and starting directions (documentation, methods, and implementation approaches), then used those references to write code myself.
- **Connecting existing pieces of code**: In cases where I had partially working components, I used AI assistance to reason through how to connect what I had already built (for example, aligning interfaces between retrieval/generation steps and making the pieces work together coherently).
- **UI scaffold + manual redesign**: AI generated an initial/basic UI scaffold so I could quickly stand up the frontend; I then manually edited layout, behavior, and presentation details to match the interface I had originally envisioned before coding.
- **Backend-to-frontend API integration support**: AI helped troubleshoot and structure the connection between backend API endpoints and frontend calls so request/response flow worked correctly across the app.
- **Evaluation brainstorming**: I used AI to brainstorm how to design evaluation code, especially when deciding what to test, what metrics/behaviors mattered, and how to structure test coverage for generated outputs.
- **Dataset quality check after manual creation**: After I created the full dataset, I used ChatGPT as a verification pass to check for missing fields per entry and confirm entries followed a consistent format.

### Authorship and final responsibility

All final architecture decisions, implementation details, code integration, and submitted outputs were manually reviewed and finalized by me.

## Media and Asset Attribution

- Frontend background images are stored under `frontend/public/images/`.

## Citation Notes

- This project does not claim ownership of third-party libraries, frameworks, pretrained models, or APIs listed above.
- All external tooling and model providers are acknowledged here for transparency and reproducibility.

