from pathlib import Path
from parser.pipeline import run_pipeline
import json

output, impacts = run_pipeline(
    Path("samples"),
    send_to_backend=False
)

print("NODES:")
for node in output['nodes']:
    print(f"  {node['id']} ({node['kind']})")

print("\nRELATIONS:")
for rel in output['relations']:
    print(f"  {rel['source']} --[{rel['type']}]--> {rel['target']}")
