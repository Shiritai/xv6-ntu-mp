import json
from typing import Any, Literal, Set, Union, List, Dict, Optional, Tuple

import fslab_models as models
from fslab_models import KmemCache, Slab, Obj
from fslab_messages import SlabMsg, SlabCreateMsg, SlabAllocMsg, SlabFreeMsg, SlabPrintMsg
from fslab_parser import SlabMatcher
from fslab_utils import is_in_same_page

def run_msg(caches: Dict[str, KmemCache], slab_msg: SlabMsg, verbose = False):
    """Execute the given slab debug message and update caches accordingly."""
    
    if verbose:
        print(f"\n<Running> {slab_msg}")

    if isinstance(slab_msg, SlabCreateMsg):
        caches[slab_msg.name] = KmemCache(slab_msg.name,
                                          slab_msg.object_size,
                                          slab_msg.addr,
                                          slab_msg.max_objs,
                                          slab_msg.in_cache_obj)
        assert caches[slab_msg.name].count_allocated_objs() == 0
    elif isinstance(slab_msg, SlabAllocMsg):
        cache = caches.get(slab_msg.name)
        if not cache:
            raise AssertionError(f"KmemCache for {slab_msg.name} does not exist")

        if verbose:
            print(f"Alloc: {slab_msg.name} slab=0x{slab_msg.slab_addr:x} obj=0x{slab_msg.obj_addr:x} new={slab_msg.allocate_new}")
            print("<Debug> Before Alloc:")
            print(cache)
        before_free_cnt = cache.count_allocated_objs()
        
        objs = list(filter(lambda o: not o.allocated, cache.objs))
        # if allocate from in cache obj
        if cache.in_cache_obj != 0 and len(objs) != 0:
            if not is_in_same_page(slab_msg.obj_addr, cache.addr):
                raise AssertionError(f"Invalid in-cache allocation: obj at {slab_msg.obj_addr} is not in {cache.addr}")
            # allocate a object out
            # If addr is known
            changed = False
            for o in objs:
                if o.addr == slab_msg.obj_addr:
                    if not o.allocated:
                        o.allocated = True
                        changed = True
                        break
                    else: # invalid
                        raise AssertionError("Double alloc the same obj inside kmem_cache")
            # If addr in unknown
            if not changed:
                for o in objs:
                    if o.addr == 0: # unknown
                        o.addr = slab_msg.obj_addr
                        o.allocated = True
                        changed = True
                        break
            if not changed:
                raise AssertionError("Unknown in-cache error")
        else:
            if slab_msg.allocate_new and (cache.free or cache.partial):
                raise AssertionError("Cannot allocate new slab when free or partial slabs exist")
            if not slab_msg.allocate_new and not (cache.free or cache.partial):
                raise AssertionError("No available slabs to allocate object")

            cur_slab = (Slab(slab_msg.slab_addr, cache.max_objs) if slab_msg.allocate_new else
                        cache.free.get(slab_msg.slab_addr) or cache.partial.get(slab_msg.slab_addr))
            if not cur_slab:
                raise AssertionError("Invalid slab address for allocation")

            if slab_msg.allocate_new:
                cache.partial[slab_msg.slab_addr] = cur_slab
            
            if slab_msg.obj_addr in cur_slab.objs and cur_slab.objs[slab_msg.obj_addr].allocated:
                raise AssertionError("Double allocate object")
            cur_slab.objs[slab_msg.obj_addr] = Obj(slab_msg.obj_addr)
            cur_slab.objs[slab_msg.obj_addr].allocated = True

            if cur_slab.count_avail_objs() == 0:
                cache.partial.pop(cur_slab.addr)
                cache.full[cur_slab.addr] = cur_slab
            if cur_slab.addr in cache.free:
                cache.free.pop(cur_slab.addr)
                cache.partial[cur_slab.addr] = cur_slab

        if verbose:
            print("<Debug> After Alloc:")
            print(cache)
        after_free_cnt = cache.count_allocated_objs()
        assert before_free_cnt + 1 == after_free_cnt, f"Allocated objs not increment before: {before_free_cnt}, after: {after_free_cnt}"

    elif isinstance(slab_msg, SlabFreeMsg):
        cache = caches.get(slab_msg.name)
        if not cache:
            raise AssertionError(f"KmemCache for {slab_msg.name} does not exist")

        if verbose:
            print(f"Free: {slab_msg.name} slab=0x{slab_msg.slab_addr:x} obj=0x{slab_msg.obj_addr:x} free_slab={slab_msg.free_slab}")
            print("<Debug> Before Free:")
            print(cache)
        before_free_cnt = cache.count_allocated_objs()
        
        if is_in_same_page(slab_msg.obj_addr, cache.addr):
            changed = False
            for o in cache.objs:
                if o.addr == slab_msg.obj_addr:
                    if not o.allocated:
                        raise AssertionError("Double free in-cache")
                    o.allocated = False
                    changed = True
                    break
            if not changed:
                raise AssertionError("Object is not in in-cache slab")
        else:
            if not (cache.full or cache.partial or cache.free):
                raise AssertionError("KmemCache is empty, nothing to free")
            if slab_msg.slab_addr in cache.free:
                raise AssertionError("Cannot free object from an empty slab")

            cur_slab = cache.partial.get(slab_msg.slab_addr) or cache.full.get(slab_msg.slab_addr)
            if not cur_slab:
                raise AssertionError(f"Slab 0x{slab_msg.slab_addr:x} not found")

            obj = cur_slab.objs.get(slab_msg.obj_addr)
            if not obj:
                raise AssertionError(f"Object 0x{slab_msg.obj_addr:x} not in slab")
            if not obj.allocated:
                raise AssertionError("Object already freed")
            
            obj.allocated = False

            if slab_msg.slab_addr in cache.full:
                cache.full.pop(slab_msg.slab_addr)
                cache.partial[slab_msg.slab_addr] = cur_slab
            elif cur_slab.count_avail_objs() == cache.max_objs:
                cache.partial.pop(slab_msg.slab_addr)
                cache.free[slab_msg.slab_addr] = cur_slab
                if len(cache.free) + len(cache.partial) > 2:
                    if slab_msg.free_slab == 0:
                        raise AssertionError("Should free slab when MP2_MIN_AVAIL_SLAB exceeded")
                    cache.free.pop(slab_msg.free_slab)

        if verbose:
            print("<Debug> After Free:")
            print(cache)
        after_free_cnt = cache.count_allocated_objs()
        assert before_free_cnt == after_free_cnt + 1, f"Allocated objs not decrement before: {before_free_cnt}, after: {after_free_cnt}"
        
    elif isinstance(slab_msg, SlabPrintMsg):
        data_iter = iter(slab_msg.msg_data)
        data = next(data_iter)
        if not isinstance(data, models.SlabPrintfKmemStatusData):
            raise AssertionError(f"Invalid first print data: {data}")
        name = data.name
        obj_size = data.object_size
        in_cache_obj = data.in_cache_obj
        kaddr = data.addr
        if name not in caches:
            raise AssertionError(f"Cache (name: {name}) DNE")
        cache = caches[name]
        if obj_size != cache.obj_size or kaddr != cache.addr or in_cache_obj != cache.in_cache_obj:
            raise AssertionError(f"Cache info in print_kmeme_cache {data} is not the same as that in creation {cache}")

        def consume_one_slab(data, data_iter):
            if not isinstance(data, models.SlabPrintfSlabStatusData):
                raise AssertionError(f"Invalid slab print data: {data}")
            addr = data.addr
            freelist = data.freelist
            nxt = data.nxt
            objs = []
            last_obj_addr = 0

            try:
                data = next(data_iter)
                while isinstance(data, models.SlabPrintfObjStatusData):
                    obj_addr = data.addr
                    if obj_addr < last_obj_addr:
                        raise AssertionError(f"Invalid slab object address {obj_addr}")
                    else:
                        last_obj_addr = obj_addr
                    
                    obj_as_ptr = data.as_ptr
                    obj_as_obj = data.as_obj
                    
                    objs.append({ 'addr': obj_addr, 'as_ptr': obj_as_ptr, 'as_obj': obj_as_obj })
                    data = next(data_iter)
            except StopIteration:
                data = None
            finally:
                if len(objs) != cache.max_objs and not is_in_same_page(addr, cache.addr):
                    raise AssertionError(f"Invalid max_objs: set to {cache.max_objs} but is actually {len(objs)}, you should print all the objects in slab, including those allocaed")
                # check freelist is a linked list
                ptr = freelist
                walked = set()
                while ptr != 0:
                    found = False
                    if ptr in walked:
                        found = True
                        break
                    walked.add(ptr)
                    for o in objs:
                        if o['addr'] == ptr:
                            found = True
                            ptr = o['as_ptr']
                            break
                    if not found:
                        raise AssertionError(f"Invalid objs in slab {addr}: freelist {freelist} structure broken {json.dumps(objs, indent=4)}")
                # check objects in use
                for o in objs:
                    if o['addr'] not in walked:
                        if any(o['as_obj'].get(attr) is None for attr in ('tp', 'ref', 'readable', 'writable')):
                            raise AssertionError(f"Object {o} is in bad format")
                        assert o['as_obj']['tp'] >= 0
                        assert o['as_obj']['ref'] >= 0
                        assert 0 <= o['as_obj']['readable'] <= 1
                        assert 0 <= o['as_obj']['writable'] <= 1
                return data, { 'addr': addr, 'freelist': freelist, 'nxt': nxt, 'objs': objs }

        def consume_one_type(data, data_iter):
            if not isinstance(data, models.SlabPrintfSlabListStatusData):
                raise AssertionError(f"Invalid slab_type print data: {data}")
            slab_type = data.slab_type

            slab_list = []
            data = next(data_iter)
            data, slab = consume_one_slab(data, data_iter)
            slab_list.append(slab)
            while isinstance(data, models.SlabPrintfSlabStatusData):
                data, slab = consume_one_slab(data, data_iter)
                slab_list.append(slab)
            
            nxt = 0
            for slab in slab_list:
                if nxt != 0 and (not is_in_same_page(slab['addr'], nxt) or is_in_same_page(slab['addr'], slab['nxt'])):
                    raise AssertionError("Invalid slab list: they are not linked together")
                nxt = slab['nxt']
            
            return data, slab_type, slab_list

        slabs = {}

        no_printable_slabs = False
        try:
            data = next(data_iter)
        except StopIteration:
            no_printable_slabs = True
        
        if not no_printable_slabs:
            try:
                data, slab_type, slab_list = consume_one_type(data, data_iter)
                slabs[slab_type] = slab_list
                while isinstance(data, models.SlabPrintfSlabListStatusData):
                    data, slab_type, slab_list = consume_one_type(data, data_iter)
                    slabs[slab_type] = slab_list
                    
                assert data is None, "data is not completely consumed"
            except StopIteration:  # means only print a single <slab_type>
                pass
            
            # print(json.dumps(slabs, sort_keys=True, indent=4))
            
            # cache related check
            if cache.in_cache_obj != 0:
                if 'cache' not in slabs:
                    raise AssertionError(f"Invalid slab: you should implement in-cache allocation since {cache.in_cache_obj} is not zero")
                cache_slab = slabs['cache']
                if len(cache_slab) != 1:
                    raise AssertionError(f"Over one in-cache slab")
                cache_slab = cache_slab[0]
                if not is_in_same_page(cache.addr, cache_slab['addr']):
                    raise AssertionError(f"Invalid in-cache slab: bad address")
                if cache_slab['nxt'] != 0:
                    raise AssertionError(f"Invalid in-cache slab: should only have one in-cache slab")
            if cache.in_cache_obj == 0 and 'cache' in slabs:
                raise AssertionError(f"Invalid slab: you should not implement in-cache allocation since {cache.in_cache_obj} is zero")

            # full related check
            if 'full' in slabs:
                full_slabs = slabs['full']
                for slab in full_slabs:
                    assert slab['freelist'] == 0
            
            # check all slabs are equivelent
            def check_slab_eq(_slabs: Dict[int, Slab], printed_slabs: list, name: str):
                for printed_slab in printed_slabs:
                    if printed_slab.get('addr') is None or printed_slab['addr'] not in _slabs:
                        raise AssertionError(f"Invalid print message: {printed_slab} is broken or not in {name}")
                    _slab = _slabs[printed_slab['addr']]
                    # check nxt
                    nil_cnt = 0
                    if printed_slab.get('nxt') is None:
                        if printed_slab['nxt'] == 0:
                            nil_cnt += 1
                        elif printed_slab['nxt'] not in _slabs:
                            raise AssertionError(f"Invalid print message: {printed_slab} is broken since the slabs printed is not a linked list")
                    if nil_cnt > 1:
                        raise AssertionError(f"Invalid print message: slab list has over one nil next pointer")
                        
                    # for obj in printed_slab.get('objs'):
                    #     if obj['addr'] not in _slab.objs:
                    #         raise AssertionError(f"Invalid print message: unknown obj {obj} printed since it's not in {_slab.objs}")

            if len(cache.full) != 0:
                if slabs.get('full') is not None:
                    check_slab_eq(cache.full, slabs["full"], 'full')
            if len(cache.free) != 0:
                if slabs.get('free') is not None:
                    check_slab_eq(cache.free, slabs["free"], 'free')
            if len(cache.partial) != 0:
                if slabs.get('partial') is None:
                    raise AssertionError("Invalid print messsage: partial slabs exists but not shown")
                check_slab_eq({ **cache.partial, **cache.free }, slabs["partial"], 'partial')
            if len(cache.objs) != 0:
                if slabs.get('cache') is None:
                    raise AssertionError("Invalid print messsage: in-cache slab exists but not shown")
                # for obj in slabs['cache'][0].get('objs'):
                #     if obj['addr'] not in cache.objs:
                #         raise AssertionError(f"Invalid print message: unknown obj {obj} printed since it's not in {cache.objs}")
            
        else: # 去掉剛好全部 full + 沒有 cache
            if not (len(cache.full) != 0 and len(cache.free) == 0 and len(cache.objs) == 0):
                if len(cache.partial) != 0:
                    raise AssertionError("Invalid kmem_cache_print: you have partial but is not printed")
                else:
                    raise AssertionError("Invalid print message: kmem_cache is broken: no slabs exists, which is impossible now.")
    else:
        raise AssertionError(f"Invalid debug message {slab_msg}")

    if verbose:
        print("<Info> legal behavior\n")

