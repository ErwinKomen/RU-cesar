# Generic
import os, sys
import csv, json
import jinja2
# XML processing
from xml.dom import minidom
# import xml.etree.ElementTree as ET
from lxml import etree as ET

# Application specific
import util                 # This allows using ErrHandle
from models import *        # This imports HierObj

errHandle = util.ErrHandle()

book = ['MAT','MRK','LUK','JHN','ACT','ROM','1CO','2CO','GAL','EPH','PHP','COL',\
        '1TH','2TH','1TI','2TI','TIT','PHM','HEB','JAS','1PE','2PE','1JN','2JN','3JN','JUD','REV']
book_ot = {'genesis': 'GEN', 'exodus': 'EXO', 'leviticus': 'LEV', 'numbers': 'NUM', \
    'deuteronomy': 'DEU', 'joshua': 'JOS', 'judges': 'JDG', 'ruth': 'RUT', \
    '1_samuel': '1SA', '2_samuel': '2SA', '1_kings': '1KI', '2_kings': '2KI', \
    '1_chronicles': '1CH', '2_chronicles': '2CH', 'ezra': 'EZR', 'nehemiah': 'NEH', \
    'esther': 'EST', 'job': 'JOB', 'psalms': 'PSA', 'proverbs': 'PRO', 'ecclesiastes': 'ECC', \
    'song_of_songs': 'SNG', 'isaiah': 'ISA', 'jeremiah': 'JER', 'lamentations': 'LAM', \
    'ezekiel': 'EZK', 'daniel': 'DAN', 'hosea': 'HOS', 'joel': 'JOL', 'amos': 'AMO', 'nahum': 'NAH', \
    'obadiah': 'OBA', 'jonah': 'JON', 'micah': 'MIC', 'habakkuk': 'HAB', \
    'zephaniah': 'ZEP', 'haggai': 'HAG', 'zechariah': 'ZEC', 'malachi': 'MAL'
    }


def atom(type, key, value):
    obj = dict(type=type, key=key, value=value)
    return obj

def get_book_abbr(file):
    try:
        sName = os.path.basename(file)
        arName = sName.split("-")
        abbr = ""
        if len(arName) == 1:
            # THis is the old testament: Get the book number and abbreviation
            sName = sName.replace(".json", "").lower()
            if sName in book_ot:
                abbr = book_ot[sName]
        else:
            # THis is the NT
            bkno = int(arName[0])-1
            abbr = book[bkno]
        return abbr
    except:
        msg = errHandle.get_error_message()
        errHandle.DoError("get_book_abbr")
        return ""


class XmlProcessor():
    """Basic XML operations"""

    xmldocument = None

    def __init__(self, **kwargs):
        response = super(XmlProcessor, self).__init__(**kwargs)
        return response

    def matches(self, context, text, pattern):
        """Check if text matches pattern"""

        bMatch = False
        lst_pattern = pattern.split("|")
        for patt in lst_pattern:
            if text == patt:
                bMatch = True
                break
        return bMatch

    def loadstring(self, sXml):
        # Make sure to parse blanks away!!
        parser = ET.XMLParser(remove_blank_text=True)
        sXml = sXml.replace("\n", "")
        try:
            self.xmldocument = ET.fromstring(sXml, parser)
        except:
            self.xmldocument = ET.fromstring(sXml.encode("utf-8"), parser)

        # Add a namespace for custom function(s)
        ns = ET.FunctionNamespace(None)
        # Add the function matches() to the namespace
        ns['matches'] = self.matches

        # DEBUGGING:
        # x = ET.tostring(self.xmldocument, xml_declaration=True, encoding="utf-8", pretty_print=False).decode("utf-8")
        return True

    def loadfile(self, sFile):
        """Load a file into xml"""

        try:
            # Load the UTF8 file into memory
            with open(sFile, "rb") as fp:
                sXml = fp.read()

            self.xmldocument = ET.fromstring(sXml)
            # Add a namespace for custom function(s)
            ns = ET.FunctionNamespace(None)
            # Add the function matches() to the namespace
            ns['matches'] = self.matches
            return self.xmldocument
        except:
            errHandle.DoError("XmlProcessor/loadfile")
            return None

    def select_nodes(self, node, search):
        # OLD: result = self.xmldocument.findall(search)
        result = node.xpath(search)
        return result

    def select_selfordescendant(self, node, tag):
        """Look for self::w and descendant::w"""
        result = []
        if node.tag == tag:
            result.append(node)
        for desc in node.xpath("./descendant::{}".format(tag)):
            result.append(desc)
        return result

    def select_single_node(self, node, search):
        # result = node.find(search)
        result = node.xpath(search)
        if result == None or len(result) == 0:
            return None
        else:
            return result[0]

    def add_xml_child(self, ndx_parent, s_tag, v_list = None):
        """Add a child under ndx_parent"""

        try:
            # Create the child
            ndx_this = ET.SubElement(ndx_parent, s_tag)
            # Check what values need to be added
            if v_list:
                for oValue in v_list:
                    type = oValue['type']
                    key = oValue['key']
                    value = oValue['value']

                    # Action depends on the kind of child
                    if type == "attribute":
                        ndx_this.set(key, value)
                    elif type == "child":
                        ndx_child = ET.SubElement(ndx_this, key)
                        ndx_child.text = value

            # Return the created child
            return ndx_this
        except:
            errHandle.DoError("XmlProcessor/add_xml_child")
            return None

    def add_xml_attribute(self, ndx_this, att_name, att_value = None):
        """Add an attribute"""

        ndx_this.set(att_name, att_value)

    def add_xml_attributes(self, ndx_this, att_list):
        """Add a list of attributes"""

        for k, v in att_list.items():
            ndx_this.set(k, v)


