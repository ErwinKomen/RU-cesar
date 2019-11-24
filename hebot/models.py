"""
The classes in this models.py are used by the Python application hebot

"""

import os
import copy
import json

cat_dict = {}
cat_dict['CP-Conj']='ConjP'

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

    def is_endnode(self):
        return self.type and self.n

    def simplify(self):
        """TRy to simplify myself in labels and hierarchically"""

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
            # Action 4: Remove delchild from the lst_hierobj
            self.sent_obj.lst_hierobj.remove(delchild)
            # Action 5: Remove delchild completely
            del delchild
        # Walk all my children - if I have any
        if self.child:
            for ch in self.child:
                ch.simplify()

    def get_copy(self, target):
        """Create a copy of myself """

        node = HierObj(target, pos=self.pos, txt=self.txt, id=self.id)
        if self.n: node.n = self.n
        if self.type: node.type = self.type
        node.f = copy.copy(self.f)
        return node

    def is_top(self):
        return False


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

    def is_top(self):
        return True

    def copy_surface(self):
        """Create a copy of me, putting discontinuous constituents in surface word order"""

        lst_source_endnodes = []

        # (1) Create a copy with the basic information
        target = SentenceObj(label=self.label, sent=self.sent, txt=self.txt, id=self.id, div = self.div, divpar=self.divpar)
        # (2) Collect a list of copies of all 'end' nodes
        for obj in self.lst_hierobj:
            # Check if this is an end-node
            if obj.is_endnode():
                # Create a copy of the relevant parts
                endnode = obj.get_copy(target)
                # Add source word to *SOURCE* endnodes list
                lst_source_endnodes.append(obj)
            else:
                # (3) Mark non-endnodes as "notdone" in the *SOURCE*
                obj.status = "notdone"

        # (4) Order the items in the lst_hierobj of *TARGET* on @n
        target.lst_hierobj.sort(key=lambda x: x.n)

        # (5) Walk left-to-right through the *SOURCE* words
        for src_word in lst_source_endnodes:
            # Find the equivalent *DST* node
            dst_word = target.find(src_word.id)

            # Travel upwards looking for parents in the *SOURCE* nodes
            src_node = src_word
            src_parent = src_node.parent
            while src_node and src_parent and not src_parent.is_top():
                # Check: has the constituent been done yet?
                if src_parent.status == "notdone":
                    # Create a copy of the consitutent
                    dst_parent = src_parent.get_copy(target)
                    # Insert this constituent above the 'current' dst node

                # Get the new source
                src_node = src_parent
                src_parent = src_node.parent


        # Return the copy
        return target

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
            target.child.append(target.loadnode(child))

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
                node.child.append(loadnode(child))
        # Ready
        return True
