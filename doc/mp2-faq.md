<div align="center">
  <h1>❓ MP2 FAQ - Memory Management: Kernel Memory Allocator (Slab)</h1>
  <h3>CSIE3310 - Operating Systems</h3>
  <h4>National Taiwan University</h4>
</div>

<hr />

This document compiles common questions raised by students during the implementation of MP2 and the answers provided by TAs for other students' reference. This document will be continuously updated.

## 📋 Frequently Asked Questions

### Q1: Output Format and Order for Single partial/cache Slab?

**Student Question:**
Regarding the output of a single partial/in_cache slab, should I only output the blocks currently in the freelist or the entire contents of the slab? The example seems to output everything. If the entire slab is output, what is the order of allocated versus free blocks?

**TA Answer:**
1. The output for a single partial/cache slab must prints all blocks of objects within the slab based on the memory address from low to high. Since these blocks can be interpreted as nxt pointers using as_ptr, or as structured system objects using print_fn. Therefore, if there are a total of 8 blocks, you must print idx 0, 1, 2, ..., 7, regardless of whether each individual block has been allocated.
2. Slab metadata only needs to include the specified fields (e.g., the `nxt` link). Students may add additional metadata to the slab structure (e.g., a `prev` link, object information, etc.) for their own use, but these should not be printed.

### Q2: What is the `nxt` pointer for the slab within `kmem_cache`?

**Student Question:**
When outputting the slab that resides within the `kmem_cache` page, should it be linked to other slabs in a linked list, or will its `nxt` pointer always be 0?

**TA Answer:**
When the `kmem_cache` acts as a slab (the in-cache slab), its **`nxt` pointer is always 0**. It should not be linked to the other `slabs` list via its `nxt` pointer and should be output as its own category.

### Q3: Internal Fragmentation Optimization Details

**Student Question:**
1. If Internal Fragmentation Optimization is implemented, does `kmem_cache_create` require using only the page where the `kmem_cache` struct itself is located?
2. Is the `kmem_cache` page included when calculating the number of slabs for `MP2_MIN_AVAIL_SLAB`?
3. If it is included, and all objects within the in-cache slab are released, should it output `[SLAB] Slab <addr> is freed due to save memory`?

**TA Answer:**
1. Regardless of whether Internal Fragmentation Optimization is implemented, `kmem_cache_create` typically only initializes the single page that contains the `kmem_cache` structure.
2. According to the specification, **`MP2_MIN_AVAIL_SLAB` only counts the number of partial slabs**. It does not consider the in-cache slab or full slabs.
3. Since the `kmem_cache` structure itself occupies the page, the in-cache slab **should not** (and cannot) be freed to reclaim memory.
4. According to the `kmem_cache_alloc` flowchart in the spec: if optimization is implemented and there is available space within the cache, the allocator should **prioritize allocating from the in-cache space**.

### Q4: Output Order Requirements

**Student Question:**
If Internal Fragmentation Optimization is implemented, does the output format require `[SLAB] [ partial slabs ]` or `[SLAB] [ cache slabs ]` to be printed first?

**TA Answer:**
If the optimization is implemented, please **print `cache slabs` first**, followed by `partial slabs`.

## Q5: `max_objs` requirements in `print_kmem_cache`

**Student Question:**
When printing the "Single Slab Status" in print_kmem_cache, should the max_objs field be included for both partial and in-cache slabs? The current example shows it for the cache slab but omits it for partial slabs.

**TA Answer:**
Yes, please include the max_objs field for both partial slabs and in-cache slabs. Please ensure that this item is printed regardless of the slab's state (whether it is currently in the cache or on the partial list).

## Q6: Verification of Slab Randomization

**Student Question:**
If the printed blocks are sorted by memory address (i.e., the addr field increases linearly), wouldn't the randomization verification always appear linear?

**TA Answer:**
The verification is based on the relationship between two specific fields: `addr` and `as_ptr`.
- `addr` / `idx`: These represent the memory location of a specific block in slab. Printing them in increasing order provides a map of the slab's layout.
- `as_ptr`: This field stores the pointer to the next available block, zero when no available block exists.

> [!TIP]
> **Continuous Updates**
>
> If you encounter any ambiguities in the specification during implementation, you are encouraged to post your questions on the MP2 discussion board on NTU COOL. We will synchronize representative questions and answers to this FAQ.