class ConvertBasic():
    src_ext = ""
    dst_ext = ""
    tag_doc = ""            # tag name for all sentences together
    tag_sent = ""           # The xml tag name for a sentence
    tag_node = ""           # Tag name for syntactic constituents
    tag_endnode = ""        # Tag name for end node
    action = ""
    lst_dst = []
    lst_src = []
    id_node = 0
    id_word = 0
    dst_template = None
    cmdi_template = "target_cmdi.xml"
    pdx = None
    div = None
    par = None
    sent = None
    map = {}                # Mapping between end-node @n and surface order

    def __init__(self, input_dir, **kwargs):
        response = super(ConvertBasic, self).__init__(**kwargs)

        if self.src_ext:
            # Gather the source documents
            self.lst_src = [os.path.join(input_dir, f) for f in os.listdir(input_dir) if os.path.isfile(os.path.join(input_dir, f)) and self.src_ext in f]

        # Initialise template system
        self.file_loader = jinja2.FileSystemLoader(searchpath=os.path.abspath("./templates"))
        self.env = jinja2.Environment(loader=self.file_loader)
        return response

    def do_htree_xml(self, output_dir, force=False, sBook=None, cmdi=False, debug=None):
        """Convert files from htree source to XML destination
        
        If the [cmdi] option is set, then an additional .cmdi.xml file is produced
        """
        outfile = ""
        outcmdi = ""
        cmdi_ext = ".cmdi.xml"

        try:
            # Get the metadata information

            # Walk all source files
            for file in self.lst_src:
                # Determine the book name
                abbr = get_book_abbr(file)
                if sBook == None or sBook == abbr:
                    # Get my bare file name
                    bare = os.path.basename(file).replace(self.src_ext,"")
                    # Determine the output file name
                    outfile = os.path.join(output_dir, os.path.basename(file).replace(self.src_ext,self.dst_ext))

                    # Possibly think of a CMDI file
                    if cmdi:
                        outcmdi = os.path.join(output_dir, os.path.basename(file).replace(self.src_ext, cmdi_ext ))

                    # Check if it already exists and whether we should overwrite
                    if not os.path.exists(outfile) or force:
                        # Show where we are
                        errHandle.Status("Working on file {}".format(file))

                        # Load the JSON file into memory
                        try:
                            with open(file, "r") as fp:
                                oJsonFile = json.load(fp)
                        except:
                            with open(file, "r", encoding="utf-8-sig") as fp:
                                oJsonFile = json.load(fp)

                        # Get the text id
                        text_id = oJsonFile['name']
                        meta = None
                        if 'meta' in oJsonFile: 
                            meta = oJsonFile['meta']
                        else:
                            meta = self.create_meta(text_id, abbr, bare)

                        # Create an XML from the information we have
                        xmldoc, words = self.create_xml(text_id, meta, oJsonFile['sentence_list'])
                        if meta:
                            meta['words'] = words

                        doctype = self.get_xml_doctype()

                        # Save this one
                        # outfile = file.replace(self.src_ext,self.dst_ext)
                        with open(outfile, "w", encoding="utf-8") as fp:
                            str_output = ET.tostring(xmldoc, xml_declaration=True, doctype=doctype, encoding="utf-8", pretty_print=True).decode("utf-8")
                            fp.write(str_output)

                        # Possibly also create a Metadata file .cmdi.xml
                        if cmdi and meta != None:
                            context = dict(meta=meta)
                            template = self.env.get_template(self.cmdi_template)
                            sXml = template.render(context)
                            with open(outcmdi, "w", encoding="utf-8") as fp:
                                fp.write(sXml)
                    else:
                        errHandle.Status("Skipping file {}".format(outfile))

            # Return positively
            return 1
        except:
            errHandle.DoError("views/do_htree_xml")
            return None

    def do_xml_htree(self, output_dir, force=False, sBook=None, debug=None):
        """Convert files from XML source to Htree destination"""

        try:
            # Validate
            if not self.dst_template: return None

            # Get the metadata information

            # Walk all source files
            for file in self.lst_src:
                # Determine the book name
                abbr = get_book_abbr(file)
                if sBook == None or sBook == abbr:
                    # Determine the output file name
                    outfile = os.path.join(output_dir, os.path.basename(file).replace(self.src_ext,self.dst_ext))

                    # Check if it already exists and whether we should overwrite
                    if not os.path.exists(outfile) or force:
                        # Show where we are
                        errHandle.Status("Working on file {}".format(file))

                        # Load the XML file into memory
                        self.pdx = XmlProcessor()
                        xmldoc = self.pdx.loadfile(file)
                        ndSent = self.pdx.select_nodes(xmldoc, "./descendant-or-self::{}".format(self.tag_sent))
                    
                        # Get the text id
                        text_id = os.path.basename(file).replace(self.src_ext, "")
                        meta = None

                        # Other initializations for one file
                        self.id_word = 1
                        self.id_node = 1

                        #oJsonFile = dict(name=text_id, meta=meta)

                        # Create an XML from the information we have
                        sXml = self.create_json(text_id, meta, ndSent)

                        # Write the object to the file
                        with open(outfile, "w", encoding="utf-8") as f:
                            errHandle.Status("Saving text {}".format(text_id))
                            f.write(sXml)
                    else:
                        errHandle.Status("Skipping file {}".format(outfile))

            # Return positively
            return 1
        except:
            errHandle.DoError("views/do_xml_htree")
            return None

    def do_htree_htree(self, output_dir, force=False, sBook=None, debug=None):
        """Convert files from htree source to htree destination
        
        This means that we are either surfacing or unraveling
        """

        if debug == None: debug = 0

        try:
            # Validate
            if not self.dst_template: return None

            # Get the metadata information

            # Walk all source files
            for file in self.lst_src:
                # Determine the book name
                abbr = get_book_abbr(file)
                if abbr != "" and (sBook == None or sBook == abbr):
                    # Determine the output file name
                    outfile = os.path.join(output_dir, os.path.basename(file).replace(self.src_ext,self.dst_ext))

                    # Check if it already exists and whether we should overwrite
                    if not os.path.exists(outfile) or force:
                        # Show where we are
                        errHandle.Status("Working on file {}".format(file))

                        # Load the JSON file into memory
                        try:
                            with open(file, "r") as fp:
                                oJsonFile = json.load(fp)
                        except:
                            with open(file, "r", encoding="utf-8-sig") as fp:
                                oJsonFile = json.load(fp)

                        # Get the text id
                        text_id = oJsonFile['name']
                        meta = None
                        if 'meta' in oJsonFile: meta = oJsonFile['meta']

                        # Create a context for the template
                        context = dict()
                        # Possibly add metadata, if this has been supplied
                        context['meta'] = meta
                        context['text_id'] = text_id

                        # Allow ancestor to add to context
                        context = self.add_to_context(context)

                        sentence_list = []

                        # Other initializations for one file
                        self.id_word = 1
                        self.id_node = 1
                        div = -1

                        # Walk all source sentences
                        for sentence in oJsonFile['sentence_list']:
                            # Properly read the source sentence
                            oSentSrc = SentenceObj.loadsent(sentence, text_id)
                            if oSentSrc == None:
                                pass
                            else:
                                sSentDst = ""

                                # Show where we are
                                if debug > 3:
                                    errHandle.Status("{} {}:{} s={}".format(text_id, oSentSrc.div, oSentSrc.divpar, oSentSrc.sent))
                                if div != oSentSrc.div:
                                    errHandle.Status("{} {}".format(text_id, oSentSrc.div))
                                    div = oSentSrc.div

                                # Debugging LUKE d.1.p.7.s.1
                                if oSentSrc.div == 1 and oSentSrc.divpar == 7 and oSentSrc.sent == 1:
                                    iStop = 1

                                # Create the destination sentence from the source one
                                if self.action == "to-surface":
                                    oSent, msg = oSentSrc.copy_surface(debug)
                                    sSentDst = json.dumps(oSent.get_object(), indent=2)
                                elif self.action == "to-surface-new":
                                    oSent, msg = oSentSrc.copy_surface_new(debug)
                                    if oSent == None:
                                        errHandle.DoError("ConvertBasic says {}".format(msg))
                                        sSentDst = ""
                                    else:
                                        sSentDst = json.dumps(oSent.get_object(), indent=2)
                                elif self.action == "from-surface":
                                    # TODO make code here
                                    pass

                                # Add to the destination
                                sentence_list.append(sSentDst)

                        # Add the sentence list to the context
                        context['sentence_list'] = sentence_list

                        # Create a JSON string based on this context
                        template = self.env.get_template(self.dst_template)
                        sJson = template.render(context)

                        # Save the string as UTF8
                        with open(outfile, "w", encoding="utf8") as f:
                            errHandle.Status("Saving text {}".format(text_id))
                            f.write(sJson)

                    else:
                        errHandle.Status("Skipping file {}".format(outfile))

            # Return positively
            return 1
        except:
            errHandle.DoError("views/do_htree_htree")
            return None

    def get_xml_doctype(self):
        return None
                
    def create_xml(self, text_id, meta, sent_list):
        """Create an XML based on the destination template"""

        xmldoc = None     # The XML document we are returning

        try:
            # Validate
            if not self.dst_template: return None

            # Create a context for the template
            context = dict()
            # Possibly add metadata, if this has been supplied
            context['meta'] = meta
            context['text_id'] = text_id

            # Allow ancestor to add to context
            context = self.add_to_context(context)

            # Create an XML based on this context
            template = self.env.get_template(self.dst_template)
            sXml = template.render(context)

            # Load the string into the XML Processor
            self.pdx = XmlProcessor()
            self.pdx.loadstring(sXml)

            sent_idx = 0
            # Find the XML element in the template that hosts all sentences
            if self.pdx.xmldocument.tag == self.tag_doc:
                ndx_sent_host = self.pdx.xmldocument
            else:
                ndx_sent_host = self.pdx.select_single_node(self.pdx.xmldocument, ".//" + self.tag_doc)
                if ndx_sent_host == None:
                    ndx_sent_host = self.pdx.select_selfordescendant(self.pdx.xmldocument, self.tag_doc)
                    if len(ndx_sent_host) > 0:
                        ndx_sent_host = ndx_sent_host[0]

            div = -1

            words = 0

            # Walk the sentences in sent_list
            for sentence in sent_list:
                # Show where we are
                # errHandle.Status("Processing: d.{}.p.{}.s.{}".format(sentence['div'], sentence['par'], sentence['sent']))
                if div != sentence['div']:
                    errHandle.Status("{} {}".format(text_id, sentence['div']))
                    div = sentence['div']

                # Get the sentence index
                object_sent_idx = sentence['sent']
                sent_idx += 1

                # Add an XML sentence under the XML grouping
                ndxSentence = self.pdx.add_xml_child(ndx_sent_host, self.tag_sent)

                # NOTE: a sentence as a whole (psdx: <forest>) does *not* have a syntactic category
                self.add_sent_details(ndxSentence, sent_idx, text_id, sentence['label'], sentence['txt'], 
                                      str(sentence['div']), str(sentence['par']), str(sentence['sent']), sentence['f'])

                # Add all the main clauses in this sentence
                for clause in sentence['child']:
                    # Possibly adapt this clause, because it must be a main clause
                    self.adapt_main_clause(clause)
                    # Get and add the number of words
                    words += self.words_in_clause(clause)
                    # Add this clause under tag_sent
                    self.add_clause(ndxSentence, clause)
                # Any post-processing on the XML
                self.adapt_main_xml(ndxSentence)

                # Debugging
                #x = ET.tostring(self.pdx.xmldocument)

            # Return the document
            xmldoc = self.pdx.xmldocument
            
            return xmldoc, words
        except:
            errHandle.DoError("views/create_xml")
            return None

    def create_meta(self, text_id, abbr, bare):
        return None

    def map_endnodes(self, ndSent):
        pass

    def words_in_clause(self, clause):
        return 0

    def create_json(self, text_id, meta, ndList):
        """Create a HTREE json"""

        lSent = []  # The json with the sentences
        # Create a context for the template
        context = dict()
        debug = 0

        try:
            # Possibly add metadata, if this has been supplied
            context['meta'] = meta
            context['text_id'] = text_id

            # Allow ancestor to add to context
            context = self.add_to_context(context)

            # Get the template
            template = self.env.get_template(self.dst_template)

            # Initialize counting
            sent = 0
            par = 1
            div = 1
            self.sent = 0
            # Walk the XML list of sentence nodes
            for ndSent in ndList:
                # Make sure we keep track of the sentence number
                self.sent += 1
                sent = self.sent
                # Get the correct div/par/sent in a generic way
                self.div, self.par, self.sent = self.get_xml_location(ndSent, div,par,sent)

                # Possibly prepare the mapping between end-node and surface order
                self.map_endnodes(ndSent)
                
                # Show where we are
                if debug > 3:
                    errHandle.Status("{} {}:{} s={}".format(text_id, self.div, self.par, self.sent))
                if div != self.div:
                    errHandle.Status("{} {}".format(text_id, self.div))
                    div = self.div

                # Convert this XML sentence into a sentence node
                if self.div >= 0:
                    oSentence = self.get_xml_sentence(text_id, ndSent)
                    if oSentence != None:
                        oJson = oSentence.get_object()

                        # lSent.append(oSentence.get_object())
                        lSent.append(json.dumps(oJson, indent=2))

            # return lSent
            # Add sentence list to context
            context['sentence_list'] = lSent

            # Create a JSON string based on this context
            sJson = template.render(context)

            return sJson
        except:
            errHandle.DoError("views/create_json")
            return None
        
    def adapt_main_clause(self, obj):
        return True

    def get_xml_location(self, ndSent, div, par, sent):
        return div, par, sent

    def get_xml_sentence(self, text_id, ndSent):
        """Convert the XML [ndSent] into a sentence object"""

        try:
            # Create a SentenceObj instance
            label = "{} {}:{}".format(text_id, self.div, self.par)
            txt = self.get_xml_sent_text(ndSent)
            oSentence = SentenceObj(label, self.sent, textid=text_id, txt=txt, div=self.div, divpar=self.par)

            # Walk all the main nodes in this sentence
            ndClauses = self.pdx.select_nodes(ndSent, "./child::{}".format(self.tag_node))
            for ndClause in ndClauses:
                # Call a recursive routine to build the elements of this clause
                oClause = self.get_xml_constituent(ndClause, oSentence, None)
                oSentence.child.append(oClause)

            return oSentence
        except:
            errHandle.DoError("views/get_xml_sentence")
            return None

    def get_xml_sent_text(self, ndSent):
        return ""

    def get_xml_constituent(self, ndConst, oSentence, oParent):
        """Given XML [ndConst], parse it into a HierObj under [oParent] in [oSentence]"""

        try:
            # Determine postag, txt, n and id
            postag = self.get_xml_pos(ndConst)
            txt = self.get_xml_const_txt(ndConst)
            id = self.get_xml_id(ndConst)

            # Create the new constituent from [ndConst]
            oConst = HierObj(oSentence, postag, txt, parent=oParent, id=id)
            oConst.f = self.get_xml_features(ndConst)
            # Constituent may not have @n: oConst.n = self.get_xml_n(ndConst)

            # Walk all the CHILDREN of [ndConst]
            for ndChild in ndConst:
                # Get the node name of this child
                if ndChild.tag == self.tag_endnode:
                    # Treat as endnode
                    oChild = self.get_xml_endnode(ndChild, oSentence, oConst)
                    # Add to my children
                    oConst.child.append(oChild)
                elif ndChild.tag == self.tag_node:
                    # Call myself
                    oChild = self.get_xml_constituent(ndChild, oSentence, oConst)
                    # Add this to my children
                    oConst.child.append(oChild)
            
            # REturn our node
            return oConst
        except:
            errHandle.DoError("views/get_xml_clause")
            return None

    def get_xml_endnode(self, ndConst, oSentence, oParent):
        """Given XML [ndConst], parse it into a HierObj under [oParent] in [oSentence]"""

        try:
            # Determine postag, txt, n and id
            postag = self.get_xml_pos(ndConst)
            txt = self.get_xml_const_txt(ndConst)
            id = self.get_xml_id(ndConst)

            # Create the new constituent from [ndConst]
            oConst = HierObj(oSentence, postag, txt, parent=oParent, id=id)
            oConst.n = self.get_xml_n(ndConst)
            oConst.f = self.get_xml_features(ndConst)
            oConst.type = self.get_word_type(txt, postag)

            # REturn our node
            return oConst
        except:
            errHandle.DoError("views/get_xml_clause")
            return None

    def get_xml_pos(self, ndConst):
        """Return the part-of-speech tag of [ndConst]"""
        return ""

    def get_xml_n(self, ndConst):
        """Return the n tag of [ndConst]"""

        response = self.id_word
        self.id_word += 1
        return response

    def get_word_type(self, txt, postag):
        return "Vern"

    def get_xml_const_txt(self, ndConst):
        """Return the txt of [ndConst]"""
        return ""

    def get_xml_id(self, ndConst):
        """Return the id of [ndConst] - as a number"""
        response = self.id_node
        self.id_node += 1
        return response

    def get_xml_features(self, ndNode):
        """Given the NODE (constituent or word), return a dictionary of features"""
        return []

    def adapt_main_xml(self, xmlobj):
        return True

    def add_clause(self, xml_parent, obj):
        """Add the [obj] as XML child under xml_parent"""

        oBack = None
        try:
            # Top level: add [obj]
            if 'type' in obj:
                if obj['type'] == "Star":
                    iStop = 1
                # This is an end node: add the end-node attributes
                n = 0 if "n" not in obj else obj['n']
                ndx_endnode = self.add_endnode(xml_parent, obj['type'], obj['txt'], obj['pos'], n, obj['f'] )
            else:
                # This is another node: add the basics
                ndx_node = self.add_node(xml_parent, obj['txt'], obj['pos'], obj['f'] )

                # Process the children
                if 'child' in obj:
                    for oChild in obj['child']:
                        self.add_clause(ndx_node, oChild)

            # Return the element that has been made
            return oBack
        except:
            errHandle.DoError("views/ConvertBasic/add_clause")
            return None

    def add_to_context(self, context):
        """User overwritable function to add to the context"""
        return context

    def add_sent_details(self, xml_sent, sent_id, text_id, label, txt, div, par, sent, f):
        """Add sentence details """
        pass

    def add_features(self, xml_this, f_list):
        """Add the features in the list"""
        pass

    def add_endnode(self, xml_this, type, txt, pos, n, feat_list):
        return None

    def add_node(self, xml_this, txt, pos, feat_list):
        return None


