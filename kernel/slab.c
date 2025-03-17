#include "types.h"
#include "param.h"
#include "memlayout.h"
#include "spinlock.h"
#include "riscv.h"
#include "defs.h"
#include "slab.h"
#include "debug.h"

#define GET_SLAB_FROM(obj) ((struct slab *)((uint64)obj & ~(MP2_SLAB_SIZE - 1)))

void print_slab(struct slab *s, uint size, void (*slab_obj_printer)(void *))
{
  debug("[SLAB]        [ slab %p ] { freelist: %p, in_use: %d, prev: %p, nxt: %p }\n",
        s, s->freelist, s->in_use, s->list.prev, s->list.next);
  // struct run *obj = (struct run *)(s + 1);
  void *obj = (void *)(s + 1);
  for (int i = 0; i < (MP2_SLAB_SIZE - sizeof(struct slab)) / size; i++)
  {
    // read as pointer list
    debug("[SLAB]           [ idx %d ] { addr: %p, as_ptr: %p, as_obj: { ", i, obj, *(void **)obj);
    // read as file object
    if (slab_obj_printer)
      slab_obj_printer(obj);
    debug(" } }\n");
    obj = (void *)((char *)obj + size);
  }
}

void print_kmem_cache(struct kmem_cache *cache, void (*slab_obj_printer)(void *))
{
  // TODO: template
  // debug("[SLAB] TODO: print_kmem_cache \n");

#ifdef MP2_IN_CACHE_FREELIST
  debug("[SLAB] kmem_cache { name: %s, object_size: %d, at: %p, in_cache_obj: %lu }\n", cache->name, cache->object_size, cache, (MP2_SLAB_SIZE - sizeof(struct kmem_cache)) / cache->object_size);
  debug("[SLAB]    [ cache    slabs ]\n");
  debug("[SLAB]        [ slab %p ] { freelist: %p, nxt: %p }\n",
        cache, cache->freelist, (void *)0);
  // struct run *obj = (struct run *)(s + 1);
  void *obj = (void *)(cache + 1);
  for (int i = 0; i < (MP2_SLAB_SIZE - sizeof(struct kmem_cache)) / cache->object_size; i++)
  {
    // read as pointer list
    debug("[SLAB]           [ idx %d ] { addr: %p, as_ptr: %p, as_obj: { ", i, obj, *(void **)obj);
    // read as file object
    if (slab_obj_printer)
      slab_obj_printer(obj);
    debug(" } }\n");
    obj = (void *)((char *)obj + cache->object_size);
  }
#else
  debug("[SLAB] kmem_cache { name: %s, object_size: %d, at: %p, in_cache_obj: %d }\n", cache->name, cache->object_size, cache, 0);
#endif // MP2_IN_CACHE_FREELIST

  struct slab *s, *safe;

#ifdef MP2_USE_FULL
  if (!list_empty(&cache->full))
  {
    debug("[SLAB]    [ full    slabs ]\n");
    list_for_each_entry_safe(s, safe, &cache->full, list)
    {
      print_slab(s, cache->object_size, slab_obj_printer);
    }
  }
#endif // MP2_USE_FULL

  if (!list_empty(&cache->partial))
  {
    debug("[SLAB]    [ partial slabs ]\n");
    list_for_each_entry_safe(s, safe, &cache->partial, list)
    {
      print_slab(s, cache->object_size, slab_obj_printer);
    }
  }

#ifdef MP2_USE_FREE
  if (!list_empty(&cache->free))
  {
    debug("[SLAB]    [ free    slabs ]\n");
    list_for_each_entry_safe(s, safe, &cache->free, list)
    {
      print_slab(s, cache->object_size, slab_obj_printer);
    }
  }
#endif // MP2_USE_FREE

  debug("[SLAB] print_kmem_cache end\n");
}

struct kmem_cache *kmem_cache_create(char *name, uint object_size)
{
  // TODO: kmem_cache_create: ...

  // NOTE: mention "allocating a page for cache" in spec
  struct kmem_cache *cache = (struct kmem_cache *)kalloc();
  if (!cache)
  {
    debug("[SLAB] Failed to create cache: %s\n", name);
    return 0;
  }

  safestrcpy(cache->name, name, sizeof(cache->name));
  cache->object_size = object_size;
  initlock(&cache->lock, name);

#ifdef MP2_IN_CACHE_FREELIST
  cache->freelist = (void **)(cache + 1);
  void *obj = cache->freelist;
  for (int i = 0; i < (MP2_SLAB_SIZE - sizeof(struct kmem_cache)) / cache->object_size - 1; i++)
  {
    *(void **)obj = (void *)((char *)obj + cache->object_size);
    obj = *(void **)obj;
  }
  *(void **)obj = 0; // mark as the last object
#endif               // MP2_IN_CACHE_FREELIST

  cache->avail_cnt = 0;

