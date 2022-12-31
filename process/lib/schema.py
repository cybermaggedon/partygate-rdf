
# Loads schema and maintains sets of properties and classes

from rdflib import Literal, URIRef, Graph
import json
import os
import logging

from . defs import *

class Schema:

    def __init__(self):
       self.properties = {}
       self.classes = {}

       self.domains = {}
       self.ranges = {}

    @staticmethod
    def load(path):

        s = Schema()

        g = Graph()

        # Walk subdirectory, load anything with a .ttl suffix
        for subdir, dirs, files in os.walk(path):
            for f in files:
                if f.endswith(".ttl"):
                    file = subdir + "/" + f
                    logging.info(f"Loading {file}...")
                    g.parse(file, format="turtle")

        s.graph = g
        s.namespaces = json.load(open(path + "/namespaces.json"))

        for tpl in g:
            if len(tpl) != 3:
                raise RuntimeError("Schema parsing unexpected triple failure")

            if tpl[1] == DESCRIPTION:
                pass
            if tpl[1] == LABEL:
                pass
            if tpl[1] == IS_A:
                if tpl[2] == PROPERTY:
                    s.properties[tpl[0]] = True
                if tpl[2] == CLASS:
                    s.classes[tpl[0]] = True

            if tpl[1] == DOMAIN:
                if tpl[0] not in s.domains: s.domains[tpl[0]] = []
                s.domains[tpl[0]].append(tpl[2])

            if tpl[1] == RANGE:
                if tpl[0] not in s.ranges: s.ranges[tpl[0]] = []
                s.ranges[tpl[0]].append(tpl[2])

        # Boot-strap a set of fundamental predicates
        s.properties[LABEL] = True
        s.properties[IS_A] = True
        s.properties[SEE_ALSO] = True
        s.properties[COMMENT] = True
        s.properties[DOMAIN] = True
        s.properties[RANGE] = True
        s.properties[SUB_CLASS_OF] = True
        s.properties[EQUIVALENT_PROPERTY] = True
        s.properties[SUB_PROPERTY_OF] = True
        s.properties[EQUIVALENT_CLASS] = True

        return s

    # Prefix mapping
    def map_ns(self, str):
        if str.startswith("http://"): return str
        if str.startswith("https://"): return str
        ix = str.find(":")
        if ix < 0: return str
        ns = str[0:ix]
        if ns not in self.namespaces: return str
        return self.namespaces[ns] + str[ix + 1:]

    # Map prefix, if it exists and return either URIRef or Literal
    def map(self, str, tp=None):
        str = self.map_ns(str)
        if str.startswith("http:"):
            return URIRef(str)
        if str.startswith("https:"):
            return URIRef(str)

        if tp:
            tp = self.map_ns(tp)
            return Literal(str, datatype=tp)
        return Literal(str)

