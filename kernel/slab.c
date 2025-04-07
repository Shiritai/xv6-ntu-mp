#include "types.h"
#include "param.h"
#include "memlayout.h"
#include "spinlock.h"
#include "riscv.h"
#include "defs.h"
#include "slab.h"
#include "debug.h"

// Mask to extract a single metadata slot using bitwise masking.
// Each slot should be equivalent to the size of a `kmem_cache/slab` minus 1,
// ensuring alignment with the allocation unit.
#define META_SLOT_MASK ((uint64)MP2_SLAB_SIZE - 1)

// Bit-mask and shift constants for tracking object allocations in `kmem_cache/slab`.
#define IN_USE_SHIFT PGSHIFT                         // Shift amount indicating whether an object is in use.
#define IN_USE_MASK (META_SLOT_MASK << IN_USE_SHIFT) // Mask for extracting the in-use status of an object.

#define SEQ_ALLOC_LEN_SHIFT (IN_USE_SHIFT + PGSHIFT)               // Shift amount for tracking the allocated object size.
#define SEQ_ALLOC_LEN_MASK (META_SLOT_MASK << SEQ_ALLOC_LEN_SHIFT) // Mask for extracting the allocated length of an object.

// Retrieves the base kmem_cache/slab address of an object.
// This ensures proper slab alignment by masking out `META_SLOT_MASK`.
#define __get_slab_from(obj) ((uint64)(obj) & ~META_SLOT_MASK)

// Extracts the freelist pointer from `kmem_cache/slab` metadata.
// If the `metadata` contains a valid slot value, compute the freelist address;
// otherwise, return `NULL`.
#define __get_freelist_from(ptr)                                               \
  ((void **)(((ptr)->metadata & META_SLOT_MASK)                                \
                 ? (((ptr)->metadata & META_SLOT_MASK) | __get_slab_from(ptr)) \
                 : 0))

// Updates the freelist pointer in `kmem_cache/slab` metadata.
// Clears the existing `META_SLOT_MASK` bits before setting the new freelist address.
#define __set_freelist_as(ptr, n_list)                      \
  ((ptr)->metadata = (((ptr)->metadata & ~META_SLOT_MASK) | \
                      ((uint64)(n_list) & META_SLOT_MASK)))

// Retrieves the number of allocated objects in a `kmem_cache/slab`.
// Extracts the in-use count by applying the `IN_USE_MASK` and shifting.
#define __get_inuse_from(ptr) \
  (((ptr)->metadata & IN_USE_MASK) >> IN_USE_SHIFT)

// Updates the allocation count in a `kmem_cache/slab`.
// Clears the previous in-use count bits and sets the new value.
#define __set_inuse_as(ptr, n_inuse)                     \
  ((ptr)->metadata = (((ptr)->metadata & ~IN_USE_MASK) | \
                      (((uint64)(n_inuse) << IN_USE_SHIFT) & IN_USE_MASK)))

// Increments the allocation count by one.
#define __increment_inuse_of(ptr) \
  __set_inuse_as(ptr, __get_inuse_from(ptr) + 1)

// Decrements the allocation count by one.
#define __decrement_inuse_of(ptr) \
  __set_inuse_as(ptr, __get_inuse_from(ptr) - 1)

// Retrieves the length of sequentially allocated objects in a `kmem_cache/slab`.
// Extracts the sequential allocation count using `SEQ_ALLOC_LEN_MASK`.
#define __get_seq_alloc_len_from(ptr) \
  (((ptr)->metadata & SEQ_ALLOC_LEN_MASK) >> SEQ_ALLOC_LEN_SHIFT)

// Updates the sequential allocation count in the `kmem_cache/slab` metadata.
// Clears the previous allocation length bits and sets the new value.
#define __set_seq_alloc_len_as(ptr, n_seq_alloc_len)            \
  ((ptr)->metadata = (((ptr)->metadata & ~SEQ_ALLOC_LEN_MASK) | \
                      (((uint64)(n_seq_alloc_len) << SEQ_ALLOC_LEN_SHIFT) & SEQ_ALLOC_LEN_MASK)))

