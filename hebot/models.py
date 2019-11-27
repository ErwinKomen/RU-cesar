"""
The classes in this models.py are used by the Python application hebot

"""

import os, sys
import copy
import json

cat_dict = {}
cat_dict['CP-Conj']='ConjP'

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
        txt.append("{}{} {} {} (id={})".format(spaces, self.pos, t, n, self.id))
        if self.child:
            for ch in self.child:
                txt.append(ch.get_simple(level+1))
        sBack = "\n".join(txt)
        return sBack

    def is_endnode(self):
        return self.type and self.n

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

    def add_child(self, node, after=None):
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
            else:
                newparent.child.append(node)
            node.parent = newparent
            return True
        except:
            msg = get_error_message()
            return False

    def add_ich(self, iIchCounter, dst_node):
        """Add an *ICH*-n node under [self] and adapt the POS of dst_node"""

        try:
            target = dst_node.sent_obj
            dst_ich_parent = HierObj(target, dst_node.pos, dst_node.txt, parent = self)
            dst_ich_node = HierObj(target, "*ICH*-{}".format(iIchCounter), "", parent=dst_ich_parent)
            dst_ich_node.type = "Star"
            dst_ich_parent.child.append(dst_ich_node)
            self.add_child(dst_ich_parent)
            # (3.2) THe category of the destination gets a "-n" attached
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
        
    def get_endnode(self, type, n = None):
        """Get the end-node according to type ('first', 'last')"""

        node = self
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
            elif type == "follows":
                node = None
                nsmall = 0
                for endnode in endnodes:
                    if endnode.n > n and endnode.status != "later":
                        node = endnode
                        break
        # Found anything?
        if node and node.is_endnode():
            return node
        else:
            return None

    def following(self):
        # Get all the nodes that *follow* after me

        try:
            nodelist = []
            parent = self.parent
            if not self.parent.is_top():
                # There *may* be nodes following me
                bFound = False
                for child in parent.child:
                    if child is self:
                        bFound = True
                    elif bFound:
                        nodelist.append(child)
            return nodelist
        except:
            msg = get_error_message()
            return []




class SentenceObj(object):
    """Sentence object"""

    label = ""  # Label
    sent = 1    # Sentence number
    pos = ""    # Grammatical category
    txt = ""    # The text associated with this instance
    type = None # The type, if it is an end-node (Punct, Vern, Star)
    id = -1     # Numerical identifier as used within the DB-system
    f = []      # List of features
    child = []  # List of child HierObj instances
    div = None          # Division number
    divpar = None       # Paragraph number within division
    parsnt = None       # Sentence number within paragraph    
    lst_hierobj = []    # Table of hierobj elements

    def __init__(self, label, sent, txt="", id=-1, div=None, divpar=None, parsnt=None, **kwargs):
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
        # Reset the table of hierobj elements
        self.lst_hierobj = []
        # Return the correct response
        return response

    def get_object(self):
        """Return an object representation of me"""

        js = dict(label=self.label, div=self.div, par=self.divpar, sent=self.sent, 
                  pos=self.pos, txt=self.txt, f=self.f, id=self.id)
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
                return None
            if nd_one is nd_two:
                # They are equal
                return nd_one
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

    def copy_surface(self):
        """Create a copy of me, putting discontinuous constituents in surface word order"""

        lst_source_endnodes = []
        iIchCounter = 0
        use_preceding_parent = False

        try:
            # (1) Create a copy with the basic information
            target = SentenceObj(label=self.label, sent=self.sent, txt=self.txt, id=self.id, div = self.div, divpar=self.divpar)
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
            if (self.div == 1 and self.divpar == 22 and self.sent == 2) or \
                (self.div == 1 and self.divpar == 1 and self.sent == 3):
                iStop = 1
            # ==============================================

            # (5) Walk left-to-right through the *SOURCE* words
            for dst_node in lst_target_endnodes:
                # Find the corresponding node in the *SRC*
                src_word = self.find_endnode(dst_node.n)

                # ============= Debugging ======================
                if src_word.n == 355811:
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
                                    if dst_prec_endnode and not dst_prec_endnode.is_top():
                                        break
                                if dst_prec_endnode == None:
                                    msg = "Warning: *no* preceding node found before n={}".format(intN)
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
                                        # A new ICH node needs to be created
                                        iIchCounter += 1
                                        # Depends on [dst_right]
                                        if dst_right and dst_right in dst_common.child:
                                            prev_parent = dst_right.parent
                                            dst_common.add_ich(iIchCounter, dst_right)
                                            # [dst_new_parent] becomes new parent, [dst_right] must move
                                            dst_new_parent.add_child(dst_right)
                                            dst_left = dst_right
                                        else:
                                            # (3.1) Create a new node under the dst_new_parent for an *ICH*-n
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
                            if dst_test == None or not dst_left:
                                dst_new_parent.add_child(dst_node)
                            else:
                                dst_new_parent.add_child(dst_node, after=dst_left)

                            # ========= DEBUGGING ========================
                            y = json.dumps( target.get_object(), indent=2)
                            x = target.get_simple()
                            # y = json.dumps(self.get_object(), indent=2)
                            # ============================================

            # Check if everything has been done in the source
            if not self.done():
                iStop = 1

            # Return the copy
            return target
        except:
            msg = get_error_message()
            return None

    def done(self):

        bFound = False
        for obj in self.lst_hierobj:
            if obj.status == "notdone" or obj.status == "later":
                bFound = True
                break
        return not bFound

    def loadsent(sent_obj):
        """Load a SentenceObj from the contents of a json object"""

        # Validate
        if sent_obj == None: return None
        # Create a copy with the basic information
        target = SentenceObj(label=sent_obj['label'], 
                             sent=sent_obj['sent'], 
                             txt=sent_obj['txt'], 
                             id=sent_obj['id'], 
                             div = sent_obj['div'], 
                             divpar=sent_obj['divpar'])
        # Walk all the objects hierarchically
        for child in sent_obj['child']:
            newnode = target.loadnode(child)
            target.child.append(newnode)

        # Return the copy
        return target

    def loadnode(self, node_obj):

        # Create a new node
        node = HierObj(self.lst_hierobj, pos=node_obj['pos'], txt=node_obj['txt'], id=node_obj['id'])
        # Add other stuff if available
        if 'n' in node_obj: node.n = node_obj['n']
        if 'type' in node_obj: node.type = node_obj['type']
        if 'f' in node_obj and len(node_obj['f']) > 0: node.f = copy.copy(node_obj['f'])
        # Add children if available
        if 'child' in node_obj and len(node_obj['child']) > 0:
            for child in node_obj['child']:
                grandchild = loadnode(child)
                node.child.append(grandchild)
                grandchild.parent = node
        # Ready
        return True
