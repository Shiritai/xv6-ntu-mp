#pragma once

#include "spinlock.h"
#include "types.h"
#include "list.h"

// adjust the following definition to...
#define MP2_IN_CACHE_FREELIST // use in-cache freelist
#define MP2_USE_FULL          // use full slab list
#define MP2_USE_FREE          // use free slab list

/**
 * struct slab - Represents a slab in the slab allocator.
 * @metadata: Metadata in a slab.
 * @list: List pointer for linking slabs in the cache.
 */
struct slab
{
  void **metadata;       // Linked list of free objects
  struct list_head list; // List pointer for linking slabs in the cache
};

/**
 * struct kmem_cache - Represents a cache of slabs.
 * @name: Cache name (e.g., "file").
 * @object_size: Size of a single object.
 * @partial: Partially allocated slabs.
 * @lock: Lock for cache management.
 * @avail_cnt: Available slab counter.
 */
struct kmem_cache
{
  char name[MP2_CACHE_MAX_NAME]; // Cache name (e.g., "file")
  uint16 object_size;            // Size of a single object
  uint16 avail_cnt;              // Available slab count
  struct spinlock lock;          // Lock for cache management

#ifdef MP2_IN_CACHE_FREELIST
  void **metadata;          // Linked list of free objects
#endif                      // MP2_IN_CACHE_FREELIST
  struct list_head partial; // Partially allocated slabs
#ifdef MP2_USE_FULL
  struct list_head full; // Completely allocated slabs
#endif                   // MP2_USE_FULL
#ifdef MP2_USE_FREE
  struct list_head free; // Free slabs
#endif                   // MP2_USE_FREE
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
