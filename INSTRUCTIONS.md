# Team Instructions: RegHealth Navigator

This file lists all major TODO functions and classes, their purpose, and the responsible team. Use this as a checklist for collaborative development.

| Module/File                | Function/Class                | Purpose                                                                 | Team        |
|---------------------------|-------------------------------|-------------------------------------------------------------------------|-------------|
| core/xml_partition.py      | partition_xml                 | Partition large XML into logical sections (e.g., Medicare, HIPAA)        | Backend     |
| core/xml_chunker.py        | chunk_section                 | Chunk a section XML string into smaller text chunks                      | Backend     |
| core/embedding.py          | embed_and_store_section       | Generate embeddings for section chunks and store them                    | Backend     |
| core/llm.py                | llm_summarize_section         | LLM-based summarization for a section                                    | Backend     |
| core/llm.py                | llm_answer_query_section      | LLM-based Q&A for a section                                             | Backend     |
| core/llm.py                | llm_compare_sections          | LLM-based comparison between two sections                                | Backend     |
| app/main.py                | upload_file                   | API endpoint for uploading XML files and processing                      | Backend     |
| app/main.py                | list_files                    | API endpoint for listing available XML files                             | Backend     |
| app/main.py                | list_sections                 | API endpoint for listing sections in a file                              | Backend     |
| app/main.py                | generate_summary              | API endpoint for section-level summary                                   | Backend     |
| app/main.py                | chat_query                    | API endpoint for section-level Q&A                                       | Backend     |
| app/main.py                | compare_sections              | API endpoint for section-level comparison                                | Backend     |
| front/src/store/store.ts   | Zustand store                 | State management for files, sections, chat, summary, mindmap, etc.       | Frontend    |
| front/src/components/      | Layout, Sidebar, etc.         | UI components for file/section selection, chat, results, etc.            | Frontend    |
| scripts/xml_structure_analysis.py | analyze_structure        | Script to analyze XML tag structure                                      | Backend     |
| scripts/xml_token_count.py        | count_tokens             | Script to count words/tokens in XML                                      | Backend     |

**All code should include docstrings, doctests (where meaningful), and English comments.** 