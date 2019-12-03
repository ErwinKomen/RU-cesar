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


def atom(type, key, value):
    obj = dict(type=type, key=key, value=value)
    return obj


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
        self.xmldocument = ET.fromstring(sXml, parser)

        # Add a namespace for custom function(s)
        ns = ET.FunctionNamespace(None)
        # Add the function matches() to the namespace
        ns['matches'] = self.matches

        # DEBUGGING:
        # x = ET.tostring(self.xmldocument, xml_declaration=True, encoding="utf-8", pretty_print=False).decode("utf-8")
        return True

    def select_nodes(self, node, search):
        # OLD: result = self.xmldocument.findall(search)
        result = node.xpath(search)
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
    lst_dst = []
    lst_src = []
    dst_template = None
    pdx = None
    div = None
    par = None
    sent = None

    def __init__(self, input_dir, **kwargs):
        response = super(ConvertBasic, self).__init__(**kwargs)

        if self.src_ext:
            # Gather the source documents
            self.lst_src = [os.path.join(input_dir, f) for f in os.listdir(input_dir) if os.path.isfile(os.path.join(input_dir, f)) and self.src_ext in f]

        # Initialise template system
        self.file_loader = jinja2.FileSystemLoader(searchpath=os.path.abspath("./templates"))
        self.env = jinja2.Environment(loader=self.file_loader)
        return response

    def do_convert(self, output_dir, force=False):
        """Convert files from source to destination"""

        try:
            # Get the metadata information

            # Walk all source files
            for file in self.lst_src:
                # Determine the output file name
                outfile = os.path.join(output_dir, os.path.basename(file).replace(self.src_ext,self.dst_ext))

                # Check if it already exists and whether we should overwrite
                if not os.path.exists(outfile) or force:
                    # Show where we are
                    errHandle.Status("Working on file {}".format(file))

                    # Load the JSON file into memory
                    with open(file, "r") as fp:
                        oJsonFile = json.load(fp)

                    # Get the text id
                    text_id = oJsonFile['name']
                    meta = None
                    if 'meta' in oJsonFile: meta = oJsonFile['meta']

                    # Create an XML from the information we have
                    xmldoc = self.create_xml(text_id, meta, oJsonFile['sentence_list'])

                    # Save this one
                    # outfile = file.replace(self.src_ext,self.dst_ext)
                    with open(outfile, "w", encoding="utf-8") as fp:
                        str_output = ET.tostring(xmldoc, xml_declaration=True, encoding="utf-8", pretty_print=True).decode("utf-8")
                        fp.write(str_output)
                else:
                    errHandle.Status("Skipping file {}".format(outfile))

            # Return positively
            return 1
        except:
            errHandle.DoError("views/do_convert")
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
            ndx_sent_host = self.pdx.select_single_node(self.pdx.xmldocument, ".//" + self.tag_doc)

            # Walk the sentences in sent_list
            for sentence in sent_list:
                # Show where we are
                errHandle.Status("Processing: d.{}.p.{}.s.{}".format(sentence['div'], sentence['par'], sentence['sent']))

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
                    # Add this clause under tag_sent
                    self.add_clause(ndxSentence, clause)
                # Any post-processing on the XML
                self.adapt_main_xml(ndxSentence)

                # Debugging
                #x = ET.tostring(self.pdx.xmldocument)

            # Return the document
            xmldoc = self.pdx.xmldocument
            
            return xmldoc
        except:
            errHandle.DoError("views/create_xml")
            return None

    def adapt_main_clause(self, obj):
        return True

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
                self.add_feature(xml_this, feat)
            self.add_features(xml_sent, f)

    def adapt_main_clause(self, obj):
        """Main clauses must be IP-MAT"""

        obj['pos'] = "IP-MAT-" + obj['pos']
        return True

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
        """Add features"""

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

    def add_node(self, xml_this, txt, pos, feat_list):
        try:
            ndx_node = self.pdx.add_xml_child(xml_this, self.tag_node, 
                [atom("attribute", "Id", self.next_id()), 
                 atom("attribute", "Label", pos)])
            # Process the list of features
            for feat in feat_list:
                # Determine the <fs> @type attribute
                ftype = type
                # Add feature
                self.add_feature(ndx_node, feat, ftype)
            return ndx_node
        except:
            errHandle.DoError("views/ConvertHtreePsdx/add_node")
            return None
        

class ConvertHtreeFolia(ConvertBasic):
    src_ext = ".json"
    dst_ext = ".folia.xml"
    dst_template = "templates/target_folia.xml"


class ConvertPsdxHtree(ConvertBasic):
    src_ext = ".psdx"
    dst_ext = ".json"


class ConvertFoliaHtree(ConvertBasic):
    src_ext = ".folia.xml"
    dst_ext = ".json"

