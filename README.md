LexiClear

LexiClear is an AI-powered legal document simplification system built using Retrieval-Augmented Generation (RAG), Natural Language Processing (NLP), and Large Language Models (LLMs).

Features

* PDF document processing
* Text extraction and chunking
* Semantic embeddings generation
* Vector database storage using ChromaDB
* Semantic retrieval of relevant document content
* Groq LLM integration
* Context-aware question answering
* Legal document explanation in simple language
* Full-document translation from English to Hindi or Kannada, page by page
* Questions and legally grounded answers in English, Hindi, or Kannada
* Preservation of clause numbers, legal citations, and section references

## Multilingual API

Upload a PDF first with `POST /upload`. Translate the complete uploaded document with:

```json
POST /translate
{"language": "Hindi"}
```

Use `"Kannada"` to receive Kannada output. Each page is split into paragraphs and
translated paragraph-by-paragraph before being recombined, so large pages stay within
the model's context limit while remaining aligned with the source PDF pages. Detected
tables are translated as whole table blocks, preserving their rows, columns, headers,
and cell order.

Blank source pages are returned as `"translation": "[Blank Page]"` with
`"is_blank_page": true`, preserving their page position for rendering or export.

Ask in any supported language; omit `language` to detect it from Hindi/Kannada script,
or set it explicitly to choose the reply language:

```json
POST /ask
{"question": "What is the notice period?", "language": "Kannada"}
```

Questions are translated to English only for retrieval against the English corpus. The
final answer is returned in the requested language, with legal citations and references
kept unchanged.

Tech Stack

* Python
* LangChain
* ChromaDB
* Sentence Transformers
* Groq API
* Retrieval-Augmented Generation (RAG)