class ConvertHtreePsdx(ConvertBasic):
    src_ext = ".json"
    dst_ext = ".psdx"
    tag_doc = "forestGrp"
    tag_sent = "forest"
    tag_node = "eTree"
    tag_endnode = "eLeaf"
    dst_template = "target_psdx.xml"
    idnum = 0

    def next_id(self):
        self.idnum += 1
        return str(self.idnum)

    def add_sent_details(self, xml_sent, sent_id, text_id, label, txt, div, par, sent, feat_list):
        """Add details of <forest> for PSDX"""

        oAttrs = dict(forestId=str(sent_id), 
                      File=text_id, 
                      TextId=text_id, 
                      Location=label.strip())
        if div != self.div: oAttrs['Section'] = div
        if par != self.par: oAttrs['Paragraph'] = par
        self.div = div
        self.par = par
        self.sent = sent
        self.pdx.add_xml_attributes(xml_sent, oAttrs)
        # Add <div> org
        self.pdx.add_xml_child(xml_sent, "div", [
            atom("attribute", "lang", "org"), atom("child", "seg", txt)])
        # Add <div> english
        self.pdx.add_xml_child(xml_sent, "div", [
            atom("attribute", "lang", "eng"), atom("child", "seg", "")])
        # If there are features at this level, add them
        if feat_list != None and len(feat_list) > 0:
            for feat in feat_list:
                self.add_feature(xml_sent, feat)
        # Return positively
        return True

    def adapt_main_clause(self, obj):
        """Main clauses must be IP-MAT"""

        obj['pos'] = "IP-MAT-" + obj['pos']
        return True

    def words_in_clause(self, obj):
        words = []

        def get_words(obj):
            if 'type' in obj and obj['type'] == "Vern":
                words.append(obj)
            if 'child' in obj:
                for child in obj['child']:
                    get_words(child)

        # Get all the word objects into a list
        get_words(obj)

        # Return the size of this list
        return len(words)


    def adapt_main_xml(self, ndx_this):
        """This is the equivalent of [eTreeSentence] in Cesax
        
        Determine the correct values of the @from and the @to attributes 
        This goes both for <eLeaf> as well as <eTree> nodes
        """

        # Initialisations
        strNoText = "CODE|META|METADATA|E_S"
        # Validate
        if ndx_this == None: return false

        try:
            # Make sure we have the forest
            ndxFor = self.pdx.select_single_node(ndx_this, "./ancestor-or-self::forest")
            # Check if the original text if is there
            ndxOrg = self.pdx.select_single_node(ndxFor, "./child::div[@lang='org']/seg")
            # Get the text of the sentence
            strSentence = ndxOrg.text
            if strSentence == "":
                # We cannot yet process this
                pass
            else:
                # The text is already there, and we do not change it
                iCurrentPos = -1
                iFrom = 0
                iTo = 0
                iSpace = 0
                # Get a list of all the words in the text
                ndxList = self.pdx.select_nodes(ndxFor, "./descendant::eLeaf[count(ancestor::eTree[matches(@Label, '{}')])=0]".format(strNoText))
                for ndxEleaf in ndxList:
                    # Get the word
                    strWord = ndxEleaf.get("Text")
                    # find the position of the word within the sentence
                    if iCurrentPos < 0:
                        iCurrentPos = strSentence.find(strWord)
                    else:
                        iCurrentPos = strSentence.find(strWord, iCurrentPos+1)
                    # Do we have the word?
                    if iCurrentPos < 0:
                        # Retry from the beginning
                        iCurrentPos = strSentence.find(strWord)
                    # Validate once more
                    if iCurrentPos < 0:
                        iStop = 1
                    # Get the size of this element
                    iSize = len(strWord)
                    # Calculate from and to
                    iFrom = iCurrentPos
                    iTo = iFrom + iSize
                    # Set these attributes
                    ndxEleaf.set("from", str(iFrom))
                    ndxEleaf.set("to", str(iTo))
                # Get a list of all the <eTree> nodes
                ndxList = self.pdx.select_nodes(ndxFor, "./descendant::eTree")
                # Treat them all
                for ndxEtree in ndxList:
                    # Determine this one's starting position
                    ndxLeaf = self.pdx.select_single_node(ndxEtree, "./descendant::eLeaf[1]")
                    if ndxLeaf != None:

                        # --------- DEBUGGING ------------
                        x = ET.tostring(ndxFor, pretty_print=True, encoding="utf-8").decode("utf-8")

                        # Get the value
                        strFrom = ndxLeaf.get("from")
                        # Set this for the <eTRee>
                        ndxEtree.set("from", strFrom)
                    # Determine the end position
                    ndxLeaf = self.pdx.select_single_node(ndxEtree, "./descendant::eLeaf[last()]")
                    if ndxLeaf != None:
                        # Get the value
                        strTo = ndxLeaf.get("to")
                        # Set this for the <eTRee>
                        ndxEtree.set("to", strTo)
            return True
        except:
            errHandle.DoError("ConvertHtreePsdx/adapt_main_xml")
            return None

    def add_feature(self, xml_this, feat, type="leaf"):
        """Add one feature"""

        try:
            # Check if there is an <fs> node child
            ndxFS = self.pdx.select_single_node(xml_this, './child::fs[@type="{}"]'.format(type))
            if ndxFS == None:
                # Add the <fs> node with a @type
                ndxFS = self.pdx.add_xml_child(xml_this, "fs", [atom("attribute", "type", type)])
                
            # Check presence of the <f> node
            ndxF = self.pdx.select_single_node(ndxFS, './child::f[@name="{}"]'.format(feat['name']))
            if ndxF == None:
                ndxF = self.pdx.add_xml_child(ndxFS, "f", [atom("attribute", "name", feat['name'])])
            # Set the correct value for the feature value
            ndxF.set("value", feat['value'])
            # Return this feature <f>
            return ndxF
        except:
            errHandle.DoError("views/ConvertHtreePsdx/add_feature")
            return None

    def add_endnode(self, xml_this, type, txt, pos, n, feat_list):
        try:
            if txt == "":
                txt = " "
            if type == "Star":
                str_position = "{0:08d}".format(n)
                ndx_node = xml_this
                txt = pos
                ndx_endnode = self.pdx.add_xml_child(ndx_node, self.tag_endnode,
                    [atom("attribute", "Type", type),
                     atom("attribute", "Text", txt),
                     atom("attribute", "n", str_position)])
            elif type == "Vern" or type == "Punc" or type == "Punct":
                ndx_node = self.pdx.add_xml_child(xml_this, self.tag_node, 
                    [atom("attribute", "Id", self.next_id()), 
                     atom("attribute", "Label", pos)])
                str_position = "{0:08d}".format(n)
                ndx_endnode = self.pdx.add_xml_child(ndx_node, self.tag_endnode,
                    [atom("attribute", "Type", type),
                     atom("attribute", "Text", txt),
                     atom("attribute", "n", str_position)])
            # Process the list of features
            for feat in feat_list:
                # Determine the <fs> @type attribute
                ftype = type
                if feat['name'] == "lemma":
                    ftype = "M"
                    feat['name'] = "l"
                # Add feature
                self.add_feature(ndx_node, feat, ftype)
            # Also add the "n" as feature
            feat = {"name": "n", "value": str_position}
            self.add_feature(ndx_node, feat, "etctc")
            return ndx_node
        except:
            errHandle.DoError("views/ConvertHtreePsdx/add_endnode")
            return None

    def add_node(self, xml_this, txt, pos, feat_list, type=None):
        try:
            ndx_node = self.pdx.add_xml_child(xml_this, self.tag_node, 
                [atom("attribute", "Id", self.next_id()), 
                 atom("attribute", "Label", pos)])
            # Process the list of features
            for feat in feat_list:
                # Determine the <fs> @type attribute
                ftype = "htree" if type == None else type
                # Add feature
                self.add_feature(ndx_node, feat, ftype)
            return ndx_node
        except:
            errHandle.DoError("views/ConvertHtreePsdx/add_node")
            return None

    def create_meta(self, text_id, abbr, bare):
        meta = {}
        meta['id'] = bare
        part = ""
        if abbr:
            if abbr in book:
                part = "nt"
            else:
                part = "ot"
        if part:
            meta['texttype'] = "bible"
            meta['texttitle'] = abbr
            meta['textclass'] = part
            if part == "ot":
                meta['project'] = "HebOT"
                meta['collname'] = "ETCBC 2017 Hebrew Bible"
                meta['collcode'] = "ETCBC_2017"
                meta['lngname'] = "Hebrew"
                meta['lngethno'] = "heb"  
            else:
                meta['project'] = "GrkNT"
                meta['collname'] = "Society for Biblical Literature GNT"
                meta['collcode'] = "SBLGNT"
                meta['lngname'] = "Greek"
                meta['lngethno'] = "grk"
            meta['sourcecontinent'] = "Asia"
            meta['sourcecountry'] = "Israel"
            meta['translated'] = "No"
        return meta
        

