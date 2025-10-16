# moniagent Development Guidelines

Auto-generated from all feature plans. Last updated: 2025-10-15

## Active Technologies
- Python 3.12.6 + FastAPI, LangChain, LangGraph, Supabase, gemini-2.5-flash-lite, gemini-2.5-flash (main)
- Python 3.12.6 (based on project guidelines) + FastAPI, LangChain, LangGraph, Supabase, gemini-2.5-flash-lite for core agent, gemini-2.5-flash for OCR. (003-t-i-mu)
- Supabase (PostgreSQL-based) for expense and user data, with potential file storage for invoice images (003-t-i-mu)

## Project Structure
```
src/
tests/
```

## Commands
cd src; pytest; ruff check .

## Code Style
Python 3.11: Follow standard conventions

## Recent Changes
- 003-t-i-mu: Added Python 3.12.6 (based on project guidelines) + FastAPI, LangChain, LangGraph, Supabase, gemini-2.5-flash-lite for core agent, gemini-2.5-flash for OCR.
- main: Added Python 3.11 + FastAPI, LangChain, LangGraph, Supabase, gemini-2.5-flash-lite for core agent, gemini-2.5-flash for ocr service

<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->
