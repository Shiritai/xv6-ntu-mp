#include "types.h"
#include "param.h"
#include "memlayout.h"
#include "spinlock.h"
#include "riscv.h"
#include "defs.h"
#include "slab.h"

// TODO: hint 利用 4K 對齊
#define GET_SLAB_FROM(obj) ((struct slab *)((uint64)obj & ~(MP2_SLAB_SIZE - 1)))

void print_slab(struct slab *s, uint size, void (*slab_obj_printer)(void *))
{
  // printf("[SLAB]        [ slab %p ] { freelist: %p, prev: %p, next: %p }\n",
  //   s, s->freelist, s->list.prev, s->list.next);
  printf("[SLAB]        [ slab %p ] { freelist: %p, in_use: %d, prev: %p, next: %p }\n",
    s, s->freelist, s->in_use, s->list.prev, s->list.next);
  // struct run *obj = (struct run *)(s + 1);
  void *obj = (void *) (s + 1);
  for (int i = 0; i < (MP2_SLAB_SIZE - sizeof(struct slab)) / size; i++)
  {
    // read as pointer list
    // printf("[SLAB]            { addr: %p, as_ptr: %p, as_obj: { ", obj, obj->next);
    printf("[SLAB]            { addr: %p, as_ptr: %p, as_obj: { ", obj, *(void **)obj);
    // read as file object
    if (slab_obj_printer)
      slab_obj_printer(obj);
    printf(" } }\n");
    obj = (void *)((char *)obj + size);
  }

  // struct list_head h;
  // const uint counter = ((uint) (&h) >> (sizeof(void *) * 8 - LOG2(MP2_SLAB_SIZE))) & (MP2_SLAB_SIZE - 1);
  // const uint a = sizeof(void *) * 8 - LOG2(MP2_SLAB_SIZE);
}

void print_kmem_cache(struct kmem_cache *cache, void (*slab_obj_printer)(void *))
{
  // TODO: template
  // printf("[SLAB] TODO: print_kmem_cache \n");

  printf("[SLAB] kmem_cache { name: %s, object_size: %d, harden: %d, rand: %d }\n", cache->name, cache->object_size, MP2_FREELIST_HARDENED, MP2_FREELIST_RANDOMIZATION);
  
  struct slab *s;
  printf("[SLAB]    [ Full    slabs (head: %p) ]\n", &cache->full);
  list_for_each_entry(s, &cache->full, list) {
    print_slab(s, cache->object_size, slab_obj_printer);
  }

  printf("[SLAB]    [ Partial slabs (head: %p) ]\n", &cache->partial);
  list_for_each_entry(s, &cache->partial, list) {
    print_slab(s, cache->object_size, slab_obj_printer);
  }

  // printf("[SLAB]    [ Free    slabs (head: %p) ]\n", &cache->free);
  // list_for_each_entry(s, &cache->free, list) {
  //   print_slab(s, cache->object_size, slab_obj_printer);
  // }
}

struct kmem_cache *kmem_cache_create(char *name, uint object_size)
{
  // TODO: kmem_cache_create: ...
  cpuid();
  
  // NOTE: mention "allocating a page for cache" in spec
  struct kmem_cache *cache = (struct kmem_cache *) kalloc();
  if (!cache)
  {
    printf("[SLAB] Failed to create cache: %s\n", name);
    return 0;
  }

  // TODO: mention in spec
  safestrcpy(cache->name, name, sizeof(cache->name));
  // TODO: mention in spec
  cache->object_size = object_size;
  // TODO: mention in spec
  initlock(&cache->lock, name);
  cache->partial_cnt = cache->full_cnt = 0;
  
  INIT_LIST_HEAD(&cache->full);
  INIT_LIST_HEAD(&cache->partial);
  // INIT_LIST_HEAD(&cache->free);
  
  // TODO: mention in spec
  printf("[SLAB] New kmem_cache (name: %s, object size: %d bytes) is created\n", cache->name, cache->object_size);
  
  // TODO: mention in spec
  return cache;
}

void kmem_cache_destroy(struct kmem_cache *cache)
{
  kfree(cache);
}

