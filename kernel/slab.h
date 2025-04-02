#pragma once

#include "spinlock.h"
#include "types.h"
#include "list.h"

/* Preprocessor configurations */
#define MP2_IN_CACHE_FREELIST /**< Enable in-cache freelist management. */
#define MP2_USE_FULL          /**< Maintain a list of fully allocated slabs. */
#define MP2_USE_FREE          /**< Maintain a list of free slabs. */

/**
 * struct slab - Represents a slab in the slab allocator.
 * @list: List head for linking slabs within the cache.
 * @metadata: Metadata to manage the linked list of free objects.
 *
 * The metadata is a 64-bit value containing:
 * - freelist (12 bits): Offset to the next free object.
 * - inuse (12 bits): Number of allocated objects in the slab.
 * - seq_alloc_n (12 bits): Sequential allocation counter for O(1) allocation.
 */
struct slab
{
  struct list_head list; /**< List head for linking slabs in the cache. */
  uint64 metadata;       /**< Metadata for managing free objects. */
};

/**
 * struct kmem_cache - Represents a memory cache for slab allocation.
 * @name: Name of the cache (e.g., "file").
 * @object_size: Size of a single object within the cache.
 * @avail_cnt: Count of available slabs.
 * @lock: Spinlock for cache management synchronization.
 * @partial: List head for partially allocated slabs.
 * @metadata: (Optional) Free object management metadata if MP2_IN_CACHE_FREELIST is defined.
 * @full: (Optional) List of completely allocated slabs if MP2_USE_FULL is defined.
 * @free: (Optional) List of free slabs if MP2_USE_FREE is defined.
 */
struct kmem_cache
{
  char name[MP2_CACHE_MAX_NAME]; /**< Name of the cache. */
  uint16 object_size;            /**< Size of a single object. */
  uint16 avail_cnt;              /**< Count of available slabs. */
  struct spinlock lock;          /**< Spinlock for cache management. */
  struct list_head partial;      /**< List of partially allocated slabs. */

#ifdef MP2_IN_CACHE_FREELIST
  uint64 metadata; /**< Metadata for managing free objects in the cache. */
#endif             /* MP2_IN_CACHE_FREELIST */

#ifdef MP2_USE_FULL
  struct list_head full; /**< List of fully allocated slabs. */
#endif                   /* MP2_USE_FULL */

#ifdef MP2_USE_FREE
  struct list_head free; /**< List of free slabs. */
#endif                   /* MP2_USE_FREE */
};

/**
 * kmem_cache_create - Create a new slab cache.
 * @name: The name of the cache.
 * @object_size: The size of each object in the cache.
 *
 * Return: A pointer to the newly created kmem_cache.
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
 * print_kmem_cache - Print details of a kmem_cache.
 * @cache: The cache to print.
 * @print_fn: Function to print each object in the cache.
 *            If NULL, object printing is skipped.
 */
void print_kmem_cache(struct kmem_cache *cache, void (*print_fn)(void *));
