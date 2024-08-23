import os
import string
from typing import Optional

from . import data
from collections import namedtuple

def write_tree(directory: str = '.') -> str:
    # Get the list of files and directories in the directory
    entries = []
    # Iterate over the files and directories
    with os.scandir (directory) as it:
        # Iterate over the files and directories
        for entry in it:
            # Get the full path of the file or directory
            full = f'{directory}/{entry.name}'
            # Check if the file or directory is ignored
            if is_ignored (full):
                continue

            # Check if the entry is a file, if it is, set the type to blob and hash the object
            if entry.is_file (follow_symlinks=False):
                type_ = 'blob'
                with open (full, 'rb') as f:
                    oid = data.hash_object (f.read ())
            # If the entry is a directory, set the type to tree and hash the object
            elif entry.is_dir (follow_symlinks=False):
                type_ = 'tree'
                oid = write_tree (full)
            entries.append ((entry.name, oid, type_))

    # Sort the entries by name and join them to create a tree object
    tree = ''.join (f'{type_} {oid} {name}\n'
                    for name, oid, type_
                    in sorted (entries))
    # Hash the tree object and return the OID
    return data.hash_object (tree.encode (), 'tree')


def _iter_tree_entries(oid: str):
    # Ensure that the OID is not None
    if not oid:
        return
    # Get the tree object
    tree = data.get_object (oid, 'tree')
    # Iterate over the tree object (split by lines) (eg: 'blob 1234 file.txt' -> ['blob', '1234', 'file.txt'])
    for entry in tree.decode ().splitlines ():
        type_, oid, name = entry.split (' ', 2) # type_ = 'blob', oid = '1234', name = 'file.txt'
        yield type_, oid, name # Return the type, oid, and as __next__ is called, it will return the next value

def get_tree(oid: str, base_path: str = '') -> dict:
    # Initialize the result as an empty dictionary
    result = {}
    # Iterate over the tree entries
    for type_, oid, name in _iter_tree_entries (oid):
        # Ensure that the name does not contain '/' eg: 'a/b/c' is not allowed
        assert '/' not in name
        # Ensure that the name is not '.' or '..'. eg: '.' and '..' are not allowed
        assert name not in ('..', '.')
        # Create the path by joining the base path and the name. eg: base_path = 'a/b', name = 'c' -> 'a/b/c'
        path = base_path + name
        # If the type is blob, set the result[path] to the OID. eg: result['a/b/c'] = '1234'
        if type_ == 'blob':
            result[path] = oid
        # If the type is tree, recursively call get_tree with the OID and the path
        elif type_ == 'tree':
            # This will be called recursively until all the tree entries are processed
            # For instance, if the tree contains a directory 'a' with a file 'b' in it, the result will be:
            # {'a/b': '1234'}
            result.update (get_tree (oid, f'{path}/'))
        else:
            # Raise an error if the type is not blob or tree
            assert False, f'Unknown tree entry {type_}'
    # Return the result
    return result

def _empty_current_directory () -> None:
    # Iterate over the files and directories in the current directory (using topdown=False to ensure that the files are deleted first)
    for root, dirnames, filenames in os.walk ('.', topdown=False):
        # Iterate over the files and directories
        for filename in filenames:
            # Get the path of the file: eg: root = 'a/b', filename = 'c' -> 'a/b/c'
            path = os.path.relpath (f'{root}/{filename}')
            # Handle the case where the file is ignored or not a file
            if is_ignored (path) or not os.path.isfile (path):
                continue
            # Calling os.remove to delete the file
            os.remove (path)
        # Iterate over the directories
        for dirname in dirnames:
            # Get the path of the directory: eg: root = 'a/b', dirname = 'c' -> 'a/b/c'
            path = os.path.relpath (f'{root}/{dirname}')
            # Handle the case where the directory is ignored 
            if is_ignored (path):
                continue
            # Calling os.rmdir to delete the directory
            try:
                os.rmdir (path)
            except (FileNotFoundError, OSError):
                # Deletion might fail if the directory contains ignored files,
                # so it's OK
                pass