class ConvertHtreeFolia(ConvertBasic):
    src_ext = ".json"
    dst_ext = ".folia.xml"
    dst_template = "target_folia.xml"


class ConvertHtreeLowfat(ConvertBasic):
    src_ext = ".json"
    dst_ext = ".xml"
    tag_doc = "book"
    tag_sent = "sentence"
    tag_node = "wg"
    tag_endnode = "w"
    dst_template = "target_lowfat.xml"

    def next_id(self):
        self.idnum += 1
        return str(self.idnum)

    def add_sent_details(self, xml_sent, sent_id, text_id, label, txt, div, par, sent, feat_list):
        """Add details of <sentence> for lowfat
        
        Lowfat is pretty easy, but it does need two additional elements at the <sentence> level:
        1 - <milestone unit="verse" id="Book.ch.vs">Book.ch.vs</milestone>
        2 - <p>sentence text</p>
        """

        # (1): no <sentence> attributes are needed
        self.div = div
        self.par = par
        self.sent = sent

        # (2) Add <milestone>
        bkchvs = "{}.{}.{}".format(text_id, div, par)
        oAttrs = dict(unit="verse", id=bkchvs)
        ndMilestone = self.pdx.add_xml_child(xml_sent, "milestone", [
            atom("attribute", "unit", "verse"),
            atom("attribute", "id", bkchvs)])
        ndMilestone.text = bkchvs

        # (3) Add the text in <p>
        ndP = self.pdx.add_xml_child(xml_sent, "p")
        ndP.text = txt

        # (4) There can be no features at the level of <sentence>

        # REturn positively
        return True

    def add_feature(self, xml_this, feat, type="leaf"):
        """Add one feature"""

        try:
            # lowfat features are simply added as k/v attributes to the node
            ndxF = self.pdx.add_xml_attribute(xml_this, feat['name'], feat['value'])

            # Note: the [type] is *not* taken into account

            # Return this feature <f>
            return ndxF
        except:
            errHandle.DoError("views/ConvertHtreeLowfat/add_feature")
            return None

    def add_endnode(self, xml_this, type, txt, pos, n, feat_list):
        """Add an end-node to [xml_this] in LOWFAT"""

        try:
            if txt == "":
                txt = " "
            if type == "Star":
                ndx_node = xml_this
                txt = pos
                ndx_endnode = self.pdx.add_xml_child(ndx_node, self.tag_endnode,
                    [atom("attribute", "class", "star")])
                ndx_endnode.text = txt
            elif type == "Vern" or type == "Punc" or type == "Punct":
                ndx_endnode = self.pdx.add_xml_child(xml_this, self.tag_endnode,
                    [atom("attribute", "class", pos)])
                ndx_endnode.text = txt

                #ndx_node = self.pdx.add_xml_child(xml_this, self.tag_node, 
                #    [atom("attribute", "Id", self.next_id()), 
                #     atom("attribute", "Label", pos)])
                #str_position = "{0:08d}".format(n)
                #ndx_endnode = self.pdx.add_xml_child(ndx_node, self.tag_endnode,
                #    [atom("attribute", "Type", type),
                #     atom("attribute", "Text", txt),
                #     atom("attribute", "n", str_position)])
            # Process the list of features
            for feat in feat_list:
                # Add feature (the type is not taken into consideration)
                if feat['name'] == "n":
                    ndx_endnode.set("n", feat['value'])
                else:
                    self.add_feature(ndx_endnode, feat)
            # Do *NOT* add the "n" as feature - we already have our own @n
            x = ET.tostring(xml_this)
            # REturn the end-node that we have created
            return ndx_endnode
        except:
            errHandle.DoError("views/ConvertHtreeLowfat/add_endnode")
            return None

    def add_node(self, xml_this, txt, pos, feat_list):
        """Add a constituent node to [xml_this] in LOWFAT"""

        oFirst = {'AdjP': 'adj', 'AdvP': 'adv', 'PP': 'adv'}
        oSecond = {'Subj': 's', 'Objc': 'o', 'Cmpl': 'o'}

        try:
            ndx_node = self.pdx.add_xml_child(xml_this, self.tag_node, 
                [atom("attribute", "class", pos)])
            # Process the list of features
            bHasRole = False
            for feat in feat_list:
                # Add feature
                self.add_feature(ndx_node, feat)
                # Note if this was @role
                if feat['name'] == "role": bHasRole = True
            # Check if there was a 'role' in the list of features
            if not bHasRole:
                # Try to derive the 'role' from the POS-tag
                arPos = pos.split("-")
                role = ""
                if len(arPos) > 1:
                    if arPos[0] in oFirst:
                        role = oFirst[arPos[0]]
                    elif arPos[1] in oSecond:
                        role = oSecond[arPos[1]]
                if role != "":
                    feat = dict(name="role", value=role)
                    self.add_feature(ndx_node, feat)
            return ndx_node
        except:
            errHandle.DoError("views/ConvertHtreeLowfat/add_node")
            return None

    def get_xml_doctype(self):
        return "<?xml-stylesheet href=\"treedown.css\"?>"