// Increments the sequential allocation count by one.
#define __increment_seq_alloc_len_of(ptr) \
  __set_seq_alloc_len_as(ptr, __get_seq_alloc_len_from(ptr) + 1)

// Computes the maximum number of objects that can fit in a `kmem_cache/slab`.
// This is calculated by subtracting metadata size from the slab size
// and dividing the remaining space by the object size.
#define __get_max_objs_with(type, object_size) \
  ((MP2_SLAB_SIZE - sizeof(type)) / object_size)

// Checks whether the given number is within the maximum capacity of the `kmem_cache/slab`.
#define __less_than_max_objs(num, ptr, object_size) \
  ((num) < __get_max_objs_with(typeof(*ptr), (object_size)))

// Allocates memory for a new `kmem_cache/slab` and initializes its metadata.
// Calls `kalloc()` and sets metadata to zero. Panics if allocation fails.
#define __kalloc_and_init_metadata(ptr) \
  do                                    \
  {                                     \
    ptr = (typeof(ptr))kalloc();        \
    if (!ptr)                           \
      panic("slab kalloc failed");      \
    ptr->metadata = 0;                  \
  } while (0)

// Allocates an object from a `kmem_cache/slab`.
// Prefers sequential allocation before falling back to the freelist.
#define __alloc_one_from(ptr, obj, object_size)                   \
  do                                                              \
  {                                                               \
    uint alloc_to = __get_seq_alloc_len_from(ptr);                \
    if (__less_than_max_objs(alloc_to, ptr, object_size))         \
    {                                                             \
      obj = (void *)((uint64)(ptr + 1) + alloc_to * object_size); \
      __increment_seq_alloc_len_of(ptr);                          \
    }                                                             \
    else                                                          \
    {                                                             \
      obj = __get_freelist_from(ptr);                             \
      __set_freelist_as(ptr, *(void **)obj);                      \
    }                                                             \
    __increment_inuse_of(ptr);                                    \
  } while (0)

// Frees an object by returning it to the freelist.
// Updates the freelist pointer and decrements the allocation count.
#define __free_one_back(ptr, obj)             \
  do                                          \
  {                                           \
    *(void **)obj = __get_freelist_from(ptr); \
    __set_freelist_as(ptr, obj);              \
    __decrement_inuse_of(ptr);                \
  } while (0)

// Determines if a `kmem_cache/slab` has available space for allocation.
// Compares the current in-use count against the maximum capacity.
#define __can_alloc(ptr, object_size) \
  __less_than_max_objs(__get_inuse_from(ptr), ptr, object_size)

/**
 * Generates a function to print slab/cache metadata and object details.
 * The function is named `print_<CACHE_NAME>`.
 *
 * @param ptr Pointer to the `CACHE_TYPE` structure.
 * @param object_size Size of objects stored in the cache/slab.
 * @param nxt Pointer to the next slab (for linked list traversal).
 * @param slab_obj_printer Function pointer for printing object details.
 */
#define gen_printer(CACHE_TYPE, CACHE_NAME)                                                               \
  void print_##CACHE_NAME(CACHE_TYPE *ptr, uint object_size, void *nxt, void (*slab_obj_printer)(void *)) \
  {                                                                                                       \
    void *obj;                                                                                            \
    while (__less_than_max_objs(__get_seq_alloc_len_from(ptr), ptr, object_size))                         \
    { /* If sequential allocation is not finished, allocate and free immediately to finish it */          \
      __alloc_one_from(ptr, obj, object_size);                                                            \
      __free_one_back(ptr, obj);                                                                          \
    }                                                                                                     \
    debug("[SLAB]        [ slab %p ] { freelist: %p, nxt: %p, max_objs: %lu }\n",                         \
          ptr, __get_freelist_from(ptr), nxt, __get_max_objs_with(typeof(*ptr), object_size));            \
    obj = (void *)(ptr + 1);                                                                              \
    for (int i = 0; __less_than_max_objs(i, ptr, object_size); i++)                                       \
    {                                                                                                     \
      debug("[SLAB]           [ idx %d ] { addr: %p, as_ptr: %p, as_obj: { ", i, obj, *(void **)obj);     \
      if (slab_obj_printer)                                                                               \
        slab_obj_printer(obj);                                                                            \
      debug(" } }\n");                                                                                    \
      obj = (void *)((uint64)obj + object_size);                                                          \
    }                                                                                                     \
  }

