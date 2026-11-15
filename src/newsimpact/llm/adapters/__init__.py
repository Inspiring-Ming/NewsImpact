"""Technology behind the llm ports - one file per technology.

anthropic_api.py  Claude via the official Anthropic SDK (hosted, paid per token)
ollama.py         any local model served by Ollama (runs on your machine, $0)
json_file.py      presets + price table from data/reference/llm_models.json
memory.py         cache + spend ledger in memory (tests)
sqlite.py         cache + spend ledger on SQLite (spend survives restarts)
"""
