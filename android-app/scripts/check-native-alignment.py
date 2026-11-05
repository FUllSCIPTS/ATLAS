"""Validate 16 KB ELF alignment, including extensions in p4a's Python archive."""
import io
import struct
import sys
import tarfile
import zipfile
from pathlib import Path

checked=0
archives=0

def check_elf(data,name):
    global checked
    assert data[:4]==b'\x7fELF','Not ELF: '+name
    endian='<' if data[5]==1 else '>'
    assert data[4]==2,'Expected a 64-bit native file: '+name
    offset=struct.unpack_from(endian+'Q',data,32)[0]
    size,count=struct.unpack_from(endian+'HH',data,54)
    for index in range(count):
        header=offset+size*index
        if struct.unpack_from(endian+'I',data,header)[0]==1:
            alignment=struct.unpack_from(endian+'Q',data,header+48)[0]
            file_offset,vaddr=struct.unpack_from(endian+'QQ',data,header+8)
            assert alignment>=16384,(name,alignment)
            assert (vaddr-file_offset)%16384==0,(name,'unaligned load segment')
    checked+=1

with zipfile.ZipFile(Path(sys.argv[1])) as bundle:
    for name in bundle.namelist():
        if not name.endswith('.so') or '/lib/' not in '/'+name:
            continue
        data=bundle.read(name)
        if name.rsplit('/',1)[-1]=='libpybundle.so':
            # Upstream p4a packages Python data as a tar archive with this suffix.
            with tarfile.open(fileobj=io.BytesIO(data),mode='r:*') as python_bundle:
                members=python_bundle.getmembers()
                assert any(m.name.endswith('stdlib.zip') for m in members),'Unexpected Python bundle'
                for member in members:
                    if member.isfile() and member.name.endswith('.so'):
                        check_elf(python_bundle.extractfile(member).read(),name+'!'+member.name)
            archives+=1
        else:
            check_elf(data,name)
assert checked>0 and archives==2,(checked,archives)
print(f'PASS: {checked} 64-bit ELF libraries/extensions aligned to 16 KB; {archives} Python data archives validated')
