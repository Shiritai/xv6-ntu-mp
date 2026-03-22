#include "types.h"
#include "param.h"
#include "memlayout.h"
#include "spinlock.h"
#include "riscv.h"
#include "defs.h"
#include "slab.h"

void print_kmem_cache(struct kmem_cache *cache, void (*slab_obj_printer)(void *))
{
  // TODO: Implement print_kmem_cache
  printf("[SLAB] TODO: print_kmem_cache is not yet implemented \n");
}

struct kmem_cache *kmem_cache_create(char *name, uint object_size)
{
  // TODO: Implement kmem_cache_create
  printf("[SLAB] TODO: kmem_cache_create is not yet implemented \n");
  
  struct kmem_cache *cache;
  cache = 0;
  return cache;
}

void kmem_cache_destroy(struct kmem_cache *cache)
{
  // TODO: Implement kmem_cache_destroy (will not be tested)
  printf("[SLAB] TODO: kmem_cache_destroy is not yet implemented \n");
}

void *kmem_cache_alloc(struct kmem_cache *cache)
{
  // TODO: Implement kmem_cache_alloc
  printf("[SLAB] TODO: kmem_cache_alloc is not yet implemented \n");
  
  // acquire(&cache->lock); // acquire the lock before modification
  // ... (modify kmem_cache)
  // release(&cache->lock); // release the lock before return
  return 0;
}

void kmem_cache_free(struct kmem_cache *cache, void *obj)
{
  // TODO: Implement kmem_cache_free
  printf("[SLAB] TODO: kmem_cache_free is not yet implemented \n");

  // acquire(&cache->lock); // acquire the lock before modification
  // ... (modify kmem_cache)
  // release(&cache->lock); // release the lock before return
}
