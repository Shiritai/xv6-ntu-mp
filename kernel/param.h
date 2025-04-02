#pragma once

#define NPROC        64  // maximum number of processes
#define NCPU          8  // maximum number of CPUs
#define NOFILE      200  // open files per process
#define NFILE       100  // open files per system
#define NINODE      200  // maximum number of active i-nodes
#define NDEV         10  // maximum major device number
#define ROOTDEV       1  // device number of file system root disk
#define MAXARG       32  // max exec arguments
#define MAXOPBLOCKS  10  // max # of blocks any FS op writes
#define LOGSIZE      (MAXOPBLOCKS*3)  // max data blocks in on-disk log
#define NBUF         (MAXOPBLOCKS*3)  // size of disk block cache
#define FSSIZE       2000  // size of file system in blocks
#define MAXPATH      128   // maximum file path name
#define USERSTACK    1     // user stack pages

// MP2 Macros that CANNOT BE CHANGED!
#define MP2_DEFAULT_DEBUG_MODE 1 // debug mode on
#define MP2_FILE_MAGIC_N 116
#define MP2_TEST
#define MP2_CACHE_MAX_NAME 16 // Max length of the name of kmem_cache object.
#define MP2_MIN_AVAIL_SLAB 2 // Minimal numbers of available (partial/free) slabs
#define MP2_SLAB_SIZE      PGSIZE // Currently set to 1 page.
