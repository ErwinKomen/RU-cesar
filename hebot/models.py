"""
The classes in this models.py are used by the Python application hebot

"""

import copy

class HierObj():
    """Hierarchical object"""

    pos = ""    # Grammatical category
    txt = ""    # The text associated with this instance
    type = None # The type, if it is an end-node (Punct, Vern, Star)
    n = None    # If present, this is a position within the surface text
    id = -1     # Numerical identifier as used within the DB-system
    f = []      # List of features
    child = []  # List of child HierObj instances
    par = None  # Each object may be part of another

    def __init__(self, pos, txt="", parent=None, id=-1, **kwargs):
        response = super(HierObj, self).__init__(**kwargs)
        self.pos = pos
        self.txt = txt
        self.f = []
        self.child = []
        self.type = None
        self.n = None
        self.par = parent
        self.id = id
        return response

    #def add_child(self, obj):
    #    """Add one child to me"""

    #    self.child.append(copy.deepcopy(obj))

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


class SentenceObj():
    """Sentence object"""

    label = ""  # Label
    sent = 1    # Sentence number
    pos = ""    # Grammatical category
    txt = ""    # The text associated with this instance
    type = None # The type, if it is an end-node (Punct, Vern, Star)
    id = -1     # Numerical identifier as used within the DB-system
    f = []      # List of features
    child = []  # List of child HierObj instances

    def __init__(self, label, sent, txt="", id=-1, **kwargs):
        response = super(SentenceObj, self).__init__(**kwargs)
        self.label = label
        self.sent = sent
        self.txt = txt
        self.id = id
        self.f = []
        self.child = []
        self.type = None
        return response

    #def add_child(self, obj):
    #    """Add one child to me"""

    #    self.child.append(copy.deepcopy(obj))

    def get_object(self):
        """Return an object representation of me"""

        js = dict(label=self.label, sent=self.sent, pos=self.pos, txt=self.txt, f=self.f, id=self.id)
        if self.type: js['type'] = self.type
        if self.child:
            children =[]
            for ch in self.child:
                children.append(ch.get_object())
            js['child'] = children
        return js
    