gen_printer(struct slab, slab);
#ifdef MP2_IN_CACHE_FREELIST
gen_printer(struct kmem_cache, cache);
#endif

void print_kmem_cache(struct kmem_cache *cache, void (*slab_obj_printer)(void *))
{
  acquire(&cache->lock);

#ifdef MP2_IN_CACHE_FREELIST
  debug("[SLAB] kmem_cache { name: %s, object_size: %d, at: %p, in_cache_obj: %lu }\n",
        cache->name, cache->object_size, cache, __get_max_objs_with(typeof(*cache), cache->object_size));
  debug("[SLAB]    [ cache    slabs ]\n");
  print_cache(cache, cache->object_size, (void *)0, slab_obj_printer);
#else
  debug("[SLAB] kmem_cache { name: %s, object_size: %d, at: %p, in_cache_obj: %d }\n",
        cache->name, cache->object_size, cache, 0);
#endif // MP2_IN_CACHE_FREELIST

  struct slab *s, *safe;

#ifdef MP2_USE_FULL
  if (!list_empty(&cache->full))
  {
    debug("[SLAB]    [ full    slabs ]\n");
    list_for_each_entry_safe(s, safe, &cache->full, list)
    {
      print_slab(s, cache->object_size, s->list.next, slab_obj_printer);
    }
  }
#endif // MP2_USE_FULL

  if (!list_empty(&cache->partial))
  {
    debug("[SLAB]    [ partial slabs ]\n");
    list_for_each_entry_safe(s, safe, &cache->partial, list)
    {
      print_slab(s, cache->object_size, s->list.next, slab_obj_printer);
    }
  }

#ifdef MP2_USE_FREE
  if (!list_empty(&cache->free))
  {
    debug("[SLAB]    [ free    slabs ]\n");
    list_for_each_entry_safe(s, safe, &cache->free, list)
    {
      print_slab(s, cache->object_size, s->list.next, slab_obj_printer);
    }
  }
#endif // MP2_USE_FREE

  debug("[SLAB] print_kmem_cache end\n");
  release(&cache->lock);
}

struct kmem_cache *kmem_cache_create(char *name, uint object_size)
{
  struct kmem_cache *cache;

#ifdef MP2_IN_CACHE_FREELIST
  __kalloc_and_init_metadata(cache);
#else
  cache = (struct kmem_cache *)kalloc();
#endif // MP2_IN_CACHE_FREELIST

  safestrcpy(cache->name, name, sizeof(cache->name));
  cache->object_size = object_size;
  cache->avail_cnt = 0;
  initlock(&cache->lock, name);
  INIT_LIST_HEAD(&cache->partial);

#ifdef MP2_USE_FULL
  INIT_LIST_HEAD(&cache->full);
#endif // MP2_USE_FULL

#ifdef MP2_USE_FREE
  INIT_LIST_HEAD(&cache->free);
#endif // MP2_USE_FREE

  debug("[SLAB] New kmem_cache (name: %s, "
        "object size: %d bytes, at: %p, max objects per slab: %lu, "
        "support in cache obj: %lu) is created\n",
        cache->name, cache->object_size, cache, __get_max_objs_with(struct slab, cache->object_size),
#ifdef MP2_IN_CACHE_FREELIST
        __get_max_objs_with(struct kmem_cache, cache->object_size)
#else
        0UL
#endif
  );

  return cache;
}

void kmem_cache_destroy(struct kmem_cache *cache)
{
  struct slab *s, *safe;
  list_for_each_entry_safe(s, safe, &cache->partial, list)
  {
    kfree(s);
  }

#ifdef MP2_USE_FULL
  list_for_each_entry_safe(s, safe, &cache->full, list)
  {
    kfree(s);
  }
#endif // MP2_USE_FULL

#ifdef MP2_USE_FREE
  list_for_each_entry_safe(s, safe, &cache->free, list)
  {
    kfree(s);
  }
  kfree(cache);
#endif // MP2_USE_FREE

  kfree(cache);
}

