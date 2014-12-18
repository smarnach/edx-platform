
import sys
from lxml import etree
from optparse import OptionParser


def validate(xsd_filename, xml_filename):
    with open(xsd_filename, 'r') as f:
        schema_root = etree.XML(f.read())

    schema = etree.XMLSchema(schema_root)
    xmlparser = etree.XMLParser(schema=schema)

    with open(xml_filename, 'r') as f:
        etree.fromstring(f.read(), xmlparser)
    return True

def main():
    """
    Validate an XML file using an XSD.
    """
    usage  = "usage: ./validate_xml.py [options]"
    parser = OptionParser(usage, version="validate_xml 0.1")

    parser.add_option("-i", "--inputXml", type="string", dest="inputXmlFile", default="stdin",
                      help="filename for the xml file to read in. Reads from stdin by default." )
    parser.add_option("-s", "--inputXsd", "--schema",  type="string", dest="inputXsdFile", default=None,
                      help="filename for the xsd (schema) file to read in." )

    (options, args) = parser.parse_args()

    if len(args) > 0:
        parser.error("The argument(s) '%s' are not valid. See the syntax help under -h." % args)

    if options.inputXmlFile == "stdin":
        if sys.stdin.isatty():
            parser.error("If no input xml file is specified, the xml must be piped to stdin.")
        inputXmlFile = 'stdin.xml'
        newFile = open(inputXmlFile, 'w')
        newFile.write(sys.stdin.read())
        newFile.close()
    else:
       inputXmlFile = options.inputXmlFile

    if options.inputXsdFile is None:
        parser.error("XSD file is required.")

    if validate(options.inputXsdFile, inputXmlFile):
        print "%s validates." % inputXmlFile

if __name__ == '__main__':
    main()
