#pragma once

#include "spinlock.h"
#include "types.h"

// struct run {
//   struct run *next;
// };

/**
 * struct slab - Represents a slab in the slab allocator.
 * @freelist: Linked list of free objects.
 */
struct slab
{
  // TODO: Choose the type of freelist from
  //    1. void **
  //    2. struct run *
  // <ptr> freelist;             // Linked list of free objects

  // TODO: Design how to link the slabs
  // ...

  // TODO: you can add other members
  // ...
};

/**
 * struct kmem_cache - Represents a cache of slabs.
 * @name: Cache name (e.g., "file").
 * @object_size: Size of a single object.
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
