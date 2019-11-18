# Generic
import os, sys
import csv, json
import jinja2
# XML processing
from xml.dom import minidom
import xml.etree.ElementTree as ET

# Application specific
import util                 # This allows using ErrHandle
from models import *        # This imports HierObj

errHandle = util.ErrHandle()


class XmlProcessor():
    """Basic XML operations"""

    xmldocument = None

    def __init__(self, sXml, **kwargs):
        response = super(XmlProcessor, self).__init__(**kwargs)
        self.xmldocument = ET.fromstring(sXml)
        return response

    def select_nodes(self, search):
        result = self.xmldocument.findall(search)
        return result

    def select_single_node(self, search):
        result = self.xmldocument.find(search)
        return result

    def atom(type, key, value):
        obj = dict(type=type, key=key, value=value)
        return obj

    def add_xml_child(self, ndx_parent, s_tag, v_list = None):
        """Add a child under ndx_parent"""

        # Create the child
        ndx_this = ET.SubElement(ndx_parent, s_tag)
        # Check what values need to be added
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

class ConvertBasic():
    src_ext = ""
    dst_ext = ""
    xml_doc = ""            # tag name for all sentences together
    xml_sent = ""           # The xml tag name for a sentence
    xml_node = ""           # Tag name for syntactic constituents
    xml_endnode = ""        # Tag name for end node
    lst_dst = []
    lst_src = []
    dst_template = None
    pdx = None

    def __init__(self, input_dir, **kwargs):
        response = super(ConvertBasic, self).__init__(**kwargs)

        if self.src_ext:
            # Gather the source documents
            self.lst_src = [os.path.join(input_dir, f) for f in os.listdir(input_dir) if os.path.isfile(os.path.join(input_dir, f)) and self.src_ext in f]

        # Initialise template system
        self.file_loader = jinja2.FileSystemLoader(searchpath=os.path.abspath("./templates"))
        self.env = jinja2.Environment(loader=self.file_loader)
        return response

    def do_convert(self):
        """Convert files from source to destination"""

        try:
            # Get the metadata information

            # Walk all source files
            for file in self.lst_src:
                # Load the JSON file into memory
                with open(file, "r") as fp:
                    oJsonFile = json.load(fp)

                # Get the text id
                text_id = oJsonFile['name']
                meta = None
                if 'meta' in oJsonFile: meta = oJsonFile['meta']

                # Create an XML from the information we have
                self.create_xml(text_id, meta, oJsonFile['sentence_list'])

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
            self.pdx = XmlProcessor(sXml)

            sent_idx = 0
            # Find the XML element in the template that hosts all sentences
            ndx_sent_host = self.pdx.select_single_node(".//" + self.xml_doc)

            # Walk the sentences in sent_list
            for sentence in sent_list:
                # Get the sentence from the JSON
                obj_sent = sent_list[sent_idx]
                sent_idx = obj_sent['sent']

                # Add an XML sentence under the XML grouping
                xml_sent = self.pdx.add_xml_child(ndx_sent_host, self.xml_sent)

                # NOTE: a sentence as a whole (psdx: <forest>) does *not* have a syntactic category
                self.add_sent_details(xml_sent, sent_idx, obj_sent['label'], obj_sent['txt'], obj_sent['f'])

                # Create an XML sentence from this sentence

                pass



            return xmldoc
        except:
            errHandle.DoError("views/create_xml")
            return None

    def add_to_context(self, context):
        """User overwritable function to add to the context"""
        return context

    def add_sent_details(self, xml_sent, sent_id, label, txt, f):
        """Add sentence details """
        pass

    def add_features(self, xml_this, f_list):
        """Add the features in the list"""
        pass


class ConvertHtreePsdx(ConvertBasic):
    src_ext = ".json"
    dst_ext = ".psdx"
    xml_doc = "forestGrp"
    xml_sent = "forest"
    xml_node = "eTree"
    xml_endnode = "eLeaf"
    dst_template = "target_psdx.xml"

    def add_sent_details(self, xml_sent, sent_id, label, txt, f):
        """Add details of <forest> for PSDX"""

        self.pdx.add_xml_attribute("forestId", str(sent_id))
        self.pdx.add_xml_attribute("File", "")
        self.pdx.add_xml_attribute("TextId", "")
        self.pdx.add_xml_attribute("Location", label.strip())
        # Add <div> org
        self.pdx.add_xml_child(xml_sent, "div", [
            self.pdx.atom("attribute", "lang", "org"), self.pdx.atom("child", "seg", txt)])
        # Add <div> english
        self.pdx.add_xml_child(xml_sent, "div", [
            self.pdx.atom("attribute", "lang", "eng"), self.pdx.atom("child", "seg", "")])
        # If there are features at this level, add them
        if f != None and len(f) > 0:
            self.add_features(xml_sent, f)

    def add_features(self, xml_this, f_list):
        """Add features"""

        

class ConvertHtreeFolia(ConvertBasic):
    src_ext = ".json"
    dst_ext = ".folia.xml"
    dst_template = "templates/target_folia.xml"


class ConvertPsdxHtree(ConvertBasic):
    src_ext = ".psdx"
    dst_ext = ".json"
    # src_template = "templates/"


class ConvertFoliaHtree(ConvertBasic):
    src_ext = ".folia.xml"
    dst_ext = ".json"
    # src_template = "templates/"

