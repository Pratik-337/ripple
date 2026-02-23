from pathlib import Path
from parser.pipeline import run_pipeline
import json
output, _ = run_pipeline(Path('samples'))
print(json.dumps(output, indent=2))