  INIT_LIST_HEAD(&cache->partial);

#ifdef MP2_USE_FULL
  INIT_LIST_HEAD(&cache->full);
#endif // MP2_USE_FULL

#ifdef MP2_USE_FREE
  INIT_LIST_HEAD(&cache->free);
#endif // MP2_USE_FREE

  debug("[SLAB] New kmem_cache (name: %s, object size: %d bytes, at: %p, max objects per slab: %lu, support in cache obj: %lu) is created\n",
        cache->name, cache->object_size, cache, (MP2_SLAB_SIZE - sizeof(struct slab)) / cache->object_size,
#ifdef MP2_IN_CACHE_FREELIST
        (MP2_SLAB_SIZE - sizeof(struct kmem_cache)) / cache->object_size
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
  // TODO: kmem_cache_alloc: ...

  // TODO: mention in spec, and release before return
  acquire(&cache->lock);

  debug("[SLAB] Alloc request on cache %s\n", cache->name);

#ifdef MP2_IN_CACHE_FREELIST
  if (cache->freelist) // kmem_cache 的 freelist 還能用
  {
    void *obj = cache->freelist;
    cache->freelist = *(void **)obj;
    debug("[SLAB] Allocated %p from cache slab (%s)\n", obj, cache->name);
    debug("[SLAB] Object %p in slab %p (%s) is allocated and initialized\n", obj, cache, cache->name);

    release(&cache->lock);
    return obj;
  }
#endif // MP2_IN_CACHE_FREELIST

  struct slab *s;
  // 1. 檢查 partial slabs 是否有可用物件
  if (!list_empty(&cache->partial))
  {
    s = list_first_entry(&cache->partial, struct slab, list);
    if (!s->freelist)
    {
      debug("[SLAB] Warning: Partial slab is empty!\n");
      release(&cache->lock);
      return 0;
    }

    void *obj = s->freelist;
    s->freelist = *(void **)obj;
    s->in_use++;

    if (!s->freelist)
    {
      list_del(&s->list);
      --cache->avail_cnt;
#ifdef MP2_USE_FULL
      list_add(&s->list, &cache->full);
      debug("[SLAB] Move partial slab %p to full slabs (%s)\n", s, cache->name);
#endif // MP2_USE_FULL
    }
    memset(obj, 0, cache->object_size);
    debug("[SLAB] Allocated %p from partial slab (%s)\n", obj, cache->name);
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

    // TODO: mention in spec
    debug("[SLAB] Reusing slab %p from free list (%s)\n", s, cache->name);
  }
  else
#endif // MP2_USE_FREE
  {
    // 3. 如果沒有可用 slab，則分配新的 slab
    s = (struct slab *) kalloc();
    if (!s)
    {
      debug("[SLAB] Error: Failed to allocate new slab for %s\n", cache->name);
      release(&cache->lock);
      return 0;
    }

    s->in_use = 0;
    ++cache->avail_cnt;

    // TODO: mention in spec
    debug("[SLAB] A new slab %p (%s) is allocated\n", s, cache->name);
  }

  // 4. 初始化新的 slab
  list_add(&s->list, &cache->partial);
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
  obj = s->freelist;
  s->freelist = *(void **)obj;
  s->in_use++;

  memset(obj, 0, cache->object_size);
  debug("[SLAB] Object %p in slab %p (%s) is allocated and initialized\n", obj, s, cache->name);

  release(&cache->lock);
  return obj;
}

void kmem_cache_free(struct kmem_cache *cache, void *obj)
{
  // TODO: kmem_cache_free: ...

  if (!obj)
  {
    debug("[SLAB] Warning: Attempted to free NULL object (%s)\n", cache->name);
    return;
  }

  // TODO: mention in spec, and release before return
  acquire(&cache->lock);
  struct slab *s = GET_SLAB_FROM(obj);

  if (!s)
  {
    debug("[SLAB] Error: No available slabs in %s\n", cache->name);
    release(&cache->lock);
    return;
  }

  debug("[SLAB] Free %p in slab %p (%s)\n", obj, s, cache->name);

  // struct run *as_run = (struct run *) obj;
  // as_run->next = s->freelist;
  // s->freelist = as_run;

#ifdef MP2_IN_CACHE_FREELIST
  if ((void *)s == (void *)cache) // 如果是 kmem_cache 中的 object
  {
    *(void **)obj = cache->freelist;
    cache->freelist = obj;
    debug("[SLAB] End of free\n");
    release(&cache->lock);
    return;
  }
#endif // MP2_IN_CACHE_FREELIST

  *(void **)obj = s->freelist;
  s->freelist = obj;
  s->in_use--;

  if (!*(void **)obj) // 若 s->freelist 原本為空, 且 obj 非空 (必然，最前面的邊界條件)
  {
#ifdef MP2_USE_FULL
    list_del(&s->list);
#endif // MP2_USE_FULL

    list_add(&s->list, &cache->partial);
    ++cache->avail_cnt;
    debug("[SLAB] Slab %p (%s) is moved from full to partial\n", s, cache->name);
  }

  if (s->in_use == 0)
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
