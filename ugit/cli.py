# Import the required libraries
import argparse
import os
import sys

# Import the required modules
from . import base
from . import data

# Main function
def main () -> None:
    # Parse the arguments
    args = parse_args ()
    # Call the function based on the command
    args.func (args)

# Parse the arguments
def parse_args ():
    # Create the parser
    parser = argparse.ArgumentParser ()

    # Add the commands
    commands = parser.add_subparsers (dest='command')
    commands.required = True

    # Add the commands
    # Add the init command
    init_parser = commands.add_parser ('init')
    init_parser.set_defaults (func=init)

    # Add the hash-object command
    hash_object_parser = commands.add_parser ('hash-object')
    hash_object_parser.set_defaults (func=hash_object)
    hash_object_parser.add_argument ('file')

    # Add the cat-file command
    cat_file_parser = commands.add_parser ('cat-file')
    cat_file_parser.set_defaults (func=cat_file)
    cat_file_parser.add_argument ('object')

    # Add the write-tree command
    write_tree_parser = commands.add_parser ('write-tree')
    write_tree_parser.set_defaults (func=write_tree)

    # Add the read-tree command
    read_tree_parser = commands.add_parser ('read-tree')
    read_tree_parser.set_defaults (func=read_tree)
    read_tree_parser.add_argument ('tree')

    # Add the commit command
    commit_parser = commands.add_parser ('commit')
    commit_parser.set_defaults(func=commit)
    commit_parser.add_argument('-m', '--message', required=True)

    # Add the log command
    log_parser = commands.add_parser('log')
    log_parser.set_defaults(func=log)
    log_parser.add_argument('oid', nargs='?')

    # Add the checkout command
    checkout_parser = commands.add_parser('checkout')
    checkout_parser.set_defaults(func=checkout)
    checkout_parser.add_argument('commit_oid')

    # Return the parsed arguments
    return parser.parse_args()

# Initialize the GIT repository
def init (args: argparse.Namespace) -> None:
    data.init ()
    print (f'Initialized empty ugit repository in {os.getcwd()}/{data.GIT_DIR}')

# Hash the object
def hash_object (args: argparse.Namespace) -> None:
    # Open the file in binary mode
    with open (args.file, 'rb') as f:
        print (data.hash_object (f.read ()))

# Get the object
def cat_file(args: argparse.Namespace) -> None:
    sys.stdout.flush()
    sys.stdout.buffer.write(data.get_object(args.object, expected=None))

# Write the tree
def write_tree(args: argparse.Namespace) -> None:
    print(base.write_tree())

# Read the tree
def read_tree (args: argparse.Namespace) -> None:
    base.read_tree (args.tree)

# Commit the changes
def commit(args: argparse.Namespace) -> None:
    print(base.commit(args.message))

# Log the commits
def log(args: argparse.Namespace) -> None:
    oid = args.oid or data.get_HEAD() # If no OID is provided, get the HEAD
    # Loop through the commits
    while oid:
        # Get the commit object
        commit = base.get_commit(oid)
        print(f'commit {oid}\n')
        print(f'    {commit.message}\n')
        # Set the OID to the parent commit (akin to cur = cur->next in linked lists)
        oid = commit.parent

# Checkout the commit
def checkout(args: argparse.Namespace) -> None:
    base.checkout(args.commit_oid)
