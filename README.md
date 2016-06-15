# Dropbox Disk Usage

Like `ls -lR` and `du -hs` in unix.

## The problem

I'd like to store tons of data in by 1TB DropBox account (instead of my external disk) which are not synchronized to my local file system. I'd like to have knowledge of which parts of the data use the most disk space. On a unix system I can use `du`, on Mac I can use DaisyDisk. However, on DropBox I don't have such a tool. The desktop shows only total usage in percents (eg. 25% of 1TB quota). The web UI doesn't show anything beyond sizes of individual files.

## Obtain Access Token

- go to https://www.dropbox.com/developers/apps
- register your app
- copy your access token and export it as an environment variable
  `export DROPBOX_ACCESS_TOKEN=...`

## Requirements

- Python 3

```
pip install dropbox
pip install pandas
```

## List files (`ls -lR`)

Obtain the index of files in Dropbox (path and size).

```
./dropbox_ls.py 2> error.log | tee dropbox-index.tsv
  /docs
123 /docs/foo.txt
  /music
1234567 /music/bar.mp3
...
```

This may take eg. 20 minutes for ~300k files.

## Disk usage (`du -hs`)

Disk usage for the children of the root directory (human readable and percentage). Ordered from biggest to smallest.

On the first run a tree is build from the index which may take about a minute.
Then it is cached.

```
./dropbox_du.py dropbox-index.tsv
Disk usage for: /
Total size: 282.4GiB
                     size_perc  size_fmt          size
name                                    
something_big/         94.40 %  266.5GiB  286195014794
large/                  3.09 %    8.7GiB    9369366131
medium/                 1.16 %    3.3GiB    3511982644
small/                  0.50 %    1.4GiB    1510581472
tiny/                   0.33 %  968.1MiB    1015146707
```

Disk usage for some subdirectory:

```
/dropbox_du.py dropbox-index.tsv /foo
Disk usage for: /foo
Total size: 8.7GiB
                                size_perc  size_fmt        size
name                                               
dir_01/                           85.02 %    7.4GiB  7966172821
dir_02/                           14.44 %    1.3GiB  1352917057
dir_03/                            0.44 %   39.5MiB    41409583
some_file.dat                      0.06 %    5.2MiB     5406862
dir_04/                            0.02 %    1.5MiB     1612598
other_file.dat                     0.01 %  662.9KiB      678798
```

Force recomputing the cached tree (or delete the `*.pickle` file):

```
/dropbox_du.py -f  dropbox-index.tsv
```
