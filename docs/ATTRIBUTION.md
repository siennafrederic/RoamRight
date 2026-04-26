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
  Used for semantic retrieval embeddings.
- **LLM provider integration**: OpenAI-compatible chat completion API (provider configurable via `.env`)  
  Used for itinerary generation and repair/reformat logic in the generation pipeline.

## Data Sources and Data Construction

- Core activity data is stored in project `data/` artifacts (e.g., `EuropeAttractions.json`) and processed through project preprocessing scripts.
- Event augmentation uses live provider integration logic in `data/events.py` and scripts under `scripts/` where applicable.
- Dataset curation and transformation logic is implemented within this repository (`data/preprocess.py` and related scripts/modules).

## AI-Assisted Development Disclosure

The project used AI coding assistance tools for selected development tasks. AI assistance was used as a drafting and iteration aid, with human review and edits before final integration.

### AI tools used

- Cursor AI assistant (code and documentation drafting support)
- LLM-based assistance for debugging, refactoring suggestions, and wording improvements

### What AI generated or assisted with

- Draft code suggestions for parts of retrieval/ranking/evaluation utilities
- Documentation drafts for evaluation and setup instructions
- Refactoring suggestions for readability and modularization

### What was manually authored, verified, or substantially reworked

- Final architecture decisions and pipeline design
- Metric definitions and evaluation framing
- Integration choices across backend, retrieval, ranking, and frontend
- Debugging runtime issues, validating outputs, and adjusting implementation details
- Final edits to code and documentation prior to submission

## Media and Asset Attribution

- Frontend background images are stored under `frontend/public/images/`.
- If external images are retained in final submission, include source links and licenses below.

Template (fill as needed):

- `<image filename>` - `<source URL>` - `<license>`

## Citation Notes

- This project does not claim ownership of third-party libraries, frameworks, pretrained models, or APIs listed above.
- All external tooling and model providers are acknowledged here for transparency and reproducibility.