"""
The classes in this models.py are used by the Python application hebot

"""

import os, sys
import copy
import json
import util

cat_dict = {}
cat_dict['CP-Conj']='ConjP'

errHandle = util.ErrHandle()

def get_error_message():
    arInfo = sys.exc_info()
    if len(arInfo) == 3:
        sMsg = str(arInfo[1])
        if arInfo[2] != None:
            sMsg += " at line " + str(arInfo[2].tb_lineno)
        return sMsg
    else:
        return ""


class HierObj(object):
    """Hierarchical object"""

    pos = ""        # Grammatical category
    txt = ""        # The text associated with this instance
    type = None     # The type, if it is an end-node (Punct, Vern, Star)
    n = None        # If present, this is a position within the surface text
    id = -1         # Numerical identifier as used within the DB-system
    f = []          # List of features
    child = []      # List of child HierObj instances
    parent = None   # Each object may be part of another
    status = ""     # Possible status (not used initially)
    # sent_obj = None # The sentence object to which I am related

    def __init__(self, sent_obj, pos, txt="", parent=None, id=-1, **kwargs):
        response = super(HierObj, self).__init__(**kwargs)
        self.pos = pos
        self.txt = txt
        self.f = []
        self.child = []
        self.type = None
        self.n = None
        self.parent = parent
        self.id = id
        # Make sure to add this object to the list
        self.sent_obj = sent_obj
        # self.sent_obj.lst_hierobj.append(self)
        sent_obj.lst_hierobj.append(self)
        # Return the correct response
        return response

    def get_object(self):
        """Return an object representation of me"""

        js = dict(pos=self.pos, txt=self.txt, f=self.f, id=self.id)
        if self.type: js['type'] = self.type
        if self.n: js['n'] = self.n
        if self.child:
            children =[]
            for ch in self.child:
                children.append(ch.get_object())
            js['child'] = children
        return js

    def get_simple(self, level):
        """Return a simple representation of me"""

        txt = []
        spaces = 2 * level * " "
        n = "" if not self.n else " n={}".format(self.n)
        t = ""
        if self.type:
            if self.type == "Vern":
                t = "[{}]".format(self.txt)
            elif self.type == "Star":
                t = "[{}]".format(self.txt)
        txt.append("{}{} {}\t{}\t(id={})".format(spaces, self.pos, t, n, self.id))
        if self.child:
            for ch in self.child:
                txt.append(ch.get_simple(level+1))
        sBack = "\n".join(txt)
        return sBack

    def is_endnode(self):
        return self.type and self.n

    def find_id(self, id):
        """Find node with [id] recursively"""

        if self.id == id:
            return self
        # Otherwise...
        for child in self.child:
            if child.find_id(id):
                return child
        # Didn't find it
        return None

    def simplify(self):
        """TRy to simplify myself in labels and hierarchically"""

        try:
            # Label simplification
            if self.pos in cat_dict:
                self.pos = cat_dict[self.pos]

            # Article: make text underscore
            if self.pos == "art" and self.txt == "":
                self.txt = "_"

            # Hierarchy check
            # (1) self should have only 1 child
            # (2) this child may not have a hyphen in the POS
            # (3) this child may not be an end node
            if self.child and len(self.child) == 1 and "-" not in self.child[0].pos and not self.child[0].type:
                # Action 1: keep child momentarily
                delchild = self.child[0]
                # Action 2: remove the child from my children
                self.child.remove(delchild)
                # Action 3: append all children of delchild to me
                for gch in delchild.child:
                    self.child.append(gch)
                    gch.parent = self
                # Action 4: Remove delchild from the lst_hierobj
                self.sent_obj.lst_hierobj.remove(delchild)
                # Action 5: Remove delchild completely
                del delchild
            # Walk all my children - if I have any
            if self.child:
                for ch in self.child:
                    ch.simplify()
            return True
        except:
            msg = get_error_message()
            return False

    def get_copy(self, target, parent=None):
        """Create a copy of myself 
        If parent is set, that becomes my parent, otherwise [target] is my parent
        """

        # Create initial node
        node = HierObj(target, pos=self.pos, txt=self.txt, id=self.id)
        # Add optional attributes
        if self.n: node.n = self.n
        if self.type: node.type = self.type
        node.f = copy.copy(self.f)
        # Set my correct parent
        node.parent = target if parent == None else parent
        # Make sure my parent receives me as a child
        node.parent.child.append(node)
        # Return the new node
        return node

    def is_top(self):
        return False

    def insert_above(self, node):
        """Insert [node] above me (self)"""

        try:
            # (1) I should be deleted as child from my former parent
            if self in self.parent.child:
                self.parent.child.remove(self)
            # (2) the parent of [node] becomes what was my parent
            node.parent = self.parent
            # (3) my parent becomes [node]
            self.parent = node
            # (4) I should be added as child of [node]
            node.child.append(self)
            return True
        except:
            msg = get_error_message()
            return False

    def add_child(self, node, after=None, start=False):
        """Add [node] as child under [self], optionally after [after]"""

        try:
            # Remove it from its previous parent
            prevparent = node.parent
            if prevparent.child and node in prevparent.child:
                prevparent.child.remove(node)
            # Add it as child to new parent
            newparent = self
            if after:
                idx = -1
                for i, item in enumerate(newparent.child):
                    if item is after:
                        idx = i
                        break
                if idx < 0 or i >= len(newparent.child):
                    newparent.child.append(node)
                else:
                    newparent.child.insert(idx+1, node)
            elif start:
                newparent.child.insert(0, node)
            else:
                newparent.child.append(node)
            node.parent = newparent
            return True
        except:
            msg = get_error_message()
            return False

    def add_ich(self, iIchCounter, dst_node, after=None):
        """Add an *ICH*-n node under [self] and adapt the POS of dst_node"""

        try:
            target = dst_node.sent_obj
            dst_ich_parent = HierObj(target, dst_node.pos, dst_node.txt, parent = self)
            dst_ich_node = HierObj(target, "*ICH*-{}".format(iIchCounter), "", parent=dst_ich_parent)
            dst_ich_node.type = "Star"
            dst_ich_parent.child.append(dst_ich_node)
            self.add_child(dst_ich_parent, after=after)
            # (3.2) THe category of the destination gets a "-n" attached
            dst_node.pos = "{}-{}".format(dst_node.pos, iIchCounter)
            return True
        except:
            msg = get_error_message()
            return False

    def preceding_sibling(self):
        """Get my immediately preceding sibling"""

        try:
            # Validate
            if self == None: return None
            if self.parent == None: return None
            parent = self.parent
            prev = None
            for ch in self.parent.child:
                if ch is self:
                    return prev
                prev = ch
            return prev
        except:
            msg = get_error_message()
            return None
        
    def copy_ich(self, iIchCounter, dst_node, after=None, start=False):
        """THe new location of dst_node is under [self], after [after]. Replace original with*ICH*-n node"""

        try:
            # Need to have the sentence object
            target = dst_node.sent_obj

            # Get my preceding sibling and my parent
            prev = dst_node.preceding_sibling()
            parent = dst_node.parent

            # Add the [dst_node] to the correct new location
            if after:
                self.add_child(dst_node, after=after)
            elif start:
                self.add_child(dst_node, start=True)
            else:
                self.add_child(dst_node)

            # Create an ICH node
            dst_ich_parent = HierObj(target, dst_node.pos, "", parent = self)
            dst_ich_node = HierObj(target, "*ICH*-{}".format(iIchCounter), "", parent=dst_ich_parent)
            dst_ich_node.type = "Star"
            dst_ich_parent.add_child(dst_ich_node)

            # Make sure it ends up where the previous [dst_node] was
            if prev:
                parent.add_child(dst_ich_parent, after=prev)
            else:
                parent.add_child(dst_ich_parent, start=True)

            # Adapt the POS of the moved dst_node
            dst_node.pos = "{}-{}".format(dst_node.pos, iIchCounter)

            return True
        except:
            msg = get_error_message()
            return False

    def get_endnodes(self, endnodes):
        """Return a list of endnodes under me"""

        if self != None:
            if self.is_endnode():
                endnodes.append(self)
            elif self.child:
                for ch in self.child:
                    endnodes = ch.get_endnodes(endnodes)
        # Return what we have
        return endnodes
        
    def get_endnode(self, type, n = None, sametop = False, sentence = False, until = False):
        """Get the end-node according to type ('first', 'last')
        
        until - True if 'precedes' should only be done until the node with [n]
        """

        node = self
        try:
            if sentence:
                # Get end-nodes from the sentence level
                endnodes = []
                for ch in self.sent_obj.child:
                    endnodes = ch.get_endnodes(endnodes)
            elif sametop:
                # Find the top from here
                top = self
                while top.parent and not top.parent.is_top():
                    top = top.parent
                if top != None and top.parent and top.parent.is_top():
                    endnodes = top.get_endnodes([])
            else:
                endnodes = self.get_endnodes([])
            if endnodes and len(endnodes) > 0:
                if type == "first":
                    node = endnodes[0]
                elif type == "last":
                    node = endnodes[-1]
                elif type == "precedes":
                    node = None
                    nsmall = 0
                    for endnode in endnodes:
                        if endnode.n > nsmall and endnode.n < n and endnode.status != "later":
                            node = endnode
                            nsmall = node.n
                        if until and endnode.n == n:
                            break
                elif type == "follows":
                    node = None
                    nsmall = 0
                    for endnode in endnodes:
                        if endnode.n > n and endnode.status != "later":
                            node = endnode
                            break
                elif type == "first-preceding":
                    node = None
                    prev = None
                    for endnode in endnodes:
                        if endnode.n and endnode.n == n:
                            node = prev
                            break
                        prev = endnode
                    # ======= DEBUG =========
                    if node == None:
                        iStop = 1
                elif type == "first-following":
                    node = None
                    for idx, endnode in enumerate(endnodes):
                        if endnode.n and endnode.n == n:
                            if idx + 1 < len(endnodes):
                                node = endnodes[idx+1]
                            break
                    # ======= DEBUG =========
                    if node == None:
                        iStop = 1
            # Found anything?
            if node and node.is_endnode():
                return node
            else:
                return None
        except:
            msg = errHandle.get_error_message()
            errHandle.Status(msg)
            return None

    def following(self, bNoStar = True):
        # Get all the nodes that *follow* after me

        try:
            nodelist = []
            # Get to my highest ancestor
            previous = self 
            node = self
            while not node.parent.is_top():
                node = node.parent
                # Look for nodes following 'me' (='previous')
                bFound = False
                for child in node.child:
                    if child is previous:
                        bFound = True
                    elif bFound:
                        # Note: a 'star' constituent has id=-1
                        if not bNoStar or child.id >=0:
                            nodelist.append(child)
                previous = node
            return nodelist
        except:
            msg = get_error_message()
            return []


