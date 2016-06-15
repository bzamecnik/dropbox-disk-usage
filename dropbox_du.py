#!/usr/bin/env python3

"""
Allows to query disk usage on Dropbox based on a previously obtained file index.
You can query for the root directory or some subdirectory.
The sorted absolute and relative disk usage of the direct children is displayed.

Example usage:

./dropbox_du.py index.ls
./dropbox_du.py index.ls /foo/bar

Note that it takes a while to build a tree from the index. Then it is cached.

Force recomputing the tree:

./dropbox_du.py -f index.ls
"""

# TODO: number of files in the subtree

import argparse
import numpy as np
import os
import pandas as pd
import pickle

def split_path(path):
    return [p for p in path.split('/') if len(p) > 0]

def read_index(index_file):
    df = pd.read_csv(index_file,
        sep='\t',
        header=None,
        names=['size', 'path_display'])
    df['path_lower'] = df['path_display'].apply(str.lower)
    df.sort('path_lower', inplace=True)
    df['is_dir'] = pd.isnull(df['size'])
    df['path_list'] = df['path_lower'].apply(split_path)
    return df

def human_readable_bytes(num, suffix='B'):
    '''
    Human readable file size
    http://stackoverflow.com/questions/1094841/reusable-library-to-get-human-readable-version-of-file-size
    '''
    for unit in ['','Ki','Mi','Gi','Ti','Pi','Ei','Zi']:
        if abs(num) < 1024.0:
            return '%3.1f%s%s' % (num, unit, suffix)
        num /= 1024.0
    return '%.1f%s%s' % (num, 'Yi', suffix)

def stats(df):
    print('total number of items:', len(df))
    print('number of files:', len(df.dropna()))
    print('number of directories:', len(df) - len(df.dropna()))
    print('total size:', human_readable_bytes(df['size'].sum()))

class Node(object):
    def __init__(self, name, is_dir, size=None, parent=None):
        self.name = name
        self.size = size
        self.is_dir = is_dir
        if is_dir:
            self.children = {}
        self.parent = parent

    def add_path(self, path, is_dir, size):
        child = path[0]
        if len(path) > 1:
            if not child in self.children:
                self.children[child] = Node(child, True, parent=self)
            self.children[child].add_path(path[1:], is_dir, size)
        else:
            self.children[child] = Node(child, is_dir, size, parent=self)

    def path(self):
        if self.parent:
            parent_path = self.parent.path()
            return (parent_path if parent_path != '/' else '') + '/' + self.name
        else:
            return '/'

    def total_size(self):
        if self.is_dir and self.size is None:
            self.size = sum(child.total_size() for _, child in self.children.items())
        return self.size

    def list(self, recursive=False):
        if self.is_dir:
            for _, child in self.children.items():
                print(human_readable_bytes(child.total_size()), child.path(), sep='\t')
                if recursive:
                    child.list()

    def find(self, path):
        path_parts = split_path(path)
        node = self
        while len(path_parts) > 0:
            node = node[path_parts[0]]
            path_parts = path_parts[1:]
        return node

    def disk_usage(self):
        self_size = self.total_size()
        print('Disk usage for:', self.path())
        print('Total size:', human_readable_bytes(self_size))
        def child_rows():
            for name, node in self.children.items():
                size = node.total_size()
                yield {
                    'name': name + ('/' if node.is_dir else ''),
                    'size': size,
                    'size_fmt': human_readable_bytes(size),
                    'size_perc': '%.2f %%' % (100 * size / self_size)
                }
        df_children = pd.DataFrame.from_records(child_rows())
        df_children.set_index('name', inplace=True)
        df_children['size'] = df_children['size'].astype(int)
        df_children.sort('size', ascending=False, inplace=True)
        print(df_children[['size_perc', 'size_fmt', 'size']])

    def __getitem__(self, key):
        return self.children[key]

    def __repr__(self):
        child_names = sorted(self.children.keys()) if self.is_dir else []
        return '[' + self.path() +', ' + repr(self.size) + ', ' + repr(child_names) + ']'

def make_tree(df):
    print('Building a tree from the index...')
    root = Node('', is_dir=True)
    for index, row in df.iterrows():
        size = row['size']
        if np.isnan(size):
            size = None
        root.add_path(row['path_list'], row['is_dir'], size)
    return root

def save_tree_to_pickle(root, pickle_file):
    with open(pickle_file, 'wb') as f:
        pickle.dump(root, f)

def load_tree_from_pickle(pickle_file):
    with open(pickle_file, 'rb') as f:
        return pickle.load(f)

def load_tree(index_file, force=False):
    """
    Loads the tree either from a cache or first build it from the index.
    """
    pickle_file = os.path.splitext(index_file)[0] + '_tree.pickle'
    if not force and os.path.exists(pickle_file):
        print('Loading cached tree from:', pickle_file)
        return load_tree_from_pickle(pickle_file)
    else:
        print('Loading from index:', index_file)
        df = read_index(index_file)
        stats(df)
        root = make_tree(df)
        print('Saving tree:', pickle_file)
        save_tree_to_pickle(root, pickle_file)
        return root

def parse_args():
    parser = argparse.ArgumentParser(description='Disk usage in Dropbox')
    parser.add_argument('index_file')
    parser.add_argument('path', default='/', nargs='?')
    parser.add_argument('-f', '--force', default=False, action='store_true',
        help='Force recomputing the tree')
    return parser.parse_args()

if __name__ == '__main__':
    args = parse_args()
    root = load_tree(args.index_file, force=args.force)
    root.find(args.path).disk_usage()
