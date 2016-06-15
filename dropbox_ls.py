#!/usr/bin/env python3

"""
Lists files and directories from Dropbox (similar to `ls -lR`).

You can specify either the root directory or some subdirectory.
You can list either direct children or recursively (-R).

The output is a TSV file with two columns (size, path) and no header.
The size in bytes is an integer for files and empty string for directories.
The files are not sorted by path. The path is in original case and might be
necessary to normalize to lowercase for additional processing.

Before usage you have to create your own Access Token in Drop box API console
and export it as the DROPBOX_ACCESS_TOKEN environment variable. Note that you
might need to register your own Dropbox App
[https://www.dropbox.com/developers/apps] with Full Dropbox permissions.

Example usage:

export DROPBOX_ACCESS_TOKEN="<my_secret_token>"
./dropbox_ls.py > dropbox-root.ls
./dropbox_ls.py -R > dropbox-root-recursive.ls
./dropbox_ls.py /foo/bar -R > dropbox-foo-bar-recursive.ls

Dropbox API for Python:
- https://www.dropbox.com/developers/documentation/python
"""

import argparse
import dropbox
import os
import sys

dbx = dropbox.Dropbox(os.environ['DROPBOX_ACCESS_TOKEN'])

def print_entries(entries):
    for entry in entries:
        if type(entry) == dropbox.files.FileMetadata:
            size, path = entry.size, entry.path_display
        elif type(entry) == dropbox.files.FolderMetadata:
            size, path = '', entry.path_display
        print(size, path, sep='\t')

def list_files(path, recursive=True):
    response = dbx.files_list_folder(path, recursive=recursive)
    print("cursor:", response.cursor, file=sys.stderr)
    print_entries(response.entries)
    while response.has_more:
        try:
            response = dbx.files_list_folder_continue(cursor=response.cursor)
            print_entries(response.entries)
        except dropbox.exceptions.InternalServerError as ex:
            print(ex, file=sys.stderr)

def parse_args():
    parser = argparse.ArgumentParser(description='List files in DropBox')
    parser.add_argument('path', default='', nargs='?')
    parser.add_argument('-R', '--recursive', default=False, action='store_true')
    return parser.parse_args()

if __name__ == '__main__':
    args = parse_args()
    list_files(args.path, args.recursive)
