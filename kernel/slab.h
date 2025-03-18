#pragma once

#include "spinlock.h"
#include "types.h"

// adjust the following definition to...
#define MP2_IN_CACHE_FREELIST // use in-cache freelist
#define MP2_USE_FULL          // use full slab list
#define MP2_USE_FREE          // use free slab list

// struct run {
//   struct run *next;
// };

/**
 * struct slab - Represents a slab in the slab allocator.
 * @freelist: Linked list of free objects.
 * @in_use: Number of allocated objects.
 * @list: List pointer for linking slabs in the cache.
 */
struct slab
{
  // TODO: Choose the type of freelist from
  //    1. void **
  //    2. struct run *
  void **freelist; // Linked list of free objects
  // struct run *freelist;        // Linked list of free objects

  // TODO: Design how to link the slabs
  // struct slab *next;
  // struct slab *prev;
  struct list_head list; // List pointer for linking slabs in the cache

  // TODO: you can add other members
  // ...
  unsigned short in_use; // Number of allocated objects
};

/**
 * struct kmem_cache - Represents a cache of slabs.
 * @name: Cache name (e.g., "file").
 * @object_size: Size of a single object.
 * @full: Completely allocated slabs.
 * @partial: Partially allocated slabs.
 * @lock: Lock for cache management.
 */
struct kmem_cache
{
  char name[32];        // Cache name (e.g., "file")
  uint object_size;     // Size of a single object
  struct spinlock lock; // Lock for cache management

  // TODO: Add slab list(s)
  // <TYPE> full     // Completely allocated slabs (Optional)
  // <TYPE> partial  // Partially allocated slabs
  // <TYPE> free     // Free slabs (Optional)
  struct list_head partial; // Partially allocated slabs
  uint avail_cnt;

#ifdef MP2_USE_FULL
  struct list_head full; // Completely allocated slabs
#endif                   // MP2_USE_FULL

#ifdef MP2_USE_FREE
  struct list_head free; // Free slabs
#endif                   // MP2_USE_FREE

#ifdef MP2_IN_CACHE_FREELIST
  void **freelist; // Linked list of free objects
#endif             // MP2_IN_CACHE_FREELIST
};

/**
 * kmem_cache_create - Create a new slab cache.
 * @name: The name of the cache.
 * @object_size: The size of each object in the cache.
 *
 * Return: A pointer to the new cache.
 */
struct kmem_cache *kmem_cache_create(char *name, uint object_size);

/**
 * kmem_cache_destroy - Destroy a slab cache.
 * @cache: The cache to be destroyed.
 */
void kmem_cache_destroy(struct kmem_cache *cache);

/**
 * kmem_cache_alloc - Allocate an object from a slab cache.
 * @cache: The cache to allocate from.
 *
 * Return: A pointer to the allocated object.
 */
void *kmem_cache_alloc(struct kmem_cache *cache);

/**
 * kmem_cache_free - Free an object back to its slab cache.
 * @cache: The cache to free to.
 * @obj: The object to free.
 */
void kmem_cache_free(struct kmem_cache *cache, void *obj);

/**
 * print_kmem_cache - Print the details of a kmem_cache.
 * @cache: The cache to print.
 * @print_fn: Function to print each object in the cache. If NULL (0) is given, will skip object printing part.
 */
void print_kmem_cache(struct kmem_cache *cache, void (*print_fn)(void *));
