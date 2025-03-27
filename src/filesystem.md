## Table of Contents

1. Background and Design Details
    - [I-Nodes](#i-nodes)
    - [D-Blocks](#d-blocks)
    - [I-Node and D-Block: The Big Picture](#i-nodes-and-d-blocks-the-big-picture)

## I-Nodes

I-Nodes store:
- File type (file or a directory)
- File permissions
- File name (Maximum 14 characters)
- File size
- Indices for the data D-blocks associated with the file. These D-blocks are called direct (due to their direct access via the inode).
- Index to the first index D-block associated with the file. The D-blocks 
stored within the this index D-block and any subsequent index D-blocks
are referred to as indirect (due to their indirect access via thie inode).

There are a maximum of four direct D-blocks that can be associated
with an inode.

Any data in a file should be stored first in the direct data D-blocks.
All extra data will be stored within the index

File name storage:
- Maximum size is 14 characters
- If the size of the name is less than 14 characters, we use the null terminating character.
- If the length of the name is exactly 14 characters, we do not use
the null terminating character. We already know the maximum size
of the string.

> [!INFORMATION]
> The above format is how all file names are stored throughout this project. 

## D-Blocks

D-blocks are short for data block referencing a block of memory
that is used for data. 

The size of a data block is 64 bytes.

There are two main types of D-blocks:
1. Data D-blocks
    - These D-blocks actually store the contents of the file.
2. Index D-blocks
    - These D-blocks store 15 indices to data D-blocks and 1
    index to another index D-block
    - These D-blocks are used to store references to other
    data D-blocks. This ultimately allows an inode to refer
    to any number of D-blocks as long as there are enough of them.

Reiterating, in the context of inodes, there are two types of D-blocks:
1. Direct D-blocks. These are accessible directly from the inode struct. 
    - Since all direct D-blocks are data D-blocks, we can assume direct D-blocks are 
    data D-blocks when direct D-blocks are mentioned.
    - The indices to these D-blocks are stored in the `direct_data` field of `inode_internal`
2. Indirect D-block. These are accessible indirectly via the index D-block
in the inode struct called `indirect_dblock`. 

## I-Nodes and D-Blocks (The big picture)

References to inodes and D-blocks are stored via indices. Since the inodes
and D-blocks are stored in contiguous memory, we can use indices into the arrays to
reference them:
- Inode indices are stored in a 16-bit integer.
- D-block indices are stored in a 32-bit integer.

The big picture: file is used here loosely to refer to both files and directories. 
- Inodes store the metadata of a file.
- D-blocks store the actual contents of a file.
    - To allow inodes to have large file sizes, index D-blocks are used to
    chain references to data D-blocks.
    - Inodes contain references to D-blocks
- Files are referred to via their inodes (each file has one inode). The inodes allow
access to metadata about the file and contains references to content of the file (via the D-block indices).
    - Therefore, we can obtain all this information (metadata and file content) from a reference to an inode.
- All allocations to D-blocks are done on demand, meaning D-blocks are allocated only
if they are going to be used and written to.
    - This prevents overallocation which is important on a filesystem where D-blocks
    should be conserved.
- From the size of the file, which is stored in the inode, we can know exactly how
many D-blocks are allocated. We can use this information to find all the D-blocks
associated with a file. 

> [!NOTE]
> Because how we keep track of which D-block and inode is available to be used is different, there are observations about allocation and deallocation that can be made:
> 1. The order of allocation and deallocation matters for inodes. They do not matter for D-blocks
> 2. To restore the state of the inode free list after N inode allocations, all N inodes must be deallocated in reverse order.
> 3. To restore the state of the D-block bitmask after N D-block allocations, the order of the N deallocations do not matter.


> [!IMPORTANT]
> Similarly memory allocated on the heap, we do not want to allocate inodes and D-blocks and then lose access to them before we deallocate them. Your program should not leak any inodes nor D-blocks. Additionally, we do not want to allocate more inodes and D-blocks than needed. 
>
> Parts of this assignment will check if you allocate the correct i-node and D-block (we check the indices). Make sure that you are allocating inodes and D-blocks only if you truly need to. 


How files are stored?
- There are a maximum number of 4 direct D-blocks in an inode.
    - This means there can be maximum 256 bytes that can be stored in these data D-blocks.
    - The first 256 bytes of a file is stored within these D-blocks.
    - A direct D-block can only be allocated and written to with file data
    if any previous direct data D-block are filled.
    - Let $N$ be the file size. For example:
        - If $N=0$, no direct D-blocks are used.
        - If $N\in(0,64]$, the first direct D-blocks are used.
        - If $N\in(64, 128]$, the first and second direct D-blocks are used. The first 64 bytes of the file are in the first direct D-block and the second 64 bytes are in the second.
        - et cetera.
- Indirect D-blocks are used only the file size exceeds the maximum capacity that
can be stored in the direct data blocks. 
    - The inode refer to the first index D-block in this case. Index D-blocks store
    references to more data D-blocks and another index D-blocks if needed. 
    - There can be 15 indices stored to data D-blocks (in a data block of 64 bytes, we can have 16 indices stored. One is reserved for the next index D-block, leaving 15).
    Index slot will be used to refer to the 4 bytes of memory reserved to store the data D-block index.
    - The 15 indices store the index of any allocated data block that is needed to store the contents of the file.
        - Since each of the 15 indices store a data D-block, an indirect D-block can store a maximum of $15\cdot64=960$ bytes of data, ignoring the next indirect D-block in the chain.
    - An index slot in the index D-block can only be written to if all earlier index slots are filled.
    - If all index slots in an index D-block are filled and there is more data in the file, the reference to the next index D-block is used. This reference is stored in the last 4 bytes of the current index D-block.
        - This will refer to at most the next 960 bytes of the file.
        - This process is repeated until the end of the file. 
        - This creates a chain of index D-blocks that can be expanded as long as there are enough D-blocks in the system. This allows files to be arbitrarily as large.
    - Let $N$ be the file size. For example:
        - If $N=0$, no direct D-blocks nor any indirect D-blocks are used. 
        - If $N\in(0,256]$, the direct D-blocks are used, but no indirect D-blocks are used.
        - If $N\in(256,256+64]$, the direct D-blocks are used, one index D-block is used. In this indirect index D-block, the first data D-block is used. 
        - If $N\in(256+64, 256+128]$, the direct D-blocks are used, one index D-block is used. In this indirect index D-block, the first two data D-block is used.
        - If $N\in(256, 256+960]$, the direct D-blocks are used, one index D-block is used. The number of data D-blocks used in the index D-block depends on the exact size of the file.
        - If $N\in(256+960, 256+2\cdot 960]$, the direct D-blocks are used, two index D-blocks are used. The first index D-block is filled. The number of data D-blocks used in the second index D-block (referenced via the first) is
        determined by the exact size of the file.

### Example D-blocks

The indices of the data D-blocks of the file (in sequential order) is:
- 2, 3, 7, 10, 12, 13, 14, 18, 19, 20, 22, 25, 30, 31, 33, 34, 47, 48, 49, 56, 57, 60
The index D-blocks of the file (in sequential order) is:
- 11, 52

Let X be any data. The value here does not matter.

Direct Data D-blocks (stored in the inode)

| Direct D-block # | D-block Index | 
| :-: | :-: |
| 0 | 2 |
| 1 | 3 |
| 2 | 7 |
| 3 | 10 |

Indirect Index D-block 11

| Bytes | D-block Type | D-block Index |
| :-: | :-: | :-: |
| 0-3 | Data | 12 |
| 4-7 | Data | 13 |
| 8-11 | Data | 14 |
| 12-15 | Data | 18 |
| 16-19 | Data | 19 |
| 20-23 | Data | 20 |
| 24-27 | Data | 22 |
| 28-31 | Data | 25 | 
| 32-35 | Data | 30 |
| 36-39 | Data | 31 |
| 40-43 | Data | 33 |
| 44-47 | Data | 34 |
| 48-51 | Data | 47 |
| 52-55 | Data | 48 |
| 56-59 | Data | 49 |
| 60-63 | Index | 52 |

Indirect Index D-block 52

| Bytes | D-block Type | D-block Index |
| :-: | :-: | :-: |
| 0-3 | Data | 56 |
| 4-7 | Data | 57 |
| 8-11 | Data | 60 |
| 12-15 | Data | X |
| 16-19 | Data | X |
| 20-23 | Data | X |
| 24-27 | Data | X |
| 28-31 | Data | X | 
| 32-35 | Data | X |
| 36-39 | Data | X |
| 40-43 | Data | X |
| 44-47 | Data | X |
| 48-51 | Data | X |
| 52-55 | Data | X |
| 56-59 | Data | X |
| 60-63 | Index | X |

> [!NOTE]
> In this assignment, when we are writing data d-blocks to a index d-blocks in this assignment, do not modify the bytes marked X above. They should retain their previous value. Only modify 

## File and Directory Representation

Files
- The inode for the file has file type DATA_FILE
- The file size in the inode is size of the contents of the file
- The name of the file is stored in the inode file name field
- The content of the file is stored in the D-blocks. No extra changes is done to the contents of the file in the D-blocks.

Directories
- The inode for the directory has file type DIRECTORY
- The name of the directory is stored in the inode file name field
- Directories store references to the contents of the directories which are the child items in the directory.
- The references are stored via directory entries which are 16 bytes long. 
    - Directory entry contain two bytes reserved for the inode index of the child item. It is followed by the 14 bytes for 
    the file name of the item. 
    - We repeat the file name within the directory entry because there are directory entries where the name is different from the name in the inode.
    - Directory entries are stored in the data D-blocks of the directory inode.
- The file size field in the directory inode is the number of directory entries times the size of the directory entry.
- Directory entries are used to find the inodes of the child items of a directory. This allows for traversal through the file system and looking through the contents of the directory.
- Every directory (except the root directory which is special) have two special directory entries: the `.` directory entry, referring the current directory, and `..` directory entry, referring to the parent directory.
    - All directories (except the root) begin with these two directory entries. This allows for traversal to ancestor directories.
    - The root directory will only have the `.` directory entry. The root does not have a parent directory.
    - The `.` directory is stored as the first directory entry. The `..` directory is stored as the second directory entry.
    - These entries cannot be removed from a directory. They must always be in a directory (except the root directory which does not have `..` as previously stated)
    - A directory with only these two entries is considered empty even though the inode's file size will be `2 * DIRECTORY_ENTRY_SIZE`, or 32 bytes in this case.
- As child items are added to a directory, directory entries are filled or added as needed.
- When a child item is removed from a directory, the directory entry is replaced with a tombstone which is 16 bytes of zeros. 
    - Any new child item added to a directory will replace the first tombstone in the inode's content if there is any. If there is no tombstone, then the new directory entry will be allocated to the end of the directory inode's content.
    - Any trailing tombstones in a file causes the directory inode file size to shrink and deallocate any data D-blocks as necessary. 
    - NOTE: the tombstone is written before any shrinking occurs, meaning if shrinking occurs, the bytes being truncated from the file should all be zeros. 

### Example Directory Content
I is the inode index. F is the file name. Let X be any byte of data.

Let the directory inode have inode index `0xABCD`. Let the parent directory have inode index `0x1234`. The children items of the
directory are:
- Inode index `0xAE28` with file name `hello.txt`
- Inode index `0x8342` with file name `new.txt`
- Inode index `0x3311` with file name `a.txt` 

> [!NOTE]
> The directory entries shown below may not be contiguous in memory. They may be split among different data D-blocks that are scattered across the file system. For example, while entries 0-3 will be contiguous in memory (they would belong to the same data D-block), entry 4 may not be since it may be in a different D-block.

| Entry\Byte | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 | 13 | 14 | 15 |
| :-: | :-: | :-: | :-: | :-: | :-: | :-: | :-: | :-: | :-: | :-: | :-: | :-: | :-: | :-: | :-: | :-: |
| *Template* | I | I | F | F | F | F | F | F | F | F | F | F | F | F | F | F |
| 0 | `CD` | `AB` | `.` | `\0` | X | X | X | X | X |  X | X | X | X | X | X | X |
| 1 | `34` | `12` | `.` | `.` | `\0` | X | X | X | X | X | X | X | X | X | X | X |
| 2 | `28` | `AE` | `h` | `e` | `l` | `l` | `o` | `.` | `t` | `x` | `t` | `\0` | X | X | X | X |
| 3 | `42` | `83` | `n` | `e` | `w` | `.` | `t` | `x` | `t` | `\0` | X | X | X | X | X | X |
| 4 | `11` | `33` | `a` | `.` | `t` | `x` | `t` | `\0` | X | X | X | X | X | X | X | X | 

> [!NOTE]
> In this assignment, when we are writing to a directory in this assignment, do not modify the bytes marked X above. They should retain their previous value. 
 

## File System Overview

- The first inode of the file system is the root directory.
    - The root directory has a directory entry named `.` that refers to the current directory.
    - As a result, the root inode also allocates the first D-block to store the directory entry. 
- The root directory is the entry point into the file system. From the root directory, we can traverse through all the files and directories from the root.

## Assignment Overview

This project is broken into four parts: part 0, part 1, part 2, and part 3. Each part
has their own test cases. 

> [!WARNING]
> For this assignment, **do not** print anything to standard output a function like `printf` or `puts` unless the function description explicitly states so. Test cases will check standard output to determine if your program is behaving correctly and extraneous output will cause the test to fail (leading to lower scores). 
>
> If you do any print debugging, instead use the `info` macro defined in `debug.h`. This macro will print to standard error which is not checked by the test cases. See `debug.h` for more information.

**Part 0**: This part of the assignment is optional and the code is provided for you already. Therefore, the test cases for part 0 should all pass immediately upon creating the repository. There are no points given for completing this part on your own. However, you should be familiar with the functions and what they do as they will become crucial in the later parts of the project. Because part 0 is provided, part 0 can be implemented at any point in time during the assignment.

**Part 1**: This part of the assignment is required. This part involves manipulation of the data stored in the D-blocks of an inode. The functions defined here serve as a layer of abstraction, and after these functions are correctly implemented, later parts do not need to be concerned with how D-blocks work (we can simply call one of these functions here). This should be the first part of the assignment (outside of part 0) which should be completed before moving on. However, this part is (likely) the most tricky part of the assignment. It is recommended to understand D-blocks fully before attempting to implement these functions.

**Part 2**: This part of the assignment is required. This part involves implementing high level file IO operations that include opening, writing, reading, and closing a file. Part 2 does not need to be completed immediately after part 1, but it is recommended because if part 1 is correctly implemented, this is likely the easiest part of the whole project. However, you can complete part 3 before part 2. 

**Part 3**: This part of the assignment is required. This part involves implementing high level file system operations such as creating files and directories and more. This part requires the functions implemented in part 1 and part 2, and it can be immediately completed after those two parts. 

> [!WARNING]
> For this assignment, do not modify bytes of the file system unnecessarily as this will cause you to fail test cases. For example, if a function requires setting the directory entry name to ".", then no other bytes after the null terminating character in the entry name should be modified.

## Part 0+1 Structs

```C
typedef struct filesystem
{   
    inode_index_t available_inode; 
    inode_t *inodes;
    size_t inode_count;
    byte *dblock_bitmask;
    byte *dblocks;
    size_t dblock_count;
} filesystem_t;
```

The `filesystem_t::inodes` data member is an array of `filesystem_t::inode_count` inodes, each represented via the union `inode_t`. The `filesystem_t::dblocks` data member is an array of bytes of size `filesystem_t::dblock_count` multiplied by the size of a D-block (64 bytes). The `filesystem_t::dblock_bitmask` is a bitmask of bytes whose bits represent if a D-block is available or is being used by a file. The `filesystem_t::available_inode` is an index to an available inode.  

The number of bytes allocated in the `filesystem_t::dblock_bitmask` array is enough bytes to store `filesystem_t::dblock_count` number of bits. Therefore, the size of the bitmask is $\lceil \text{dblockcount} / 8 \rceil$. The bit mask is divided into 8-bit integers. Within the 8-bit integer, the higher order bit represent a lower D-bock index. For example:

| Byte:Bit | D-block Index |
| :-: | :-: |
| 0:7 | 0 |
| 0:6 | 1 | 
| 0:5 | 2 |
| 0:4 | 3 |
| 0:3 | 4 |
| 0:2 | 5 |
| 0:1 | 6 | 
| 0:0 | 7 |
| 1:7 | 8 |
| 1:6 | 9 | 
| 1:5 | 10 |
| 1:4 | 11 |
| 1:3 | 12 |
| 1:2 | 13 |
| 1:1 | 14 | 
| 1:0 | 15 |


```C
struct inode_internal
{
    file_type_t file_type;
    permission_t file_perms;
    char file_name[MAX_FILE_NAME_LEN];
    size_t file_size;
    dblock_index_t direct_data[INODE_DIRECT_BLOCK_COUNT];
    dblock_index_t indirect_dblock;
};

typedef union inode
{
    inode_index_t next_free_inode;
    struct inode_internal internal;
} inode_t;
```

`inode_t` is a union of `inode_internal` and an inode index. The `inode_interal` stores all the contents associated with an inode. The inode index is an index to the next available inode. If the inode is currently being used, only `inode_internal` field of the union should be used. If the inode is currently not being used in the file system, the `next_free_inode` field of the union should be used.
- The inode index field creates a free list (we use indices into an array instead of pointers). Since free `inode_t` can reference the next `inode_t`, this creates a linked list that allows iteration through all the available inodes.
- The head of the free list is accessed via `filesystem_t::available_inode`
- The free list is terminated by a inode_t whose `inode_t::next_free_inode` is 0. We can use `0` as a terminating condition because the inode index of `0` refers to the root directory which will always be in use and can never be released. 
- This linked free list data structure must be maintained as this is the mechanism used to allocate and deallocate inodes. 

## Part 0 Functions

```C
fs_retcode_t new_filesystem(filesystem_t *fs, size_t inode_total, size_t dblock_total);
```
- `fs` is the address to the file system to initialize the new file system.
- Create a new file system with the maximum number of inodes being `inode_total` and the maximum number of D-blocks being `dblock_total`.
- If `NULL` is passed into `fs`, then return `INVALID_INPUT` immediately. 
- If `inode_total` or `dblock_total` is zero, them return `INVALID_INPUT` immedately.
- Will dynamically allocate `inode_total` number of inodes and `dblock_total`
number of D-blocks (each are 64 bytes).
- Will dynamically allocate the necessary number of bytes to stores `dblock_total` number of bits for the `dblock_bitmask` field of the file system. All the bits of the bitmask should be set to 1 (including the bits that would not correspond to any D-block because its out of range).
- Allocate the first inode which is reserved for the root directory.
    - The inode's file type should be set to DIRECTORY
    - The inode's permission is set to read, write, and execute.
    - The first direct D-block is set to D-block index 0. This corresponds to the fact that the first D-block is used to store the contents of the root directory.
    - The inode's file size is set to the size of one directory entry.
    - The file name of the inode is set to `root`. 
- All `inode_t` elements except the first inode have their `next_free_inode` set to the inode index of the subsequent inode in the array.
    - The last inode element has its `next_free_inode` set to 0 to mark the end of the free list.
- The bit corresponding with the first D-block is set to 0 marking that the D-block is used. 
- The directory entry in the root directory inode has the inode index refer to the root directory and the entry name set to `.`. 
- Function returns `SUCCESS` upon completion.

```C
void free_filesystem(filesystem_t *fs);
```
- Frees any dynamically allocated arrays in the file system. 

```C
size_t available_inodes(filesystem_t *fs);
```
- Calculates the number of available inodes in the file system.
- This will require a traversal through the free inodes list which begins in `fs->available_inode`.
- If `fs` is NULL, return 0. 

```C
size_t available_dblocks(filesystem_t *fs);
```
- Calculates the number of D-blocks available in the file system.
- This will require counting the number of 1 bits in the `fs->dblock_bitmask` bitmasks.
- If `fs` is NULL, return 0.

```C
fs_retcode_t claim_available_inode(filesystem_t *fs, inode_index_t *index);
```
- Claims the available inode from `fs->available_inode` and updates `fs->available_inode` to point to the next subsequent available inode (the one pointed to by the claimed inode)
- If we claim the last available inode, `fs->available_inode` should be set to 0.
- `index` should be set to the index of the claimed inode. 
- Possible return values:
    - If `fs` or `index` is NULL, return `INVALID_INPUT`
    - If there are no more available inodes to claim, return `INODE_UNAVAILABLE`
    - If the inode is successfully claimed, return `SUCCESS`

```C
fs_retcode_t claim_available_dblock(filesystem_t *fs, dblock_index_t *index);
```
- Claims the first available D-block in the list of D-blocks.
    - This will require scanning through `fs->dblock_bitmask` for a 1-bit to be set which marks a block as available
- Claiming the block will require clearing the corresponding bit in `fs->dblock_bitmask`.
- `index` should be set to the index of the claimed D-block.
- Possible return values are:
    - If `fs` or `index` is NULL, return `INVALID_INPUT`
    - If there are no more available D-blocks to claim, return `DBLOCK_UNAVAILABLE`
    - If the dblock is successfully claimed, return `SUCCESS`

```C
fs_retcode_t release_inode(filesystem_t *fs, inode_t *inode);
```
- Releases a claimed inode back into the list of free inodes.
- Releasing the claimed inode involves adding the inode to the head of the free inode list (via setting the `fs->available_inode`) and updating `inode->next_free_inode` to point to the old `fs->available_inode`.
- It can be assumed that `inode` points to an inode within `fs`
- Possible return values are:
    - If `fs` or `inode` is NULL, return `INVALID_INPUT`
    - If `inode` is the first inode in the list (i.e. has inode index of 0), return `INVALID_INPUT`
    - If the inode is successfully released and added to the free list, return `SUCCESS`

```C
fs_retcode_t release_dblock(filesystem_t *fs, byte *dblock);
```
- Release a claimed D-block.
- Releasing the claimed D-block involves setting its corresponding bit in the `fs->dblock_bitmask` to 1. 
- It can be assumed that `dblock` points to a dblock within `fs`
- Possible return values are:
    - If `fs` or `dblock` is NULL, return `INVALID_INPUT`
    - If `dblock` does not point to the beginning of a D-block, return `INVALID_INPUT`
    - If the D-block is successfully released, return `SUCCESS`

## Part 1 Functions (inode_manip.c)

```C
fs_retcode_t inode_write_data(filesystem_t *fs, inode_t *inode, void *data, size_t n);
```
- Writes `n` bytes of data from `data` to the data D-blocks of an inode. It allocates D-blocks as necessary.
- Data written is appended and does not modify any existing data in the inode.
- D-blocks are allocated as needed to store the data being written. 
- Allocated D-blocks are stored in the direct D-blocks first before being stored indirectly via index D-blocks
- If there is not enough D-blocks available to store all the data, then the function should do nothing except return `INSUFFICIENT_DBLOCKS`. The state of the file system after the call to the function should be identical to the state of file system before the call.
- Will need to update `inode->internal.file_size` appropriately to reflect the new size of the file.
- This function should not claim any extra D-blocks than is needed. 
- Possible return values are:
    - If `fs` or `inode` is NULL, return `INVALID_INPUT`
    - If there is not enough available D-blocks in the system to satisfy the request, return `INSUFFICIENT_DBLOCKS`
    - If the data is successfully written, return `SUCCESS`

```C
fs_retcode_t inode_read_data(filesystem_t *fs, inode_t *inode, size_t offset, void *buffer, size_t n, size_t *bytes_read);
```
- Reads `n` bytes of data starting from `offset` bytes from the beginning of the contents of `inode`. Stores this data in `buffer`.
- If there are not `n` bytes of data starting from `offset`, only read the number of bytes until the end of the inode.
- Set `bytes_read` to the number of bytes actually read by the function. This should be the number of bytes written to `buffer` as well.
- Possible Return values are:
    - If `fs`, `inode`, or `bytes_read` is NULL, return `INVALID_INPUT`
    - If the read operation was successful, return `SUCCESS`

```C
fs_retcode_t inode_modify_data(filesystem_t *fs, inode_t *inode, size_t offset, void *buffer, size_t n)
```
- Modifies `n` bytes of data starting from `offset` bytes from the beginning of the contents of `inode` with `n` bytes from `buffer`. This can overwrite any pre-existing data.
- Any bytes that would modify bytes beyond the contents of the inode should be treated as appending to the end of the inode. The inode should allocate D-blocks as necessarily similarly to `inode_write_data`.
- If the operation would require claiming more D-blocks than there is available, then the function should do nothing except return `INSUFFICIENT_DBLOCK` similarly with `inode_write_data`. The state of the file system after the call to the function should be identical to the state of file system before the call.
- Will need to update `inode->internal.file_size` appropriately if there is data appended.
- This function should not claim any extra D-blocks than is needed. 
- Possible return values are:
    - If `fs` or `inode` is NULL, return `INVALID_INPUT`
    - If the offset exceeds the inode file size, return `INVALID_INPUT`
    - If there is not enough available D-blocks in the system to satisfy the request, return `INSUFFICIENT_DBLOCKS`
    - If the data is successfully modifed, return `SUCCESS`

```C
fs_retcode_t inode_shrink_data(filesystem_t *fs, inode_t *inode, size_t new_size);
```
- Shrinks the file size of the inode, releasing any D-blocks as necessary. 
- The function should shrink the contents of the inode from the end. 
- This function should release data D-blocks if necessary and index D-blocks if all the D-blocks whose index is stored in the index D-block have been freed. 
- Possible return values are:
    - If `fs` or `inode` is NULL, return `INVALID_INPUT`
    - If the new size exceeds the inode size, return `INVALID_INPUT`
    - If the inode is shrunk successfully, return `SUCCESS`

```C
fs_retcode_t inode_release_data(filesystem_t *fs, inode_t *inode);
```
- Releases all the D-blocks (direct D-blocks, data D-blocks, and index D-blocks) that are associated with a file.
- Sets the inode size to 0 (Since there is no data associated with the inode now)
- Possible return values are:
    - If `fs` or `inode` is NULL, return `INVALID_INPUT`
    - If all the inode data is successfully released, return `SUCCESS`

## Part 2+3 Structs and Macros

```C
typedef struct terminal_context
{
    filesystem_t *fs;
    inode_t *working_directory;
} terminal_context_t;

struct fs_file
{
    filesystem_t *fs;
    inode_t *inode;
    size_t offset;
};

typedef struct fs_file *fs_file_t
```
- `terminal_context_t` stores reference to the file system and the current working directory.
    - This will be passed onto functions in parts 2 and 3 which will use this information.
    - `new_terminal` is a function used to initialize the terminal context.
- `fs_file` is a struct that contains information such as the file system, the inode of the file, and the current offset in the file. 
    - This will be passed to high level functions to allow writing and reading to a file.
    - `fs_file_t` is a pointer to an dynamically allocted `fs_file`.

For part 2 and 3, there is the `REPORT_RETCODE` macro defined which accepts a `fs_retcode_t` value. It will output an error message corresponding to the return code to stdout. The functions will describe the retcode which should be passed into this macro and the conditions necessary.

> [!INFORMATION]
> The `REPORT_RETCODE` prints a string to standard out depending on the return code passed into it. Test cases often check this output meaning that if you use a function like `printf` in a function whose instruction does not say to output anything to standard out, you will likely fail the test case. It is recommended to replace these debugging `printf` with the macro `info` defined in `debug.h`

## Parts 2+3 Core Concepts

A path provides directions to a file in the file system. 
- All paths in this assignment are relative paths meaning they are relative to the current working directory which is stored in `terminal_context_t`
- An example of an path is: `path/to/a/file`
- In this assignment, a path is made up of names that are separated by `/`
- There are two main components of a path:
    1. The directory name (or dirname) refers to everything before the last name of a path. Every name that makes up a dirname should be a directory.
        - In the example above, the dirname is `path/to/a`
        - Every subsequent name must be a subdirectory of the previous name except the first name which must be a subdirectory of the current working directory
        - If this is not true, then traversal through the file system will fail
    2. The base name (or basename) refers to the last name of a path. Depending on the context, the basename may refer to a file, a directory, or something that is not in the file system yet. 
        - In the example above, the basename is `file`

## Part 2 Functions (file_operations.c)

```C
void new_terminal(filesystem_t *fs, terminal_context_t *term)
```
- Initializes a new terminal context which is pointed to via `term`.
- The working directory should be set to the root directory of `fs`
- The `term->fs` should be set to `fs`

```C
fs_file_t fs_open(terminal_context_t *context, char *path);
```
- Opens a file found at `path` relative to the working directory in `context` by creating the `fs_file_t` object
- The `fs_file_t` must be dynamically allocated and appropriately set its values.
    - The offset of `fs_file_t` should be set to 0
    - The file system should be copied from the terminal context
    - The inode field must point to the inode of the file opened
- The basename of `path` MUST be a DATA_FILE type
- Return code reporting in the order of precedence (earliest has highest priority):
    1. If the dirname of `path` contains a name which does not exist or whose inode is not a directory inode, report `DIR_NOT_FOUND`. Return `NULL`.
    2. If the basename of `path` does not have a corresponding inode (it may be a directory inode), report `FILE_NOT_FOUND`. Return `NULL`.
    3. If the basename of `path` corresponds to a directory inode, report `INVALID_FILE_TYPE`. Return `NULL`.
- On success, return the allocated and set `fs_file_t` object.

```C
void fs_close(fs_file_t file);
```
- Closes a `fs_file_t` object by deallocated it.
- If `NULL` is passed into the function, do nothing.

```C
size_t fs_read(fs_file_t file, void *buffer, size_t n);
```
- Reads `n` bytes from the `file` starting from the offset set in `file` and stores it in the `buffer`. 
- If `n` bytes from the offset stored in `file` exceeds the file size, read until the end of the file.
- The function returns the number of bytes read, a.k.a the number of bytes written to `buffer`.
- The offset in `file` should be updated appropriately to the new offset after the read.
- If `NULL` is passed into `file`, return `0`.

```C
size_t fs_write(fs_file_t file, void *buffer, size_t n);
```
- Writes `n` bytes into `file` starting from the offset set in `file`.
- If `n` bytes from the offset stored in `file` exceed the file size, the bytes before exceeding the file size will modify the contents of the file. The bytes exceeding the file size will be appended to the end of the file, increasing the size of the file. (Students shoud call `inode_modify_data` function, but I think they should figure that out for themselves)
- If there is not enough D-blocks in the file system to satisfy the write request, return 0.
- The offset in `file` should be updated appropriately to the new offset after the write.
- If `NULL` is passed into `file`, return `0`
- On a successful write, return the number of bytes written

```C
int fs_seek(fs_file_t file, seek_mode_t seek_mode, int offset)
```
- Updates the offset stored in `file` based on the mode `seek_mode` and the `offset`.
- Returns `-1` on failure and `0` on a successful seek operations.
    - If the final offset is less than `0`, this is a failed operation. No changes should be made to `file`, i.e. the state of `file` before the function call must be equal to its state after the function call.
    - If the final offset is greater than the file size, set it to the file size. This is still
    an succesful seek operation. 
- If the seek mode is `FS_SEEK_START`, the `offset` is the offset from the beginning of the file.
- If the seek mode is `FS_SEEK_CURRENT`, the `offset` is the offset from the current offset stored in `file`.
- If the seek mode is `FS_SEEK_END`, the `offset` is the offset from the end of the file. 

## Part 3 Functions (file_operations.c)

```C
int new_file(terminal_context_t *context, char *path, permission_t perms);
```
- Creates a new file at `path` relative to the working directory in `context` with permissions `perms`.
- The basename of `path` is the name of the file being created.
    - If the basename exceed the max file name size, truncate the name to fit.
- The size of the file created should be 0.
- The permissions of the file should be set to `perms`
- The type of the inode should be `DATA_FILE`
- Creating this file should also update its parent directory's directory entries.
    - The entry should replace the earliest tombstone in the directory entries.
    - If there is no tombstones, then the entry should be appended to the end of the directory entries.
- If any error (described below) occur, no file should be created and the file system should not be modified, i.e. the state of the file system before the function call should be the same as the state of the file system after the function call. 
- Return `-1` in case of any error. Return `0` on success.
- If `context` or `path` is NULL, just return `0`.
- The return codes to be reported (errors) in the order of precedence:
    1. If the dirname of `path` contains a name which does not exist or whose inode is not a directory inode, report `DIR_NOT_FOUND`. Return -1.
    2. If the basename of `path` has a corresponding inode (it may be a directory inode), report `FILE_EXIST`. Return -1.
    3. If there is not enough D-blocks in the file system to satisfy the request, report `INSUFFICIENT_DBLOCKS`. Return -1.
    4. If we cannot allocate an inode from the file system, report `INODE_UNAVAILABLE`. Return -1;

```C
int new_directory(terminal_context_t *context, char *path);
```
- Creates a new directory at `path` relative to the working directory in `context`.
- The basename of `path` is the name of the directory being created
    - If the basename exceed the max file name size, truncate the name to fit.
- The permissions of the file should be set to no permissions.
- The type of the inode should be `DIRECTORY`
- The content of the inode should include the special directory entries `.` and `..`
    - The `.` entry should be first. The `..` entry should be second.
    - The inode's file size should reflect the number of bytes in the content of the inode.
- Creating this directory should also update its parent directory's directory entries.
    - The entry should replace the earliest tombstone in the directory entries.
    - If there is no tombstones, then the entry should be appended to the end of the directory entries.
- If any error (described below) occur, no directory should be created and the file system should not be modified, i.e. the state of the file system before the function call should be the same as the state of the file system after the function call. 
- Return `-1` in case of any error. Return `0` on success.
- If `context` or `path` is NULL, just return `0`.
- The return codes to be reported (errors) in the order of precedence:
    1. If the dirname of `path` contains a name which does not exist or whose inode is not a directory inode, report `DIR_NOT_FOUND`. Return -1.
    2. If the basename of `path` has a corresponding inode (it may be a file inode), report `DIRECTORY_EXIST`. Return -1.
    3. If there is not enough D-blocks in the file system to satisfy the request, report `INSUFFICIENT_DBLOCKS`. Return -1.
    4. If we cannot allocate an inode from the file system, report `INODE_UNAVAILABLE`. Return -1;

```C
int remove_file(terminal_context_t *context, char *path);
```
- Removes a file at `path` relative to the working directory in `context`.
- The basename of `path` is the name of the file to be deleted.
    - If the basename exceeds the max file name size, the name of the file is the truncated name.
- Removing the file should also update its parent directory's directory entries.
    - The file's directory entry should be replaced with the tombstone which are filled with all zeros.
    - After replacing the entry with the tombstone, any trailing tombstone in the parent directory should be removed from the parent directory file, i.e. the parent directory's file size should be shrunk to remove the tombstone. 
- If any error (described below) occur, the file should not be removed and the state of the file system before the function call should be the same as the state of the file system after the function call.
- Return `-1` in the case of an error. Return `0` on success. 
- If `context` or `path` is NULL, just return `0`.
- The return codes to be reported (errors) in the order of precedence:
    1. If the dirname of `path` contains a name which does not exist or whose inode is not a directory inode, report `DIR_NOT_FOUND`. Return -1.
    2. If the basename of `path` is a name which does not correspond with an inode or if the inode type is not a `DATA_FILE`, report `FILE_NOT_FOUND`. Return -1.

```C
int remove_directory(terminal_context_t *context, char *path);
```
- Removes a directory at `path` relative to the working directory in `context`.
- The basename of `path` is the name of the directory to be deleted.
    - If the basename exceeds the max file name size, the name of the directory is the truncated name
- We can only remove a directory if it is empty, i.e. the directory only contains special directory entries.
- Removing the directory should also update its parent directory's directory entries.
    - The file's directory entry should be replaced with the tombstone which are filled with all zeros.
    - After replacing the entry with the tombstone, any trailing tombstone in the parent directory should be removed from the parent directory file, i.e. the parent directory's file size should be shrunk to remove the tombstone. 
- If any error (described below) occur, the directory should not be removed and the state of the file system before the function call should be the same as the state of the file system after the function call.
- Return `-1` in the case of an error. Return `0` on success. 
- If `context` or `path` is NULL, just return `0`.
- The return codes to be reported (errors) in the order of precedence:
    1. If the dirname of `path` contains a name which does not exist or whose inode is not a directory inode, report `DIR_NOT_FOUND`. Return -1.
    2. If the basename of `path` is `.` or `..`, report `INVALID_FILENAME`. Return -1.
    3. If the basename of `path` contains a name which does not exist or whose inode type is not a `DIRECTORY`, report `DIR_NOT_FOUND`. Return -1.
    4. If the directory being deleted is not empty, report `DIR_NOT_EMPTY`. Return -1.
    5. If the directory being deleted is the working directory in `context`, retport `ATTEMPT_DELETE_CWD`. Return -1.

```C
int change_directory(terminal_context_t *context, char *path);
```
- Changes the working directory stored in `context` to the `path` relative to the current working directory in `context`.
- The basename of `path` should be a directory.
- If any error (described) occur, the working directory should not be modified, i.e. the state of `context` before the function call should be the same as the state of `context` after the function call. 
- Return `-1` in case of an error. Return `0` on success.
- If `context` or `path` is NULL, just return `0`
- The return codes to be reported (errors) in the order of precedence:
    1. If the dirname of `path` contains a name which does not exist or whose inode is not a directory inode, report `DIR_NOT_FOUND`. Return -1.
    2. If the basename of `path` contains a name which does not exist or whose inode is not a directory inode, report `DIR_NOT_FOUND`. Return -1.

```C
int list(terminal_context_t *context, char *path);
```
- Displays the content of a file or a directory located at `path` relative to the working directory in `context`.
- If the basename of the `path` is a file, display the permissions, file size, and filename of the inode of the file.
- If the basename of the `path` is a directory, display each the directory entries on separate lines treating each child item (both files and directories) of the directory the same manner as the previous bullet point.
    - Even for directories, just display the value stored in the inode file size field as the file size of the directory.
- The formatting of displaying a file is:
    - The first character of the line should be `d` if the inode is a directory or `f` if it is a file. You can use `E` for any other file types (we have no tests for this, should we?)
    - The second character of the line should be `r` if there is read permissions, `-` otherwise.
    - The third character of the line should be `w` if there is write permissions, `-` otherwise.
    - The fourth character of the line should be `x` if there is execute permissions, `-` otherwise. 
    - The next character should be the tab character `\t`. 
    - The next part should be the inode file size displayed as an unsigned long in base 10. 
    - The next character directly after the file size should be the tab character `\t`.
    - The next part should be the file name as stored in the directory entry (if the basename refer to a directory) or in the inode (if basename refer to a file). 
    - If directory entry being displayed is a special directory entry, then display ` -> ` (ONE SPACE BETWEEN AND AFTER) immediately after the previous file name. After the array, display the name of the inode. 
```
SAMPLE OUTPUT
d---    64      . -> a
drwx    160     .. -> root
d---    32      b
d---    32      c
```
- Return `-1` in case of an error. Return `0` on success.
- If `context` or `path` is NULL, just return `0`
- The return codes to be reported (errors) in the order of precedence:
    1. If the dirname of `path` contains a name which does not exist or whose inode is not a directory inode, report `DIR_NOT_FOUND`. Return -1.
    2. If the basename of `path` contains a name which does not exist, report `NOT_FOUND`. Return -1.

```C
char *get_path_string(terminal_context_t *context);
```
- Returns a dynamically allocated string storing the absolute path for the current working directory stored in `context`.
- If `context` is NULL, return a dynamically allocated empty string. 

```C
int tree(terminal_context_t *context, char *path);
```
- Displays a tree representation of the inode. 
- Unlike list which displays only the contents of the current inode, tree displays the contents of the entire subtree begining at the current inode.
  - If the inode is a file, display the name of the file. If the inode is a directory, display all files and directories including any in subdirectories.
- All files within a directory should be displayed in the order of their occurrence in the directory entries in the directory.
- For each depth level from the root of the tree, there is THREE spaces that appears before the file name.
```txt
root
   a
      b
         c
         hello.txt
      d
         text
      password
   book.txt
   book2.txt
```
- Return `-1` in case of an error. Otherwise return `0`.
- If `context` or `path` is NULL, just return `0`
- The return codes to be reported (errors) in the order of precedence:
    1. If the dirname of `path` contains a name which does not exist or whose inode is not a directory inode, report `DIR_NOT_FOUND`. Return -1.
    2. If the basename of `path` contains a name which does not exist, report `NOT_FOUND`. Return -1.