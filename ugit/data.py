import hashlib
from typing import Optional
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

# Setters and Getters for HEAD
def set_HEAD (commit_oid: str) -> None:
    with open(f'{GIT_DIR}/HEAD', 'w') as f:
        f.write(commit_oid)

# Get the HEAD commit OID
def get_HEAD() -> Optional[str]:
    if os.path.isfile(f'{GIT_DIR}/HEAD'):
        with open(f'{GIT_DIR}/HEAD') as f:
            return f.read().strip()

# Get the object from the OID
def get_object (oid: str, expected: Optional[str] = 'blob') -> bytes:
    # Open the object file in binary mode
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
