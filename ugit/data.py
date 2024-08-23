import hashlib
from typing import Optional, Tuple, Generator
import os

# Initialize the GIT directory
GIT_DIR = '.ugit'

# Initialize the GIT directory
def init () -> None:
    os.makedirs (GIT_DIR)
    os.makedirs (f'{GIT_DIR}/objects')

# Take in bytes and return the hash of the object
def hash_object (data: bytes, type_: str = 'blob') -> str:
    obj = type_.encode () + b'\x00' + data
    oid = hashlib.sha1 (obj).hexdigest ()
    with open (f'{GIT_DIR}/objects/{oid}', 'wb') as out:
        out.write (obj)
    return oid

# Setters and Getters for Refs
def update_ref(ref: str, commit_oid: str) -> None:
    ref_path = f'{GIT_DIR}/{ref}'
    os.makedirs(os.path.dirname(ref_path), exist_ok=True)
    with open(ref_path, 'w') as f:
        f.write(commit_oid)

# Get the HEAD commit OID
def get_ref(ref: str) -> Optional[str]:
    ref_path = f'{GIT_DIR}/{ref}'
    if os.path.isfile(ref_path):
        with open(ref_path) as f:
            return f.read().strip()

# Create iter_refs() function
def iter_refs(): 
    refs = ['HEAD']

    for root, _, filenames in os.walk(f'{GIT_DIR}/refs/'):
        root = root.replace('\\', '/').replace(GIT_DIR, '')[1:]
        refs.extend(f'{root}/{name}' for name in filenames)

    for refname in refs:
        yield refname, get_ref(refname)

# Get the object from the OID
def get_object (oid: str, expected: Optional[str] = 'blob') -> bytes:
    # Open the object file in binary mode
    # with open (f'{GIT_DIR}/objects/{oid}', 'rb') as f:
    with open (f'{GIT_DIR}/objects/{oid}', 'rb') as f:
        obj = f.read ()

    # Split the object into type and content
    type_, _, content = obj.partition (b'\x00') # eg: b'blob\x00' + b'1234' -> b'blob', b'1234'
    type_ = type_.decode() # eg: b'blob' -> 'blob'

    # Ensure that the type is expected
    if expected is not None:
        assert type_ == expected, f'Expected {expected}, got {type_}'

    # Return the content
    return content
