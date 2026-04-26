# Dataset Methodology

This document describes how the `EuropeAttractions` dataset was constructed and validated for RoamRight.

## Dataset Summary

- Dataset file: `data/EuropeAttractions.json`
- Current scope: 8 cities across multiple European countries (**Spain**: Madrid, Barcelona, Valencia, and Sevilla; **France**: Paris; **England**: London; **Italy**: Rome, Florence)
- Record type: attraction/activity entries used for retrieval, ranking, and itinerary generation
- Schema style: standardized JSON object format under `activities`

## Collection Process

The dataset was manually curated by reviewing tourism-oriented sources (for example, official tourism websites, travel guides, and destination writeups), then normalizing each attraction into a consistent schema.

For each attraction candidate, the following process was used:

1. Identify a city-relevant attraction or experience.
2. Cross-check basic details (name, city, category, short description) against travel references.
3. Encode the attraction in a structured JSON format matching the project schema.
4. Add tags to support personalization and retrieval.
5. Repeat across target cities to build broad, balanced city coverage.

## Data Schema and Standardization

Data is stored in `data/EuropeAttractions.json` with:

- `metadata` block (dataset-level summary fields)
- `activities` list (one object per attraction)

Core activity fields include:

- `id`
- `city`
- `country`
- `name`
- `category`
- `description`
- `tags`
- optional location and metadata fields used by downstream ranking/scheduling

The collection process uses a single schema template so all records are represented consistently for downstream preprocessing and retrieval.

## Cleaning and Preprocessing

Preprocessing is implemented in `data/preprocess.py`. The pipeline includes:

- tag normalization (lowercasing, deduplication, underscore formatting)
- fallback handling for missing text fields
- type coercion for numeric/location fields
- row-level filtering for invalid entries (for example, missing `id` or `name`)

These steps ensure records are consistently structured before indexing and ranking.

## Quality Control and Validation

Quality checks performed during curation and preprocessing include:

- **Schema consistency:** all entries follow the same JSON structure.
- **Required fields check:** invalid rows are dropped by preprocessing if key fields are missing.
- **Duplicate control:** IDs are curated to be unique across merged city slices.
- **Retrieval readiness check:** description/tags are normalized for hybrid retrieval compatibility.

Related evidence:

- `data/EuropeAttractions.json` (final curated data artifact)
- `data/preprocess.py` (validation/normalization logic)
- `retrieval/documents.py` (conversion to retrieval documents)

## Engineering Effort Justification

This dataset was assembled through substantial manual curation and normalization work:

- selecting and compiling attractions city-by-city
- writing entries in a unified schema
- designing reusable tags for downstream personalization
- validating and cleaning data for model pipeline compatibility

## Reproducibility Notes

To inspect and validate schema usage in code:

- load + preprocess: `data/preprocess.py`
- pipeline entry point using the dataset path: `pipeline/run.py`
- configurable dataset path: `config.py` (`ROAMRIGHT_ACTIVITIES_PATH`)

## Limitations and Future Improvements

- Source URLs are not yet uniformly attached to every record.
- Future iterations can add stronger provenance tracking per activity.
- Additional cities and temporal refresh logic can be added to expand coverage.