void *kmem_cache_alloc(struct kmem_cache *cache)
{
  acquire(&cache->lock);
  debug("[SLAB] Alloc request on cache %s\n", cache->name);
  void *obj;

#ifdef MP2_IN_CACHE_FREELIST
  if (__can_alloc(cache, cache->object_size))
  {
    __alloc_one_from(cache, obj, cache->object_size);
    debug("[SLAB] Object %p in slab %p (%s) is allocated and initialized\n", obj, cache, cache->name);
    release(&cache->lock);
    return obj;
  }
#endif // MP2_IN_CACHE_FREELIST

  struct slab *s;
  if (!list_empty(&cache->partial))
  {
    s = list_first_entry(&cache->partial, struct slab, list);
    __alloc_one_from(s, obj, cache->object_size);
    if (!__can_alloc(s, cache->object_size))
    {
      list_del(&s->list);
      --cache->avail_cnt;
#ifdef MP2_USE_FULL
      list_add(&s->list, &cache->full);
#endif // MP2_USE_FULL
    }
    memset(obj, 0, cache->object_size);
    debug("[SLAB] Object %p in slab %p (%s) is allocated and initialized\n", obj, s, cache->name);
    release(&cache->lock);
    return obj;
  }

#ifdef MP2_USE_FREE
  if (!list_empty(&cache->free))
  {
    s = list_first_entry(&cache->free, struct slab, list);
    list_del(&s->list);
    s->metadata = 0;
  }
  else
#endif // MP2_USE_FREE
  {
    __kalloc_and_init_metadata(s);
    ++cache->avail_cnt;
    debug("[SLAB] A new slab %p (%s) is allocated\n", s, cache->name);
  }

  list_add(&s->list, &cache->partial);

  __alloc_one_from(s, obj, cache->object_size);
  memset(obj, 0, cache->object_size);
  debug("[SLAB] Object %p in slab %p (%s) is allocated and initialized\n", obj, s, cache->name);
  release(&cache->lock);
  return obj;
}

void kmem_cache_free(struct kmem_cache *cache, void *obj)
{
  if (!obj)
  {
    debug("[slab] Warning: Attempted to free NULL object (%s)\n", cache->name);
    return;
  }

  acquire(&cache->lock);
  struct slab *s = (struct slab *)__get_slab_from(obj);

  if (!s)
  {
    debug("[slab] Error: No available slabs in %s\n", cache->name);
    release(&cache->lock);
    return;
  }

  debug("[SLAB] Free %p in slab %p (%s)\n", obj, s, cache->name);

#ifdef MP2_IN_CACHE_FREELIST
  if ((void *)s == (void *)cache)
  {
    __free_one_back(cache, obj);
    debug("[SLAB] End of free\n");
    release(&cache->lock);
    return;
  }
#endif // MP2_IN_CACHE_FREELIST

  __free_one_back(s, obj);

  if (__get_inuse_from(s) == __get_max_objs_with(typeof(*s), cache->object_size) - 1)
  {
#ifdef MP2_USE_FULL
    list_del(&s->list);
#endif // MP2_USE_FULL

    list_add(&s->list, &cache->partial);
    ++cache->avail_cnt;
    debug("[slab] Slab %p (%s) is moved from full to partial\n", s, cache->name);
  }

  if (__get_inuse_from(s) == 0)
  {
#ifdef MP2_USE_FREE
    list_del(&s->list);
    list_add(&s->list, &cache->free);
    debug("[slab] Slab %p (%s) is moved from partial to free\n", s, cache->name);
#endif // MP2_USE_FREE

    if (cache->avail_cnt > MP2_MIN_AVAIL_SLAB)
    {
      --cache->avail_cnt;
      list_del(&s->list);
      kfree(s);
      debug("[SLAB] Slab %p (%s) is freed due to save memory\n", s, cache->name);
    }
  }

  debug("[SLAB] End of free\n");
  release(&cache->lock);
}
