import abc
from enum import Enum
from typing import Union

from fslab_models import (
    SlabCreateData, SlabAllocRequestData, SlabAllocObjData,
    SlabFreeObjData, SlabFreeSlabData
)
from fslab_utils import is_in_same_page

# Command base class
class MyMsg(abc.ABC):
    def __init__(self, *msg_data):
        self.msg_data = msg_data
        self.check()

    @abc.abstractmethod
    def check(self):
        """Validate the debug message data."""

    def bad_msg(self, msg: str):
        raise AssertionError(f"Invalid {self.__class__.__name__}: {msg}\nData: {self.msg_data}")

    def __repr__(self):
        return f"{self.__class__.__name__} {self.msg_data}"

# Concrete debug message classes
class SlabCreateMsg(MyMsg):
    def check(self, valid_object_size: int = 504):
        if len(self.msg_data) != 1 or not isinstance(self.msg_data[0], SlabCreateData):
            self.bad_msg("Expected single SlabCreateData")
        data = self.msg_data[0]
        if not data.name:
            self.bad_msg("Name cannot be empty")
        if data.object_size != valid_object_size:
            self.bad_msg(f"Invalid object_size {data.object_size}")
        self.name = data.name
        self.object_size = data.object_size
        self.addr = data.addr
        self.max_objs = data.max_objs
        self.in_cache_obj = data.in_cache_obj

class SlabAllocMsg(MyMsg):
    def check(self):
        if not (2 <= len(self.msg_data) <= 3):
            self.bad_msg("Expected 2-3 data items")
        if not isinstance(self.msg_data[0], SlabAllocRequestData) or \
           not isinstance(self.msg_data[-1], SlabAllocObjData):
            self.bad_msg("Invalid data types")
        
        req, obj = self.msg_data[0], self.msg_data[-1]
        slab = self.msg_data[1] if len(self.msg_data) == 3 else None
        
        # Name consistency check
        if not req.name or (slab and req.name != slab.name) or req.name != obj.name:
            self.bad_msg(f"Name mismatch: request={req.name}, slab={slab.name if slab else ''}, obj={obj.name}")
        # Address validation
        if slab and (slab.addr == 0 or slab.addr != obj.slab_addr):
            self.bad_msg(f"Slab address mismatch: 0x{slab.addr:x} vs 0x{obj.slab_addr:x}")
        if obj.addr == 0 or not is_in_same_page(obj.addr, obj.slab_addr):
            self.bad_msg(f"Invalid object address 0x{obj.addr:x} for slab 0x{obj.slab_addr:x}")

        self.name = obj.name
        self.obj_addr = obj.addr
        self.slab_addr = obj.slab_addr
        self.allocate_new = len(self.msg_data) == 3

class SlabFreeMsg(MyMsg):
    def check(self):
        if not (1 <= len(self.msg_data) <= 2) or not isinstance(self.msg_data[0], SlabFreeObjData):
            self.bad_msg("Expected 1-2 lines: free obj, optionally free slab")
        
        obj = self.msg_data[0]
        slab = self.msg_data[1] if len(self.msg_data) == 2 else None
        
        if not obj.name or (slab and obj.name != slab.name):
            self.bad_msg(f"Name mismatch: {obj.name} {slab.name if slab else ''}")
        if slab and slab.addr == 0:
            self.bad_msg(f"Invalid slab to free")
        if obj.addr == 0 or not is_in_same_page(obj.addr, obj.slab_addr):
            self.bad_msg(f"Invalid obj_addr 0x{obj.addr:x} for slab 0x{obj.slab_addr:x}")

        self.name = obj.name
        self.obj_addr = obj.addr
        self.slab_addr = obj.slab_addr
        self.free_slab: int = slab.addr if len(self.msg_data) == 2 else 0

class SlabPrintMsg(MyMsg):
    def check(self):
        pass
    def __repr__(self):
        res = [f"{self.__class__.__name__}", *[str(data) for data in self.msg_data]]
        return "\n\t".join(res)

class ListCheckMsg(MyMsg):
    def check(self):
        return super().check()

# --- Other Message Types ---

SlabMsg = Union[SlabCreateMsg,
                SlabAllocMsg,
                SlabFreeMsg,
                SlabPrintMsg]

class FileMsg(Enum):
    Init = "fileinit"
    Alloc = "filealloc"
    Close = "fileclose"