class ConvertPsdxHtree(ConvertBasic):
    src_ext = ".psdx"
    dst_ext = ".json"
    tag_doc = "forestGrp"
    tag_sent = "forest"
    tag_node = "eTree"
    tag_endnode = "eLeaf"


class ConvertPsdHtree(ConvertBasic):
    """Convert from bracketed labelling format"""

    pass


class ConvertHtreeSurface(ConvertBasic):
    src_ext = ".json"
    dst_ext = ".json"
    idnum = 0
    dst_template = "target_htree.txt"
    action = "to-surface-new" # "to-surface"


class ConvertSurfaceHtree(ConvertBasic):
    src_ext = ".json"
    dst_ext = ".json"
    idnum = 0
    dst_template = "target_htree.txt"
    action = "from-surface"


class ConvertLowfatHtree(ConvertBasic):
    src_ext = ".xml"
    dst_ext = ".json"
    tag_doc = "book"
    tag_sent = "sentence"
    tag_node = "wg"
    tag_endnode = "w"
    idnum = 0
    dst_template = "target_htree.txt"

    def next_id(self):
        self.idnum += 1
        return str(self.idnum)

    def get_xml_location(self, ndSent, div, par, sent):
        """Figure out where we are in div/par/sent from [ndSent]"""

        try:
            # Note: lowfat has a <milestone unit="verse" id="book.chapter.verse">
            #       and div=chapter, par=verse
            ndMilestone = self.pdx.select_single_node(ndSent,"./child::milestone[@unit='verse']")
            if ndMilestone != None:
                loc_id = ndMilestone.get('id')
                arLoc = loc_id.split(".")
                div = int(arLoc[1])
                par = int(arLoc[2])
                if div != self.div or par != self.par:
                    sent = 1
            return div, par, sent
        except:
            errHandle.DoError("get_xml_location")
            return -1,-1,-1

    def map_endnodes(self, ndSent):
        """Map all the end nodes in ndSent] to where they should be in position"""

        ndLit = self.pdx.select_nodes(ndSent, "./descendant::w")
        # Create a list from this
        endnodes = []
        for node in ndLit:
            endnodes.append(node.get("n"))
        # Sort them
        endnodes.sort()
        # Create the mapping
        id = 1
        for node in endnodes:
            self.map[node] = id
            id += 1
        return True

    def get_xml_sent_text(self, ndSent):
        return self.pdx.select_single_node(ndSent, "./p").text

    def get_xml_pos(self, ndConst):
        """Return the part-of-speech tag of [ndConst]"""

        postag = ""
        if ndConst is not None:
            postag = ndConst.get("class")
            if postag == None:
                # See if the constituent has feature "role"
                role = ndConst.get("role")
                postag = "none" if role == None else role
        return postag

    def get_xml_n(self, ndConst):
        """Return the n tag of [ndConst]"""

        ntag = -1
        try:
            if ndConst is not None:
                # Get the @n
                sN = ndConst.get("n")
                # Find out what the number is from the mapping
                ntag = self.map[sN]
            return ntag
        except:
            errHandle.DoError("ConvertLowfatHtree/get_xml_n")
            return -1

    def get_xml_const_txt(self, ndConst):
        """Return the txt of constituent [ndConst]"""

        try:
            lText = []
            # ndWords = self.pdx.select_nodes(ndConst, "./self-or-descendant::w")
            ndWords = self.pdx.select_selfordescendant(ndConst, "w")
            for ndWord in ndWords:
                lText.append(ndWord.text)
            return " ".join(lText)
        except:
            errHandle.DoError("get_xml_const_txt")
            return None

    def get_xml_features(self, ndNode):
        """Given the NODE (constituent or word), return a dictionary of features"""

        f = []
        exclude = ['class']
        try:
            # Walk all the attributes of [ndNode]
            for k,v in ndNode.attrib.items():
                if k not in exclude:
                    f.append({'name': k, 'value': v})
                    #f[k] = v
        except:
            errHandle.DoError("get_xml_features")
            f = None
        # Return the result
        return f


class ConvertFoliaHtree(ConvertBasic):
    src_ext = ".folia.xml"
    dst_ext = ".json"


