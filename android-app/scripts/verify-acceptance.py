"""Fail on missing interactions, images, undersized viewports or blank screenshots."""
import json
import sys
from pathlib import Path
from PIL import Image
path=Path(sys.argv[1])
result=json.loads((path/'result.json').read_text())
assert result['success'],result
screenshots=list(path.glob('*.png'))
assert len(screenshots)==12,'Expected twelve actual app screenshots'
for screenshot in screenshots:
    with Image.open(screenshot).convert('RGB') as image:
        width,height=image.size
        assert width>=320 and height>=600,(screenshot,image.size)
        top=image.crop((0,0,width,height//3))
        assert top.getextrema() != ((0,0),(0,0),(0,0)),f'Blank/clipped screenshot: {screenshot}'
        assert len(top.getcolors(width*height) or [])>10,f'Empty screen: {screenshot}'
print(result['detail'])
