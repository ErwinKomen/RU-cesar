# Application specific
import util                 # This allows using ErrHandle
from models import *        # This imports HierObj

errHandle = util.ErrHandle()

def do_convert_from_htree(lst_source, dst_type, dst_ext):
    """Convert a HTREE json file to a destination format"""

    src_ext = ".json"
    lst_dst = []

    try:
        pass
    except:
        errHandle.DoError("do_convert_from_htree")
        return False

def do_convert_to_htree(lst_source, src_type, src_ext):
    """Convert from some kind of format to HTREE"""

    dst_ext = ".json"
    lst_dst = []

    try:
        pass
    except:
        errHandle.DoError("do_convert_to_htree")
        return False
