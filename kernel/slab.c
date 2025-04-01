#include "types.h"
#include "param.h"
#include "memlayout.h"
#include "spinlock.h"
#include "riscv.h"
#include "defs.h"
#include "slab.h"
#include "debug.h"

// Mask to extract the lower 39 bits of a pointer, ensuring compatibility with the xv6 memory layout.
#define XV6_PTR_MASK 0x0000007FFFFFFFFFULL

// Bit-shifting constants for tracking the number of allocated objects in a slab.
#define IN_USE_SHIFT 39ULL
#define IN_USE_MASK (0x0fffULL << IN_USE_SHIFT)

// Bit-shifting constants for tracking the total number of allocated objects in a slab.
#define ALLOC_LEN_SHIFT ((uint64)(IN_USE_SHIFT + PGSHIFT))
#define ALLOC_LEN_MASK (0x0fffULL << ALLOC_LEN_SHIFT)

// Retrieves the slab structure from an object pointer by aligning it to the start of the slab.
#define __get_slab_from(obj) ((struct slab *)((uint64)obj & ~(MP2_SLAB_SIZE - 1)))

// Extracts the freelist pointer from the slab metadata by masking out non-pointer bits.
#define __get_freelist_from(ptr) \
  ((void **)((uint64)(ptr)->metadata & XV6_PTR_MASK))

// Updates the freelist pointer in the slab metadata while preserving other metadata bits.
#define __set_freelist_into(ptr, n_list)                                    \
  ((ptr)->metadata = ((void **)(((uint64)(ptr)->metadata & ~XV6_PTR_MASK) | \
                                ((uint64)(n_list) & XV6_PTR_MASK))))

// Retrieves the number of currently allocated objects in a slab.
#define __get_inuse_from(ptr) \
  (((uint64)(ptr)->metadata & IN_USE_MASK) >> IN_USE_SHIFT)

// Sets the number of allocated objects in a slab while preserving other metadata bits.
#define __set_inuse_into(ptr, n_inuse)                                     \
  ((ptr)->metadata = ((void **)(((uint64)(ptr)->metadata & ~IN_USE_MASK) | \
                                (((uint64)(n_inuse) << IN_USE_SHIFT) & IN_USE_MASK))))

// Increments the count of allocated objects in a slab.
#define __increment_inuse_of(ptr) \
  __set_inuse_into(ptr, __get_inuse_from(ptr) + 1)

// Decrements the count of allocated objects in a slab.
#define __decrement_inuse_of(ptr) \
  __set_inuse_into(ptr, __get_inuse_from(ptr) - 1)

// Retrieves the total number of allocated objects in the slab.
#define __get_alloc_len_from(ptr) \
  (((uint64)(ptr)->metadata & ALLOC_LEN_MASK) >> ALLOC_LEN_SHIFT)

// Sets the total number of allocated objects in a slab.
#define __set_alloc_len_into(ptr, n_alloc_len)                                \
  ((ptr)->metadata = ((void **)(((uint64)(ptr)->metadata & ~ALLOC_LEN_MASK) | \
                                (((uint64)(n_alloc_len) << ALLOC_LEN_SHIFT) & ALLOC_LEN_MASK))))

// Increments the total allocation count for a slab.
#define __increment_alloc_len_of(ptr) \
  __set_alloc_len_into(ptr, __get_alloc_len_from(ptr) + 1)

// Get max objects with `type` and `object_size`
#define __get_max_objs_with(type, object_size) \
  ((MP2_SLAB_SIZE - sizeof(type)) / object_size)

// Allocates memory for a new slab/cache structure and initializes its metadata to zero.
#define __kalloc_and_init_metadata(ptr) \
  do                                    \
  {                                     \
    ptr = (void *)kalloc();             \
    ptr->metadata = 0;                  \
  } while (0)

// Allocates an object from the slab. It first tries to allocate from the preallocated memory region;
// if full, it retrieves an object from the freelist.
#define __alloc_one_from(ptr, obj, object_size)                    \
  do                                                               \
  {                                                                \
    uint alloc_to = __get_alloc_len_from(ptr);                     \
    if (alloc_to < __get_max_objs_with(typeof(*ptr), object_size)) \
    { /* Allocate from preallocated slab space */                  \
      obj = (void *)((uint64)(ptr + 1) + alloc_to * object_size);  \
      __increment_alloc_len_of(ptr);                               \
    }                                                              \
    else                                                           \
    { /* Allocate from the free list */                            \
      obj = __get_freelist_from(ptr);                              \
      __set_freelist_into(ptr, *(void **)obj);                     \
    }                                                              \
    __increment_inuse_of(ptr);                                     \
  } while (0)

// Frees an object by adding it back to the freelist and decreasing the usage count.
#define __free_one_back(ptr, obj)             \
  do                                          \
  {                                           \
    *(void **)obj = __get_freelist_from(ptr); \
    __set_freelist_into(ptr, obj);            \
    __decrement_inuse_of(ptr);                \
  } while (0)

