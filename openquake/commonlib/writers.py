# Copyright (c) 2010-2014, GEM Foundation.
#
# NRML is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# NRML is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with NRML.  If not, see <http://www.gnu.org/licenses/>.

import cStringIO
from xml.sax.saxutils import escape, quoteattr


def scientificformat(value, fmt='%13.9E'):
    """
    Convert a float into a string by using the scientific notation
    and a fixed precision (by default 10 decimal digits).
    If the value is not a float, convert it into a string.

    >>> scientificformat(-0.004)
    '-4.000000000E-03'
    >>> scientificformat(0.004)
    '4.000000000E-03'
    """
    if isinstance(value, float):
        return fmt % value
    return str(value)


class StreamingXMLWriter(object):
    """
    A stream-based XML writer. The typical usage is something like this::

        with StreamingXMLWriter(output_file) as writer:
            writer.start_tag('root')
            for node in nodegenerator():
                writer.serialize(node)
            writer.end_tag('root')
    """
    def __init__(self, stream, indent=4, encoding='utf-8', nsmap=None):
        """
        :param stream: the stream or a file where to write the XML
        :param int indent: the indentation to use in the XML (default 4 spaces)
        """
        self.stream = stream
        self.indent = indent
        self.encoding = encoding
        self.indentlevel = 0
        self.nsmap = nsmap

    def shorten(self, tag):
        """
        Get the short representation of a fully qualified tag

        :param str tag: a (fully qualified or not) XML tag
        """
        if tag.startswith('{'):
            ns, _tag = tag.rsplit('}')
            tag = self.nsmap.get(ns[1:], '') + _tag
        return tag

    def _write(self, text):
        """Write text by respecting the current indentlevel"""
        if not isinstance(text, str):
            text = text.encode(self.encoding, 'xmlcharrefreplace')
        spaces = ' ' * (self.indent * self.indentlevel)
        self.stream.write(spaces + text.strip() + '\n')

    def emptyElement(self, name, attrs):
        """Add an empty element (may have attributes)"""
        attr = ' '.join('%s=%s' % (n, quoteattr(scientificformat(v)))
                        for n, v in sorted(attrs.iteritems()))
        self._write('<%s %s/>' % (name, attr))

    def start_tag(self, name, attrs=None):
        """Open an XML tag"""
        if not attrs:
            self._write('<%s>' % name)
        else:
            self._write('<' + name)
            for (name, value) in sorted(attrs.items()):
                self._write(' %s=%s' % (name, quoteattr(scientificformat(value))))
            self._write('>')
        self.indentlevel += 1

    def end_tag(self, name):
        """Close an XML tag"""
        self.indentlevel -= 1
        self._write('</%s>' % name)

    def serialize(self, node):
        """Serialize a node object (typically an ElementTree object)"""
        if self.nsmap is not None:
            tag = self.shorten(node.tag)
        else:
            tag = node.tag
        if not node and not node.text:
            self.emptyElement(tag, node.attrib)
            return
        self.start_tag(tag, node.attrib)
        if node.text:
            self._write(escape(scientificformat(node.text).strip()))
        for subnode in node:
            self.serialize(subnode)
        self.end_tag(tag)

    def __enter__(self):
        """Write the XML declaration"""
        self._write('<?xml version="1.0" encoding="%s"?>\n' %
                    self.encoding)
        return self

    def __exit__(self, etype, exc, tb):
        """Close the XML document"""
        pass


def tostring(node, indent=4):
    """
    Convert a node into an XML string by using the StreamingXMLWriter.
    This is useful for testing purposes.

    :param node: a node object (typically an ElementTree object)
    :param indent: the indentation to use in the XML (default 4 spaces)
    """
    out = cStringIO.StringIO()
    writer = StreamingXMLWriter(out, indent)
    writer.serialize(node)
    return out.getvalue()