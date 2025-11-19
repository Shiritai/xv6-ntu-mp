from dataclasses import dataclass
from typing import Any, Literal, Set, Union, List, Dict, Optional, Tuple

from slab_utils import hex_to_int, is_in_same_page

@dataclass
class BaseData:
    """Base class for all slab-related data with original string representation."""
    origin: str
    def __str__(self) -> str:
        return self.origin

# Abstract base class: Data structure with address
@dataclass
class AddrData:
    """Base class for data structures with an address field."""
    addr: Union[str, int]
    def __post_init__(self):
        if isinstance(self.addr, str):
            self.addr = hex_to_int(self.addr)

# --- Concrete Log Data Structures ---

@dataclass
class SlabCreateData(BaseData, AddrData):
    """Data for a newly created slab cache."""
    name: str
    object_size: int
    max_objs: int
    in_cache_obj: int
    def __post_init__(self):
        super().__post_init__()
        self.object_size = int(self.object_size)
        self.max_objs = int(self.max_objs)
        self.in_cache_obj = int(self.in_cache_obj)

@dataclass
class SlabAllocRequestData(BaseData):
    name: str

@dataclass
class SlabAllocSlabData(BaseData, AddrData):
    name: str
    # addr: int

@dataclass
class SlabAllocObjData(BaseData, AddrData):
    name: str
    slab_addr: int
    # addr: int
    def __post_init__(self):
        super().__post_init__()
        if isinstance(self.slab_addr, str):
            self.slab_addr = hex_to_int(self.slab_addr)

@dataclass
class SlabFreeObjData(BaseData, AddrData):
    name: str
    slab_addr: int
    # addr: int
    def __post_init__(self):
        super().__post_init__()
        if isinstance(self.slab_addr, str):
            self.slab_addr = hex_to_int(self.slab_addr)

@dataclass
class SlabFreeSlabData(BaseData, AddrData):
    name: str
    # addr: int

@dataclass
class SlabPrintfKmemStatusData(BaseData, AddrData):
    name: str
    object_size: int
    # addr: int
    in_cache_obj: int
    def __post_init__(self):
        super().__post_init__()
        self.object_size = int(self.object_size)
        self.in_cache_obj = int(self.in_cache_obj)

SlabType = Literal['full', 'partial', 'free', 'cache']

@dataclass
class SlabPrintfSlabListStatusData(BaseData):
    slab_type: SlabType

@dataclass
class SlabPrintfSlabStatusData(BaseData, AddrData):
    # addr: int
    freelist: int
    nxt: int

class SlabPrinfEndData(BaseData):
    pass

@dataclass
class SlabPrintfObjStatusData(BaseData, AddrData):
    idx: int
    # addr: int
    as_ptr: int
    as_obj: dict
    def __post_init__(self):
        super().__post_init__()
        self.idx = int(self.idx)
        self.as_ptr = hex_to_int(self.as_ptr)

@dataclass
class ListCheckData(BaseData):
    init: int
    _add: int
    _del: int
    def __post_init__(self):
        super().__post_init__()
        if isinstance(self.init, str):
            self.init = int(self.init)
        if isinstance(self._add, str):
            self._add = int(self._add)
        if isinstance(self._del, str):
            self._del = int(self._del)

# --- Simulator State Models ---

class Obj:
    def __init__(self, obj_addr: int):
        self.addr = obj_addr
        self.allocated = False

    def __str__(self) -> str:
        return f"Obj(addr=0x{self.addr:x}, allocated={self.allocated})"

class Slab:
    def __init__(self, slab_addr: int, max_objs: int):
        self.addr = slab_addr
        self.max_objs = max_objs
        self.objs: Dict[int, Obj] = {}

    def count_avail_objs(self) -> int:
        return len([o for o in self.objs.values() if not o.allocated]) + (self.max_objs - len(self.objs))

    def __str__(self) -> str:
        lines = [
            f"\tSlab(addr=0x{self.addr:x})",
            f"  Objects ({len(self.objs)}):",
        ]
        if not self.objs:
            lines.append("    None")
        else:
            for obj_addr, obj in self.objs.items():
                lines.append(f"    0x{obj_addr:x}: {obj}")
        return "\n\t\t".join(lines)

class KmemCache:
    def __init__(self, name: str, obj_size: int,
                 addr: int, max_objs: int, in_cache_obj: int):
        self.name: str = name
        self.obj_size: int = obj_size
        self.addr: int = addr
        self.max_objs: int = max_objs
        self.in_cache_obj: int = in_cache_obj
        self.objs: Set[Obj] = {}
        self.full: Dict[int, Slab] = {}
        self.partial: Dict[int, Slab] = {}
        self.free: Dict[int, Slab] = {}
        
        if self.in_cache_obj != 0:
            self.objs = { Obj(0) for _ in range(self.in_cache_obj) }

    def __str__(self) -> str:
        lines = [
            f"KmemCache: {self.name}",
            f"  Addr       : 0x{self.addr:x}",
            f"  Object Size: {self.obj_size}",
            f"  Max Objects: {self.max_objs}",
            f"  Cache Slab:",
        ]
        if not self.objs:
            lines.append("    None")
        else:
            for obj in self.objs:
                lines.append(f"    {obj}")
        lines.append(f"  Full Slabs ({len(self.full)}):")
        for slab in self.full.values():
            lines.append(f"{slab}")
        lines.append(f"  Partial Slabs ({len(self.partial)}):")
        for slab in self.partial.values():
            lines.append(f"{slab}")
        lines.append(f"  Free Slabs ({len(self.free)}):")
        for slab in self.free.values():
            lines.append(f"{slab}")
        return "\n".join(lines)

    def count_allocated_objs(self):
        res = 0
        res += len(list(filter(lambda o: o.allocated, self.objs)))
        for slab in (*self.full.values(), *self.partial.values(), *self.free.values()):
            res += len(list(filter(lambda o: o.allocated, slab.objs.values())))
        return res