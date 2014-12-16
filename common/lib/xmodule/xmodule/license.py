"""
Different types of licenses for content

This file contains a base license class as well as a some useful specific license classes, namely:
    - ARRLicense (All Rights Reserved License)
    - CCLicense (Creative Commons License)

The classes provide utility funcions for dealing with licensing, such as getting an image representation
of a license, a url to a page describing the specifics of the license, converting licenses to and from json
and storing some vital information about licenses, in particular the version.
"""
import requests
from cStringIO import StringIO
from lxml import etree
from django.utils.translation import ugettext as _

from xblock.fields import JSONField


class License(JSONField):
    """
    Base License class
    """

    _default = None
    MUTABLE = False

    def __init__(self, license=None, version=None, *args, **kwargs):
        self.license = license
        self.version = version
        super(JSONField, self).__init__(*args, **kwargs)

    @property
    def html(self):
        """
        Return a piece of html that describes the license

        This method should be overridden in child classes to provide the desired html.
        """
        return u"<p>" + _("This resource is not licensed.") + u"</p>"

    def to_json(self, value):
        """
        Return a JSON representation of the license
        """
        if value is None:
            return None
        elif isinstance(value, License):
            return {"license": value.license, "version": value.version}
        else:
            raise TypeError("Cannot convert {!r} to json".format(value))


    def from_json(self, field):
        """
        Construct a new license object from a valid JSON representation
        """
        if field is None:
            return field
        elif not field or field is "":
            return None
        elif isinstance(field, basestring):
            if field == "ARR":
                return ARRLicense(field)
            elif field[0:5] == "CC-BY" or field == "CC0":
                return CCLicense(field)
            else:
                raise ValueError('Invalid license.')
        elif isinstance(field, dict):
            return parse_license(field['license'], field['version'])
        elif isinstance(field, License):
            return field
        else:
            raise ValueError('Invalid license.')

    enforce_type = from_json


class ARRLicense(License):
    """
    License class for an 'All rights reserved' license
    """

    def __init__(self, license, version=None, *args, **kwargs):
        super(ARRLicense, self).__init__(license, version, *args, **kwargs)

    @property
    def html(self):
        """
        Return a piece of html that descripts the license
        """
        phrase = _("All rights reserved")
        return "<span class='license-icon license-arr'></span><span class='license-text'>{phrase}</span>".format(
            phrase=phrase
        )


class CCLicense(License):
    """
    License class for a Creative Commons license
    """

    def __init__(self, license, version=None, *args, **kwargs):
        super(CCLicense, self).__init__(license, version, *args, **kwargs)
        # If no version was set during initialization, we may assume the most recent version of a CC license and fetch that using the API
        if self.license and not self.version:
            data = CCLicense.get_cc_api_data(self.license)
            license_img = data.find(".//a")
            self.version = license_img.get("href").split("/")[-2]

    @property
    def html(self):
        """
        Return a piece of html that describes the license
        """

        license_html = []
        if 'BY' in self.license:
            license_html.append("<span class='license-icon license-cc-by'></span>")
        if 'NC' in self.license:
            license_html.append("<span class='license-icon license-cc-nc'></span>")
        if 'SA' in self.license:
            license_html.append("<span class='license-icon license-cc-sa'></span>")
        if 'ND' in self.license:
            license_html.append("<span class='license-icon license-cc-nd'></span>")

        phrase = _("Some rights reserved")
        return "<a rel='license' href='http://creativecommons.org/licenses/{license_link}/{version}/' data-tooltip='{description}' target='_blank' class='license'>{license_html}<span class='license-text'>{phrase}</span></a>".format(
            description=self.description,
            version=self.version,
            license_link=self.license.lower()[3:],
            license_html=''.join(license_html),
            phrase=phrase
        )

    @property
    def description(self):
        """
        Return a text that describes the license
        """
        cc_attributes = []
        if 'BY' in self.license:
            cc_attributes.append(_("Attribution"))
        if 'NC' in self.license:
            cc_attributes.append(_("NonCommercial"))
        if 'SA' in self.license:
            cc_attributes.append(_("ShareAlike"))
        if 'ND' in self.license:
            cc_attributes.append(_("NonDerivatives"))

        return _("This work is licensed under a Creative Commons {attributes} {version} International License.").format(
            attributes='-'.join(cc_attributes),
            version=self.version
        )

    @staticmethod
    def cc_attributes_from_license(license):
        """
        Convert a license object to a tuple of values representing the relevant CC attributes

        The returning tuple contains a string and two boolean values which represent:
          - The license class, either 'zero' or 'standard'
          - Are commercial applications of the content allowed, 'yes', 'no' or 'only under the same license' (share alike)
          - Are derivatives of the content allowed, 'true' by default
        """
        commercial = "y"
        derivatives = "y"

        if license == "CC0":
            license_class = "zero"
        else:
            license_class = "standard"

            # Split the license attributes and remove the 'CC-' from the beginning of the string
            attrs = iter(license.split("-")[1:])

            # Then iterate over the remaining attributes that are set
            for attr in attrs:
                if attr == "SA":
                    derivatives = "sa"
                elif attr == "NC":
                    commercial = "n"
                elif attr == "ND":
                    derivatives = "n"

        return (license_class, commercial, derivatives)

    @staticmethod
    def get_cc_api_data(license):
        """
        Fetch data about a CC license using the API at creativecommons.org
        """
        (license_class, commercial, derivatives) = CCLicense.cc_attributes_from_license(license)

        # Format the url for the particular license
        url = "http://api.creativecommons.org/rest/1.5/license/{license_class}/get?commercial={commercial}&derivatives={derivatives}".format(
            license_class=license_class,
            commercial=commercial,
            derivatives=derivatives
        )

        # Fetch the license data
        xml_data = requests.get(url).content

        # Set up the response parser
        edx_xml_parser = etree.XMLParser(
            dtd_validation=False,
            load_dtd=False,
            remove_comments=True,
            remove_blank_text=True
        )

        # Parse the response file and extract the relevant data
        license_file = StringIO(xml_data.encode('ascii', 'ignore'))
        xml_obj = etree.parse(
            license_file,
            parser=edx_xml_parser
        ).getroot()
        data = xml_obj.find("html")

        return data


def parse_license(license, version=None):
    """
    Return a license object appropriate to the license

    This is a simple utility function to allowed for easy conversion between license strings and license objects. It
    accepts a license string and an optional license version and returns the corresponding license object. It also accounts
    for the license parameter already being a license object.
    """

    if license is None:
        return license
    elif license is "":
        return None
    elif isinstance(license, basestring):
        if license == "ARR":
            return ARRLicense(license, version)
        elif license.startswith("CC-BY") or license == "CC0":
            return CCLicense(license, version)
        else:
            raise ValueError('Invalid license.')
    elif isinstance(license, dict):
        return parse_license(license=license['license'], version=license['version'])
    elif isinstance(license, License):
        return license
    else:
        raise ValueError('Invalid license.')
