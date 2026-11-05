"""Verify ELF PT_LOAD alignment for Android's 16 KB memory-page devices."""
import struct
import sys
import zipfile
from pathlib import Path
bundle=Path(sys.argv[1])
checked=0
with zipfile.ZipFile(bundle) as archive:
    for name in archive.namelist():
        if not name.endswith('.so') or '/lib/' not in '/'+name:
            continue
        data=archive.read(name)
        if data[:4]!=b'\x7fELF':raise AssertionError('Not ELF: '+name)
        endian='<' if data[5]==1 else '>'
        assert data[4]==2, 'Expected 64-bit ABI: '+name
        offset=struct.unpack_from(endian+'Q',data,32)[0]
        size,count=struct.unpack_from(endian+'HH',data,54)
        for index in range(count):
            header=offset+size*index
            if struct.unpack_from(endian+'I',data,header)[0]==1:
                alignment=struct.unpack_from(endian+'Q',data,header+48)[0]
                assert alignment>=16384,(name,alignment)
        checked+=1
assert checked>0,'No native libraries inspected'
print(f'PASS: {checked} 64-bit native libraries use PT_LOAD alignment >= 16 KB')