class SentenceObj(object):
    """Sentence object"""

    textid = "" # Name of the text
    label = ""  # Label
    sent = 1    # Sentence number
    pos = ""    # Grammatical category
    txt = ""    # The text associated with this instance
    type = None # The type, if it is an end-node (Punct, Vern, Star)
    id = -1     # Numerical identifier as used within the DB-system
    ich_count = 0       # ICH counter
    f = []              # List of features
    child = []          # List of child HierObj instances
    div = None          # Division number
    divpar = None       # Paragraph number within division
    parsnt = None       # Sentence number within paragraph    
    lst_hierobj = []    # Table of hierobj elements

    def __init__(self, label, sent, textid="", txt="", id=-1, div=None, divpar=None, parsnt=None, **kwargs):
        response = super(SentenceObj, self).__init__(**kwargs)
        self.label = label
        self.div = div
        self.divpar = divpar
        self.sent = sent
        self.txt = txt
        self.id = id
        self.f = []
        self.child = []
        self.type = None
        self.textid = textid
        # Reset the table of hierobj elements
        self.lst_hierobj = []
        # Return the correct response
        return response

    def get_object(self):
        """Return an object representation of me"""

        js = dict(label=self.label, div=self.div, par=self.divpar, sent=self.sent, 
                  pos=self.pos, txt=self.txt, f=self.f, id=self.id, textid=self.textid)
        if self.type: js['type'] = self.type
        if self.child:
            children =[]
            for ch in self.child:
                children.append(ch.get_object())
            js['child'] = children
        return js

    def get_simple(self):
        """Return a simple representation of me"""

        txt = []
        txt.append("Tree of: d.{}.p.{}.s.{} {} (id={})".format(self.div, self.divpar, self.sent, self.label, self.id))
        level = 0
        #js = dict(label=self.label, div=self.div, par=self.divpar, sent=self.sent, 
        #          pos=self.pos, txt=self.txt, f=self.f, id=self.id)
        #if self.type: js['type'] = self.type
        if self.child:
            level += 1
            for ch in self.child:
                txt.append(ch.get_simple(level))
        sBack = "\n".join(txt)
        return sBack

    def simplify(self):
        """TRy to simplify myself in labels and hierarchically"""

        if self.child:
            for ch in self.child:
                ch.simplify()
        return True
    
    def find(self, id):
        """Look in the lst_hierobj and find the one with this id"""

        for obj in self.lst_hierobj:
            if obj.id == id:
                return obj
        return None

    def find_node(self, func):
        """Look in the lst_hierobj and find the one with this id"""

        for obj in self.lst_hierobj:
            if func(obj):
                return obj
        return None

    def find_endnode(self, n):
        """Look in the lst_hierobj and find the one with this @n"""

        for obj in self.lst_hierobj:
            if obj.n and obj.n == n:
                return obj
        return None

    def is_top(self):
        return True

    def add_child(self, node):
        """Add 'node' as child under me"""

        if node:
            self.child.append(node)
            node.parent = self
        return True

    def get_common_ancestor(self, nd_one, nd_two):
        """Get the common ancestor between [nd_one] and [nd_two]"""

        try:
            # Validate
            if nd_one == None or nd_two == None:
                # There is no common ancestor
                return None, None, None
            if nd_one is nd_two:
                # They are equal
                return nd_one, None, None
            # Initialize
            ndLeft = nd_one
            ndRight = nd_two
            nd_mybef = nd_one
            # Outer loop
            while nd_mybef != None and not nd_mybef.is_top():
                # See if there is an ancestor of nd_two equal to nd_mybef
                nd_work = nd_two
                while nd_work != None and not nd_work.is_top():
                    # Test
                    if nd_work is nd_mybef:
                        # Found it
                        return nd_mybef, ndLeft, ndRight
                    # Adjust
                    ndRight = nd_work
                    # Go higher
                    nd_work = nd_work.parent
                # Adjust left
                ndLeft = nd_mybef
                # Try parent
                nd_mybef = nd_mybef.parent

            # COming here means: we did not find it
            return None, ndLeft, ndRight
        except:
            msg = get_error_message()
            return None, None, None

    def insert_sentence(self, additional):
        """Combine the [additional] SentenceObj into [self]"""

        try:
            # (PRE.1) If we have an additional, then combine it onto the main one
            if additional == None:
                return "insert_sentence: empty"
            else:
                # Copy the additional's lst_hierobj
                for obj in additional.lst_hierobj:
                    self.lst_hierobj.append(obj)
                # Add the child(ren) of additional to self
                # (a) Get all the end-nodes in additional
                add_endnodes = additional.child[0].get_endnodes([])
                add_first = add_endnodes[0]
                # (b) Get all the end-nodes in [self]
                self_endnodes = self.child[0].get_endnodes([])
                # (c) walk the ones in self
                idx = 0
                size = len(list(self_endnodes))
                while idx < size and self_endnodes[idx].n < add_first.n :
                    idx += 1
                if idx < size:
                    nd_bef = self_endnodes[idx-1]
                    nd_aft = self_endnodes[idx]
                    # (d) get common ancestor
                    add_common, self_left, self_right = self.get_common_ancestor(nd_bef, nd_aft)
                    # (e) Place additional as child under add_common
                    add_common.add_child(additional.child[0], after = self_left)

                # x = self.get_simple()
        except:
            msg = errHandle.get_error_message()
            return msg

    def get_location(self):
        sLoc = "d{}.p{}.s{}".format(self.div, self.divpar, self.sent)
        return sLoc

    def copy_surface(self, debug = None):
        """Create a copy of me, putting discontinuous constituents in surface word order"""

        lst_source_endnodes = []        # List of endnodes in the source (will be sorted)
        top_later = []                  # List of top-nodes that may need to be inserted somewhere later
        iIchCounter = 0                 # Local counter for all *ICH*-n nodes in this sentence
        use_preceding_parent = False    # Programming option. Use 'False' for the moment

        try:

            # (1) Create a copy with the basic information
            target = SentenceObj(textid=self.textid, label=self.label, sent=self.sent, txt=self.txt, id=self.id, div = self.div, divpar=self.divpar)
            # (2) Collect a list of copies of all 'end' nodes
            for obj in self.lst_hierobj:
                # Check if this is an end-node
                if not obj.is_endnode():
                    # (3) Mark non-endnodes as "notdone" in the *SOURCE*
                    obj.status = "notdone"

            # (4) Order the items in the lst_hierobj of *TARGET* on @n
            lst_source_endnodes = [x for x in self.lst_hierobj if x.is_endnode()]
            lst_source_endnodes.sort(key=lambda x: x.n)
            for obj in lst_source_endnodes:
                # Create a copy of the relevant parts, adding them under [target]
                endnode = obj.get_copy(target)

            # (5) Get a list of endnodes from the sorted target
            lst_target_endnodes = [x for x in target.lst_hierobj if x.is_endnode()]

            # ============= Debugging ======================
            if (self.div == 1 and self.divpar == 22 and self.sent == 1) :
                iStop = 1
                x = target.get_simple()
            #if additional != None:
            #    iStop = 1
            # ==============================================
            if debug and debug > 2: errHandle.Status(target.get_simple())

            # (6) Make sure to note whether the 'top' has already been reached
            bDstTopReached =False

            # (7) Walk left-to-right through the *SOURCE* words
            dst_previous_node = None
            for dst_node in lst_target_endnodes:
                # Find the corresponding node in the *SRC*
                src_word = self.find_endnode(dst_node.n)

                # ============= Debugging ======================
                if src_word.n == 35367:
                    iStop = 1
                # ==============================================
                
                src_node = src_word

                # Travel upwards looking for parents in the *SOURCE* nodes
                if src_node.parent:
                    # Get the parent of the source node
                    src_parent = src_node.parent
                    # If a source word is at the 'top', it gets a special treatment
                    if src_parent.is_top():
                        # Save words attached to the 'top'
                        src_word.status = "later"
                    else:
                        # DOUBLE check if this works
                        n_prec = src_node.n
                        # PHASE 1
                        while src_node and src_parent and not src_parent.is_top() and src_parent.status == "notdone":
                            # This node has not yet been processed...
                            # (a) Create a copy of the consitutent (Note: 'target' becomes initial parent)
                            dst_parent = src_parent.get_copy(target)
                            # (b) now [src_parent] has been 'done'
                            src_parent.status = "done"

                            # (c) Insert this constituent above the 'current' dst node
                            dst_node.insert_above(dst_parent)

                            # Next step up: 
                            # (d) go to the destination parent
                            dst_node = dst_parent
                            # (e) Get the new source and its parent
                            src_node = src_parent
                            src_parent = src_node.parent

                        # Check for special situation: target already has a sentence-child, and this would be the second
                        if src_parent.is_top():
                           if bDstTopReached:
                               # Store the dst_parent to be treated later on
                               top_later.append(dict(node=dst_node, prev_word=dst_previous_node))
                           else:
                               bDstTopReached = True

                        # PHASE 2
                        # Check the end situation: is the current source parent 'done'?
                        if src_node and src_parent and not src_parent.is_top() and src_parent.status == "done":
                            # The new destination [dst_node] must be added as child 
                            #   under the correct destination copy of the source node

                            # (2.1) Find the copy of the source parent in the destination area
                            dst_new_parent = target.find(src_parent.id)

                            # (2.2) Double check the outcome
                            if dst_new_parent == None:
                                # There is an error and we cannot proceed
                                msg = "Warning: cannot find DST equivalent of SRC node"
                                return None, msg

                            # (2.2) Check for well-formedness:
                            #       - linear precedence: the last endnode under my destination parent
                            #                            must immediately precede 'me'
                            #       - the word preceding me may not come after my destination parent-to-be
                            # [a] Find the @n value of the first word in the destination node being processed
                            dst_first_endnode = dst_node.get_endnode("first")
                            if n_prec != dst_first_endnode.n:
                                n_prec = dst_first_endnode.n
                            # [b] Is there a word in destination: (i) it follows after dst_new_parent, (ii) @n < n_prec, and (iii) @status != 'later'
                            following = dst_new_parent.following()
                            first_following = None if len(following) == 0 else following[0]
                            dst_test = None
                            dst_left = None
                            dst_test = None
                            if first_following:
                                dst_test = first_following.get_endnode("precedes", n_prec)
                                method = "common_ancestor"
                            if use_preceding_parent and not dst_test:
                                # [c] Is there a word in destination: (i) it is under dst_new_parent, (ii) @n > n_prec and (iii) @status != 'later'
                                dst_test = dst_new_parent.get_endnode("follows", n_prec)
                                method = "preceding_parent"
                            if dst_test != None:
                                # (3) We have a disruption in the word order

                                # (3.1) Get the first @n number under the destination node
                                intN = n_prec
                                # (3.2) Get the lowest common ancestor under the following nodes in the destination:
                                #       1 - dst_new_parent
                                #       2 - the endnode that precedes dst_node
                                iSubtract = 0
                                while True:
                                    iSubtract -= 1
                                    dst_prec_endnode = next(iter([x for x in target.lst_hierobj if x.n and x.n == intN+iSubtract]), None)
                                    if dst_prec_endnode == None:
                                        msg = "Warning: could not find endnode with @n={}".format(intN+iSubtract)
                                        # Provide a message to the user
                                        errHandle.Status(msg)
                                    if dst_prec_endnode and not dst_prec_endnode.is_top():
                                        break
                                if dst_prec_endnode == None:
                                    msg = "Warning: *no* preceding node found before n={}".format(intN)
                                    # Provide a message to the user
                                    errHandle.Status(msg)
                                else:
                                    # We found the right preceding node
                                    # (3.5) do we have a lowest common ancestor?
                                    if method == "preceding_parent":
                                        dst_common, dst_left, dst_right = target.get_common_ancestor(dst_prec_endnode, dst_test)
                                        if not dst_common is dst_new_parent:
                                            # (3.1) Create a new node under the dst_new_parent for an *ICH*-n
                                            iIchCounter += 1
                                            dst_new_parent.add_ich(iIchCounter, dst_node)
                                    elif method == "common_ancestor":
                                        dst_common, dst_left, dst_right = target.get_common_ancestor(dst_new_parent, dst_prec_endnode)
                                        
                                        method = "Normal"
                                        method = "Dec12"

                                        # Depends on [dst_right]
                                        if method == "Normal" and dst_right and dst_right in dst_common.child:

                                            if dst_right in following:
                                                # Process all the following elements in the same way
                                                for follows in following:
                                                    prev_parent = follows.parent
                                                    # A new ICH node needs to be created
                                                    iIchCounter += 1
                                                    dst_common.add_ich(iIchCounter, follows)
                                                    dst_new_parent.add_child(follows)
                                                dst_left = follows
                                            else:
                                                prev_parent = dst_right.parent
                                                # A new ICH node needs to be created
                                                iIchCounter += 1
                                                dst_common.add_ich(iIchCounter, dst_right)
                                                # [dst_new_parent] becomes new parent, [dst_right] must move
                                                dst_new_parent.add_child(dst_right)
                                                dst_left = dst_right
                                        else:
                                            # (3.1) Create a new node under the dst_new_parent for an *ICH*-n
                                            iIchCounter += 1
                                            dst_new_parent.add_ich(iIchCounter, dst_node)
                                            # This is the new parent
                                            dst_new_parent = dst_common

                                    if dst_common == None:
                                        # There is no common ancestor
                                        msg = "Warning: no common ancestor for node with @n={}".format(intN+iSubtract)
                                    #else:
                                    #    # This is the new parent
                                    #    dst_new_parent = dst_common
                                iStop = 1

                            # Add the dst_node we have as child to [dst_new_parent] after [dst_left]
                            use_old_system = False
                            if use_old_system:
                                if dst_test == None or not dst_left:
                                    dst_new_parent.add_child(dst_node)
                                else:
                                    dst_new_parent.add_child(dst_node, after=dst_left)
                            dst_new_parent.add_child(dst_node)

                            # ========= DEBUGGING ========================
                            if debug and debug > 11:
                                y = json.dumps( target.get_object(), indent=2)
                                x = target.get_simple()
                            # y = json.dumps(self.get_object(), indent=2)
                            # ============================================
                            if debug and debug > 2: 
                                errHandle.Status(target.get_simple())

                # Keep the destination node for later
                dst_previous_node = target.find_endnode(src_word.n)

            # Check if everything has been done in the source
            if not self.done():
                iStop = 1

            if len(top_later) > 0:
                # Check if the target is in the right order
                if not target.is_complete(sorted=False):
                    # We still have elements in the 'top_later': use these
                    for item in top_later:
                        nd_bef = item['prev_word']
                        node = item['node']
                        # FInd the *next* node following after [nd_bef]
                        if nd_bef.n == 36194:
                            iStop = 1
                        nd_aft = nd_bef.get_endnode("follows", nd_bef.n, sentence = True )  # , sametop = True
                        if nd_aft == None:
                            # Cannot find the *next* node after [nd_bef] - now do what?
                            msg = "Could not find a node following after {}".format(nd_bef.n)
                            errHandle.Status(msg)
                        else:
                            # Find common ancestor
                            nd_common, nd_left, nd_right = target.get_common_ancestor(nd_bef, nd_aft)
                            # Make sure we have a common ancestor
                            if nd_common:
                                # Add [node] at the right place
                                nd_common.add_child(node, after=nd_left)
                            elif nd_left and nd_right:
                                # Place right under left
                                nd_left.add_child(nd_right)
                                # pass
                            else:
                                # There is no common ancestor - now what do we do??
                                msg = "Could not find a common ancestor"
                                errHandle.Status(msg)
                        # Debugging
                        if debug and debug > 3: x = target.get_simple()

            # Perform an evaluation of the result
            msg = SentenceObj.evaluate(target)
            if msg != None and msg != "":
                # Provide a message to the user
                errHandle.Status(msg)                
                x = self.get_simple()
            # Return the copy
            return target, ""
        except:
            msg = get_error_message()
            return None, msg

    def do_correct(self, node):
        """Make sure that [node] ends up between n-1 and n+1"""

        try:
            # Figure out what my number is
            n = node.n
            
            # Get my immediately preceding and following end nodes
            prev = node.get_endnode('precedes', n, sametop=True, until=True)
            next = node.get_endnode('follows', n, sametop=True)
            # prev = node.get_endnode('first-preceding', n, sametop=True)
            # next = node.get_endnode('first-following', n, sametop=True)

            bForceStart = False
            if prev == None:
                prev = next.parent
                bForceStart = True

            if prev and next:
                # Get the nearest common ancestor between prev and next
                com, left, right = self.get_common_ancestor(prev, next)

                if com:
                    # Add a copy of [node] under [com] with endnode *ICH*-n
                    #   and also emend the POS tag of [node]
                    self.ich_count += 1
                    if bForceStart or left == None:
                        # It must come right at the beginning
                        com.copy_ich(self.ich_count, node, start=True)
                    else:
                        com.copy_ich(self.ich_count, node, after=left)
                else:
                    errHandle.DoError("do_correct: com is empty")
            else:
                errHandle.DoError("do_correct: prev or next is empty")
            return True, ""
        except:
            msg = get_error_message()
            return False, msg

    def copy_surface_new(self, debug=None):
        """Copy myself, perform surfacing on that copy"""

        try:
            sent_loc = self.get_location()
            if debug and debug >= 1:
                errHandle.Status("Working on: {}".format(sent_loc))
            # ============= Debugging ========================
            if sent_loc == "d3.p23.s1":
                iStop = 1
            # ================================================

            # Make a deep copy of myself
            # target = copy.deepcopy(self)
            target = self

            # Walk all 'sentences' within me
            for hobj in target.child:
                # Reset the ich counter
                target.ich_count = 0

                # Get all the end nodes
                endnodes = []
                endnodes = hobj.get_endnodes(endnodes)
                prev = None
                bPrevReset = False

                # Walk all the endnodes in the order we received them
                for idx, endnode in enumerate(endnodes):
                    # ========== DEBUG =============================
                    if sent_loc == "d5.p19.s1":
                        iStop = 1

                    # Make sure that we initially do not have a reset of [prev]
                    bPrevReset = False

                    # Check if this should be treated
                    if prev != None and endnode.is_endnode() and prev.n > endnode.n:

                        # Get the picture before
                        if debug and debug > 2: 
                            before = target.get_simple()

                        if debug and debug >= 1:
                            # Show what we are correcting
                            errHandle.Status("{} correcting n={}".format(sent_loc, endnode.n))

                        # Perform the correction
                        if endnode.n == 1:
                            # If we are getting an order 2-1, then it's easier to correct n=2, which should come between [1...3]
                            # But: if we have the order [2, 3, 1], then [1] should be corrected, not [3]
                            # OLD result, msg = target.do_correct(prev)
                            result, msg = target.do_correct(endnode)
                            # break
                        else:
                            # Otherwise try to place the [endnode] in the correct window
                            result, msg = target.do_correct(endnode)
                            # break

                        # Adapt the 'prev'
                        bPrevReset = True

                        # Get the result how it looks like
                        if debug and debug > 2: 
                            after = target.get_simple()

                    # Keep track of the previous endnode
                    if not bPrevReset: 
                        prev = endnode

                if debug and debug > 1:
                    # Perform an evaluation of the result
                    msg = SentenceObj.evaluate(target)
                    if msg != None and msg != "":
                        # look at [after]
                        x = target.get_simple()
                        y = self.get_simple()
                        iStop = 1


            # Perform an evaluation of the result
            msg = SentenceObj.evaluate(target)
            if msg != None and msg != "":
                # Provide a message to the user
                errHandle.Status(msg)                
                x = target.get_simple()
            # Return the copy
            return target, ""
        except:
            msg = get_error_message()
            errHandle.DoError("copy_surface_new")
            return None, msg

    def is_complete(self, sorted=True):
        """Check if the sentence is COMPLETE"""

        try:
            endnodes = []
            for ch in self.child:
                endnodes = ch.get_endnodes(endnodes)
            if sorted:
                # Sort the end nodes
                endnodes.sort(key=lambda x: x.n)
            # Walk them and see if there are no gaps
            last_n = 0
            for node in endnodes:
                if last_n == 0:
                    last_n = node.n
                else:
                    if node.n - last_n != 1:
                        return False
                    last_n = node.n

            # Return positively
            return True
        except:
            msg = errHandle.get_error_message()
            errHandle.Status(msg)
            return False
        
    def evaluate(target):
        """Check if the sentence in target is ok. If not: provide a report"""

        try:
            lBack = []
            # Walk all my children
            for ch in target.child:
                # Get the end nodes
                endnodes = ch.get_endnodes([])
                # Check the end nodes
                bOrder = True
                bNumber = True
                last_n = 0
                for node in endnodes:
                    if last_n == 0:
                        last_n = node.n
                    else:
                        if node.n - last_n > 1:
                            bNumber = False
                            lBack.append("{} d.{}.p.{}.s.{} Number problem: {}...{}".format(
                                target.textid, target.div, target.divpar, target.sent,  last_n, node.n)) 
                        if node.n < last_n:
                            bOrder = False
                            lBack.append("{} d.{}.p.{}.s.{} Order problem: {}...{}".format(
                                target.textid, target.div, target.divpar, target.sent,last_n, node.n))
                        last_n = node.n
            if len(lBack) > 0:
                msg = "\n".join(lBack)
                return msg

            # Return positively
            return None
        except:
            msg = errHandle.get_error_message()
            return msg
        
    def done(self):

        bFound = False
        for obj in self.lst_hierobj:
            if obj.status == "notdone" or obj.status == "later":
                bFound = True
                break
        return not bFound

    def loadsent(sent_obj, textid=None):
        """Load a SentenceObj from the contents of a json object"""

        # Validate
        if sent_obj == None: return None

        try:
            textid = textid if textid != None else sent_obj['textid']
            if 'par' in sent_obj:
                divpar = sent_obj['par']
            else:
                divpar = sent_obj['divpar']
            # Create a copy with the basic information
            target = SentenceObj(textid=textid,
                                 label=sent_obj['label'], 
                                 sent=sent_obj['sent'], 
                                 txt=sent_obj['txt'], 
                                 id=sent_obj['id'], 
                                 div = sent_obj['div'], 
                                 divpar=divpar)
            if 'child' not in sent_obj:
                return None
            # Walk all the objects hierarchically
            for child in sent_obj['child']:
                newnode = target.loadnode(child)
                newnode.parent = target
                target.child.append(newnode)

            # Return the copy
            return target
        except:
            errHandle.DoError("loadsent")
            return None

    def loadnode(self, node_obj):

        try:
            # Create a new node
            node = HierObj(self, pos=node_obj['pos'], txt=node_obj['txt'], id=node_obj['id'])
            # Add other stuff if available
            if 'n' in node_obj: node.n = node_obj['n']
            if 'type' in node_obj: node.type = node_obj['type']
            if 'f' in node_obj and len(node_obj['f']) > 0: node.f = copy.copy(node_obj['f'])
            # Add children if available
            if 'child' in node_obj and len(node_obj['child']) > 0:
                for child in node_obj['child']:
                    if self.is_top():
                        grandchild = self.loadnode(child)
                    else:
                        grandchild = self.sent_obj.loadnode(child)
                    node.child.append(grandchild)
                    grandchild.parent = node
            # Ready
            return node
        except:
            errHandle.DoError("loadnode")
            return None
