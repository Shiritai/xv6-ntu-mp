import abc
import re
import parse
from typing import Any, Literal, Set, Union, List, Dict, Optional, Tuple

import fslab_data_models as models
from fslab_messages import (
    MyMsg, SlabCreateMsg, SlabAllocMsg, SlabFreeMsg, SlabPrintMsg, FileMsg
)
from fslab_utils import normalize_spaces, parse_dict, check_exists

# Slab matcher with pattern definitions
class Matcher(abc.ABC):
    def __init__(self):
        self.datalist: List = []

    @abc.abstractmethod
    def match(self, line: str) -> Optional["MyMsg"]:
        """Match a line and return a debug message if complete."""

    def __call__(self, line: str):
        return self.match(line)

class SlabMatcher(Matcher):
    PATTERNS = {
        models.SlabCreateData: "New kmem_cache (name: {name}, object size: {object_size} bytes, at: {addr}, max objects per slab: {max_objs}, support in cache obj: {in_cache_obj}) is created",
        models.SlabAllocRequestData: "Alloc request on cache {name}",
        models.SlabAllocSlabData: "A new slab {addr} ({name}) is allocated",
        models.SlabAllocObjData: "Object {addr} in slab {slab_addr} ({name}) is allocated and initialized",
        models.SlabFreeObjData: "Free {addr} in slab {slab_addr} ({name})",
        models.SlabFreeSlabData: "Slab {addr} ({name}) is freed due to save memory",
        models.SlabPrintfKmemStatusData: "kmem_cache { name: {name}, object_size: {object_size}, at: {addr}, in_cache_obj: {in_cache_obj} }",
        models.SlabPrintfSlabListStatusData: "[ {slab_type} slabs ]",
        models.SlabPrintfSlabStatusData: "[ slab {addr} ] {kv_pair}",
        models.SlabPrintfObjStatusData: "[ idx {idx} ] { addr: {addr}, as_ptr: {as_ptr}, as_obj: {as_obj} }",
        models.SlabPrinfEndData: "print_kmem_cache end",
    }

    def match(self, line: str) -> Optional["MyMsg"]:
        line = normalize_spaces(line.strip())
        for msg_type, pattern in self.PATTERNS.items():
            match = parse.parse(pattern, line)
            if match:
                if msg_type in (models.SlabCreateData, models.SlabAllocObjData, models.SlabFreeSlabData):
                    self.datalist.append(msg_type(origin=line, **match.named))
                    if msg_type == models.SlabCreateData:
                        return self.encapsulate(SlabCreateMsg)
                    elif msg_type == models.SlabAllocObjData:
                        return self.encapsulate(SlabAllocMsg)
                    elif msg_type == models.SlabFreeSlabData and parse.parse("End of free", line):
                        return self.encapsulate(SlabFreeMsg)
                elif msg_type == models.SlabPrintfSlabStatusData:
                    kv_pair = check_exists(match.named, 'kv_pair', msg_type)
                    addr = check_exists(match.named, 'addr', msg_type)

                    kv_pair = parse_dict(kv_pair)
                    freelist = check_exists(kv_pair, 'freelist', msg_type)
                    nxt = check_exists(kv_pair, 'nxt', msg_type)
                    data = models.SlabPrintfSlabStatusData(origin=line,
                                                    addr=addr,
                                                    freelist=freelist,
                                                    nxt=nxt)
                    self.datalist.append(data)
                elif msg_type == models.SlabPrintfObjStatusData:
                    kv_pair = parse_dict(check_exists(match.named, 'as_obj', msg_type))
                    idx = check_exists(match.named, 'idx', msg_type)
                    addr = check_exists(match.named, 'addr', msg_type)
                    as_ptr = check_exists(match.named, 'as_ptr', msg_type)
                    data = models.SlabPrintfObjStatusData(origin=line,
                                                    idx=idx,
                                                    addr=addr,
                                                    as_ptr=as_ptr,
                                                    as_obj=kv_pair)
                    self.datalist.append(data)
                elif msg_type == models.SlabPrinfEndData:
                    return self.encapsulate(SlabPrintMsg)
                else:
                    self.datalist.append(msg_type(origin=line, **match.named))
                break
        if parse.parse("End of free", line) and any(isinstance(d, models.SlabFreeObjData) for d in self.datalist):
            return self.encapsulate(SlabFreeMsg)
        return None

    def encapsulate(self, msg_type):
        msg = msg_type(*self.datalist)
        self.datalist = []
        return msg


def file_matcher(line: str) -> Optional[FileMsg]:
    for case in FileMsg:
        if line == case.value:
            return case
    return None