def read_tree(tree_oid: str) -> None:
    # Call _empty_current_directory to delete all the files and directories in the current directory
    _empty_current_directory ()
    # Get the tree entries
    # example with a realistic tree: {'/home/user/a/file.txt': '1234'} -> path = '/home/user/a/file.txt', oid = '1234'
    for path, oid in get_tree (tree_oid, base_path='./').items ():
        # Create the directories if they do not exist
        os.makedirs (os.path.dirname (path), exist_ok=True)
        # Get the object and write it to the file
        with open (path, 'wb') as f:
            f.write (data.get_object (oid))

# The commit function now takes a message as an argument, which is a string. This message is added to the commit object.
def commit (message: str) -> str:
    # This is akin to the detached HEAD state in Git. Still have to implement the main pointer to the HEAD and branches.
    # Get the current tree and get the OID of the tree
    commit = f'tree {write_tree ()}\n'
    # Get the HEAD commit OID
    HEAD = data.get_ref('HEAD')
    # If the HEAD exists, add it to the commit object
    if HEAD:
        commit += f'parent {HEAD}\n'

    # Add the message to the commit object
    commit += '\n'
    # Add the message to the commit object
    commit += f'{message}\n'

    # Hash the commit object and set the HEAD to the new commit OID (using .encode() to convert the string to bytes)
    commit_oid = data.hash_object (commit.encode (), 'commit')
    # Set the HEAD to the new commit OID
    # data.set_HEAD (commit_oid)
    data.update_ref('HEAD', commit_oid)

    # Return the commit OID
    return commit_oid

def checkout(commit_oid: str) -> None:
    # Get the commit object
    commit = get_commit(commit_oid)
    # Use the tree object from the commit object to update the working directory
    read_tree(commit.tree)
    # Update HEAD to the new commit
    data.update_ref('HEAD', commit_oid)

# create_tag function to create a tag for each commit (a one-to-one mapping between a commit and a tag)
def create_tag(name: str, oid: str) -> None:
    # Update the ref to the OID
    data.update_ref(f'refs/tags/{name}', oid)

# Named tuple to store the commit object (tree, parent, message)
Commit = namedtuple('Commit', ['tree','parent','message'])

def get_commit(commit_oid: str) -> Commit:
    # Get the commit object
    commit_data = data.get_object(commit_oid, 'commit').decode()
    # Parse the commit object to get the tree and parent commit object
    lines = commit_data.splitlines()
    
    # Initialize the variables
    tree = None
    parent = None
    # Message is the rest of the lines
    message_lines = []
    
    # Parse the commit object
    for line in lines:
        # If the line is empty, it means the message starts
        if not line:
            break
        # Parse the line by splitting it by space (eg. 'tree 1234') -> ['tree', '1234'] (key, value)
        key, value = line.split(' ', 1)
        # If the key is tree or parent, set the value to the corresponding variable
        if key == 'tree':
            tree = value
        elif key == 'parent':
            parent = value
        else:
            # If the key is not tree or parent, raise an error
            raise ValueError(f'Unknown field {key}')
    
    # The rest of the lines are the message
    message = '\n'.join(lines[len(message_lines):])
    # Return the Commit object (nameTuple) (can be outside the function as well, but it's better to keep it here)
    return Commit(tree=tree, parent=parent, message=message)

# Get the commit object from the ref
def iter_commits_and_parents(oids):
    oids = set(oids)
    visited = set()

    while oids:
        oid = oids.pop()
        if not oid or oid in visited:
            continue
        visited.add(oid)
        yield oid

        commit = get_commit(oid)
        oids.add(commit.parent)

# Get_oid function to get the OID of a ref
def get_oid(name: str) -> Optional[str]:

    if name == '@': 
        name = 'HEAD'

    # Name is ref
    ref_directories_to_search = [
            f'{name}',
            f'refs/{name}',
            f'refs/tags/{name}',
            f'refs/heads/{name}',
    ]
    # Iterate over the ref directories
    for ref in ref_directories_to_search:
        if data.get_ref(ref):
            return data.get_ref(ref)

    # If the Name is SHA-1
    is_hex = all(c in string.hexdigits for c in name)
    if len(name) == 40 and is_hex:
        return name
    
    assert False, f'Unknown name {name}'

# Ignore the files in the .ugit directory
def is_ignored (path: str) -> bool:
    # Check if the path contains .ugit or .git
    # path.split('/') will split the path by / and return a list of directories and files (eg: path = 'a/b/c' -> ['a', 'b', 'c'])
    return bool('.ugit' or '.git' in path.split ('/') or path == '.ugit' or path == '.git') 
