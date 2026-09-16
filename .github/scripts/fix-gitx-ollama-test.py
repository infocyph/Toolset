#!/usr/bin/env python3
from pathlib import Path

path = Path('tests/gitx.sh')
text = path.read_text()
text = text.replace("    *' /api/tags '*) printf '{\"models\":[{\"name\":\"qwen2.5:3b\"},{\"name\":\"llama3.2:3b\"}]}' ;;", "    *'/api/tags'*) printf '{\"models\":[{\"name\":\"qwen2.5:3b\"},{\"name\":\"llama3.2:3b\"}]}' ;;")
text = text.replace("    *' /api/generate '*) printf '{\"response\":\"feat: local ollama\",\"done\":true}' ;;", "    *'/api/generate'*) printf '{\"response\":\"feat: local ollama\",\"done\":true}' ;;")
path.write_text(text)