void *kmem_cache_alloc(struct kmem_cache *cache)
{
  // TODO: kmem_cache_alloc: ...
  
  // TODO: mention in spec, and release before return
  acquire(&cache->lock);
  
  printf("[SLAB] Alloc request on cache %s\n", cache->name);
  
  struct slab *s;
  // 1. 檢查 partial slabs 是否有可用物件
  if (!list_empty(&cache->partial))
  {
    s = list_first_entry(&cache->partial, struct slab, list);
    if (!s->freelist)
    {
      printf("[SLAB] Warning: Partial slab is empty!\n");
      release(&cache->lock);
      return 0;
    }

    void *obj = s->freelist;
    s->freelist = *(void **)obj;
    // struct run *obj = s->freelist;
    // s->freelist = obj->next;
    s->in_use++;

    // if (s->in_use == (MP2_SLAB_SIZE - sizeof(struct slab)) / cache->object_size)
    if (!s->freelist)
    {
      list_del(&s->list);
      --cache->partial_cnt;
      list_add(&s->list, &cache->full);
      ++cache->full_cnt;
      printf("[SLAB] Move partial slab %p to full slabs (%s)\n", s, cache->name);
    }

    release(&cache->lock);
    
    // TODO: mention in spec
    memset(obj, 0, cache->object_size);

    // TODO: mention in spec
    printf("[SLAB] Allocated %p from partial slab (%s)\n", obj, cache->name);
    return obj;
  }

  // 2. 檢查 free slabs 是否有可用 slab
  // if (!list_empty(&cache->free))
  // {
  //   s = list_first_entry(&cache->free, struct slab, list);
  //   list_del(&s->list);

  //   // TODO: mention in spec
  //   printf("[SLAB] Reusing slab %p from free list (%s)\n", s, cache->name);
  // }
  // else
  // {
  //   // 3. 如果沒有可用 slab，則分配新的 slab
  //   s = (struct slab *) kalloc();
  //   if (!s)
  //   {
  //     printf("[SLAB] Error: Failed to allocate new slab for %s\n", cache->name);
  //     release(&cache->lock);
  //     return 0;
  //   }

  //   s->in_use = 0;
    
  //   // TODO: mention in spec
  //   printf("[SLAB] Allocated new slab %p for %s\n", s, cache->name);
  // }

  // 3. 如果沒有可用 slab，則分配新的 slab
  s = (struct slab *) kalloc();
  if (!s)
  {
    printf("[SLAB] Error: Failed to allocate new slab for %s\n", cache->name);
    release(&cache->lock);
    return 0;
  }
  // TODO: mention in spec
  printf("[SLAB] A new slab %p (%s) is allocated\n", s, cache->name);
  
  // 4. 初始化新的 slab
  s->in_use = 0;
  list_add(&s->list, &cache->partial);
  ++cache->partial_cnt;
  s->freelist = (void **)(s + 1); // 將物件可用空間裡最前面的空間設為 freelist 的開頭
  
  // use struct run
  // struct run *obj = s->freelist;
  // for (int i = 0; i < (MP2_SLAB_SIZE - sizeof(struct slab)) / cache->object_size; i++)
  // {
  //   obj->next = (struct run *)((char *)obj + cache->object_size);
  //   obj = obj->next;
  // }
  // obj->next = 0; // mark as the last object
  
  // use void *
  void *obj = s->freelist;
  for (int i = 0; i < (MP2_SLAB_SIZE - sizeof(struct slab)) / cache->object_size - 1; i++)
  {
    *(void **)obj = (void *)((char *)obj + cache->object_size);
    obj = *(void **)obj;
  }
  *(void **)obj = 0; // mark as the last object
  
  // 5. 取得第一個可用物件
  // obj = s->freelist;
  // s->freelist = obj->next;
  obj = s->freelist;
  s->freelist = *(void **)obj;
  s->in_use++;
  
  release(&cache->lock);

  // TODO: mention in spec
  memset(obj, 0, cache->object_size);

  // TODO: mention in spec
  printf("[SLAB] Object %p in slab %p (%s) is allocated and initialized\n", obj, s, cache->name);

  // TODO: mention in spec
  return obj;
}

void kmem_cache_free(struct kmem_cache *cache, void *obj)
{
  // TODO: kmem_cache_free: ...
  
  if (!obj)
  {
    printf("[SLAB] Warning: Attempted to free NULL object (%s)\n", cache->name);
    return;
  }

  // TODO: mention in spec, and release before return
  acquire(&cache->lock);
  struct slab *s = GET_SLAB_FROM(obj);
  
  if (!s)
  {
    printf("[SLAB] Error: No available slabs in %s\n", cache->name);
    release(&cache->lock);
    return;
  }

  printf("[SLAB] Free %p in slab %p (%s)\n", obj, s, cache->name);

  // struct run *as_run = (struct run *) obj;
  // as_run->next = s->freelist;
  // s->freelist = as_run;
  *(void **)obj = s->freelist;
  s->freelist = obj;
  s->in_use--;

  // if (s->type == FULL)
  // if (s->in_use == (MP2_SLAB_SIZE - sizeof(struct slab)) / cache->object_size - 1)
  if (!*(void **)obj) // 若 s->freelist 原本為空, 且 obj 非空 (必然，最前面的邊界條件)
  {
    list_del(&s->list);
    --cache->full_cnt;
    list_add(&s->list, &cache->partial);
    ++cache->partial_cnt;
    printf("[SLAB] Slab %p (%s) is moved from full to partial\n", s, cache->name);
  }
  
  if (s->in_use == 0)
  {
    // if free list exists
    // list_del(&s->list);
    // list_add(&s->list, &cache->free);
    // printf("[SLAB] Slab %p (%s) is moved from partial to free\n", s, cache->name);
    
    // if min available slabs satisfied
    if (cache->partial_cnt > MP2_MIN_AVAIL_SLAB)
    {
      --cache->partial_cnt;
      list_del(&s->list);
      kfree(s);
      printf("[SLAB] Slab %p (%s) is freed due to save memory (%d, %d)\n", s, cache->name, cache->partial_cnt, cache->full_cnt);
    }
  }

  release(&cache->lock);
}