// Checks if there is available space in a slab for allocation.
#define __can_alloc(ptr, object_size) \
  (__get_inuse_from(ptr) < __get_max_objs_with(typeof(*ptr), object_size))

/**
 * Generates a function to print information about a slab or cache structure.
 * The function is named `print_<CACHE_NAME>`, where `<CACHE_NAME>` is the macro parameter.
 *
 * @param ptr              Pointer to the `CACHE_TYPE` structure.
 * @param object_size      Size of objects stored in the cache/slab.
 * @param nxt              Pointer to the next slab (used for linked list traversal).
 * @param slab_obj_printer Function pointer to a custom object printer for debugging.
 *
 * The function prints the metadata of the cache/slab, including the freelist, the total number
 * of objects that can be stored, and details about each allocated object. It ensures that
 * all potential object slots are allocated and then freed to accurately reflect the slab state.
 */
#define gen_printer(CACHE_TYPE, CACHE_NAME)                                                               \
  void print_##CACHE_NAME(CACHE_TYPE *ptr, uint object_size, void *nxt, void (*slab_obj_printer)(void *)) \
  {                                                                                                       \
    void *obj;                                                                                            \
    while (__get_alloc_len_from(ptr) < __get_max_objs_with(typeof(*ptr), object_size))                    \
    {                                                                                                     \
      __alloc_one_from(ptr, obj, object_size);                                                            \
      __free_one_back(ptr, obj);                                                                          \
    }                                                                                                     \
    debug("[SLAB]        [ slab %p ] { freelist: %p, nxt: %p, max_objs: %lu }\n",                         \
          ptr, __get_freelist_from(ptr), nxt, __get_max_objs_with(typeof(*ptr), object_size));            \
                                                                                                          \
    obj = (void *)(ptr + 1);                                                                              \
    for (int i = 0; i < __get_max_objs_with(typeof(*ptr), object_size); i++)                              \
    {                                                                                                     \
      debug("[SLAB]           [ idx %d ] { addr: %p, as_ptr: %p, as_obj: { ", i, obj, *(void **)obj);     \
      if (slab_obj_printer)                                                                               \
        slab_obj_printer(obj);                                                                            \
      debug(" } }\n");                                                                                    \
      obj = (void *)((uint64)obj + object_size);                                                          \
    }                                                                                                     \
  }

gen_printer(struct slab, slab);
gen_printer(struct kmem_cache, cache);

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
  __kalloc_and_init_metadata(cache);
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

  debug("[SLAB] New kmem_cache (name: %s, object size: %d bytes, at: %p, max objects per slab: %lu, support in cache obj: %lu) is created\n",
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
}

void *kmem_cache_alloc(struct kmem_cache *cache)
{
  acquire(&cache->lock);
  debug("[SLAB] Alloc request on cache %s\n", cache->name);

#ifdef MP2_IN_CACHE_FREELIST
  if (__can_alloc(cache, cache->object_size)) // kmem_cache 的 freelist 還能用
  {
    void *obj;
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
    void *obj;
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

  // 2. 檢查 free slabs 是否有可用 slab
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

  void *obj;
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
    debug("[SLAB] Warning: Attempted to free NULL object (%s)\n", cache->name);
    return;
  }

  acquire(&cache->lock);
  struct slab *s = __get_slab_from(obj);

  if (!s)
  {
    debug("[SLAB] Error: No available slabs in %s\n", cache->name);
    release(&cache->lock);
    return;
  }

  debug("[SLAB] Free %p in slab %p (%s)\n", obj, s, cache->name);

#ifdef MP2_IN_CACHE_FREELIST
  if ((void *)s == (void *)cache) // 如果是 kmem_cache 中的 object
  {
    __free_one_back(cache, obj);
    debug("[SLAB] End of free\n");
    release(&cache->lock);
    return;
  }
#endif // MP2_IN_CACHE_FREELIST

  __free_one_back(s, obj);

  // 若 s->metadata 原本為空, 且 obj 非空 (必然，最前面的邊界條件)
  if (__get_inuse_from(s) == __get_max_objs_with(typeof(*s), cache->object_size) - 1)
  {
#ifdef MP2_USE_FULL
    list_del(&s->list);
#endif // MP2_USE_FULL

    list_add(&s->list, &cache->partial);
    ++cache->avail_cnt;
    debug("[SLAB] Slab %p (%s) is moved from full to partial\n", s, cache->name);
  }

  if (__get_inuse_from(s) == 0)
  {
    // if free list exists
#ifdef MP2_USE_FREE
    list_del(&s->list);
    list_add(&s->list, &cache->free);
    debug("[SLAB] Slab %p (%s) is moved from partial to free\n", s, cache->name);
#endif // MP2_USE_FREE

    // if min available slabs satisfied
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
