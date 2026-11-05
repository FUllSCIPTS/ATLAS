"""Exit nonzero unless the UI driver finished with twelve screenshots."""
import json
import sys
from pathlib import Path
path=Path(sys.argv[1])
result=json.loads((path/'result.json').read_text())
assert result['success'],result
assert len(list(path.glob('*.png')))==12,'Expected twelve real screenshots'
print(result['detail'])