def interpreter(lines: List[str], verbose = False):
    """Interpret a list of lines and execute slab commands after kernel boot."""
    if verbose:
        print("<Info> Welcome to slab intepreter.\nVersion: 0.2, Author: Shiritai (NTU CSIE).\n")
    
    caches: Dict[str, KmemCache] = {}
    slab_msg: Optional[SlabMsg] = None
    booted = False
    slab_matcher = SlabMatcher()
    magic = "[SLAB]"
    failed_magics = ("panic: ", "[MP2] <FAILED>")
    run_cnt = [0, 0, 0, 0]
    expected_print_cnt = 0
    msg_types = (SlabCreateMsg, SlabAllocMsg, SlabFreeMsg, SlabPrintMsg)
    
    for line in map(str.strip, lines):
        if line == "xv6 kernel is booting":
            booted = True
        if booted:
            if verbose:
                print(line)
            
            mp2_msg_cnt = line.count(" mp2")
            oap_msg_cnt = line.count(" oap")
            expected_print_cnt += mp2_msg_cnt + oap_msg_cnt
            for failed_magic in failed_magics:
                if line.startswith(failed_magic):
                    err_msg = f"Invalid xv6 state <{line}>"
                    if len(slab_matcher.datalist) != 0:
                        err_msg += f", remained debug message to parse: {slab_matcher.datalist}"
                    raise AssertionError(err_msg)

            if line.startswith(magic):
                matched = slab_matcher.match(line[len(magic):])
                if matched:
                    if isinstance(matched, msg_types):
                        slab_msg = matched
                        run_msg(caches, slab_msg, verbose)
                        run_cnt[msg_types.index(type(matched))] += 1

    if run_cnt[0] == 0:
        raise AssertionError(f"Slab creation is not working or in bad format, please check the implementation.")
    if run_cnt[1] == 0:
        raise AssertionError(f"Slab allocation is not working or in bad format, please check the implementation.")
    if run_cnt[2] == 0:
        raise AssertionError(f"Slab free is not working or in bad format, please check the implementation.")
    if run_cnt[3] != expected_print_cnt:
        if run_cnt[3] == 0:
            raise AssertionError(f"Slab print is not working or in bad format, please check the implementation.")
        else:
            raise AssertionError(f"Slab print should be {expected_print_cnt} times, got {run_cnt} times")

    if len(slab_matcher.datalist) != 0:
        raise AssertionError(f"Invalid remaining debug message: {slab_matcher.datalist}")
    
    file_cache_name = list(filter(lambda k: k.startswith('f'), caches.keys()))
    if len(file_cache_name) == 0:
        raise AssertionError(f"kmem_cache (named starting from 'f') does not exist!")
    file_cache_name = file_cache_name[0]

    return (caches[file_cache_name].max_objs, caches[file_cache_name].in_cache_obj)