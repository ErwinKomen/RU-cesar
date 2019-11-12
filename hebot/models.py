

class HierObj():
    """Hierarchical object"""

    label = ""  # Label
    sent = 1    # Sentence number
    pos = ""    # Grammatical category
    txt = ""    # The text associated with this instance
    type = None # The type, if it is an end-node (Punct, Vern, Star)
    f = []      # List of features
    child = []  # List of child HierObj instances

    def __init__(self, **kwargs):
        response = super(HierObj, self).__init__(**kwargs)
        return response
