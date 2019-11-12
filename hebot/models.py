"""
The classes in this models.py are used by the Python application hebot

"""

class HierObj():
    """Hierarchical object"""

    pos = ""    # Grammatical category
    txt = ""    # The text associated with this instance
    type = None # The type, if it is an end-node (Punct, Vern, Star)
    f = []      # List of features
    child = []  # List of child HierObj instances

    def __init__(self, pos, txt="", **kwargs):
        response = super(HierObj, self).__init__(**kwargs)
        self.pos = pos
        self.txt = txt
        return response

class SentenceObj():
    """Sentence object"""

    label = ""  # Label
    sent = 1    # Sentence number
    pos = ""    # Grammatical category
    txt = ""    # The text associated with this instance
    type = None # The type, if it is an end-node (Punct, Vern, Star)
    f = []      # List of features
    child = []  # List of child HierObj instances

    def __init__(self, label, sent, txt="", **kwargs):
        response = super(SentenceObj, self).__init__(**kwargs)
        self.label = label
        self.sent = sent
        self.txt = txt
        return response

    


