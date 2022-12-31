
#
# Curator class, handles schema loading invocation of the data processing on
# each directory, and returns a graph.
#

import os
import json
import logging
from rdflib.term import Literal

from . csv import *
from . turtle import *
from . module import *
from . schema import *

# This is the list of processors currently supported.  To add a new processing
# type create a class and add it to this dict.
processors = {
    "csv": Csv,
    "turtle": Turtle,
    "module": Module,
}

# Curator class
class Curator:

    # Init, empty schema
    def __init__(self):
        self.schema = None

    # Loads the schema, Turtle format
    def load_schema(self, path):
        self.schema = Schema.load(path)

    # Processes a subdirectory
    def process(self, subdir):

        logging.info("Processing " + subdir + "...")
        metadata = json.load(open(subdir + "/metadata.json"))

        for field in [
                "id", "processing", "catalogue"
        ]:
            if field not in metadata:
                raise MetadataError(
                    subdir, f"The '{field}' field does not exist"
                )

        if metadata["processing"] not in processors:
            msg = f"Processing type '{metadata['processing']}' not known."
            raise MetadataError(subdir, msg)
   
        cls = processors[metadata["processing"]]

        g = cls.load(subdir, metadata, self.schema)

        cg = Graph()
        file = subdir + "/" + metadata["catalogue"]
        logging.info(f"Loading catalog {file}...")
        cg.parse(file, format="turtle")

        for t in cg:
            g.graph.add(t)

        return g
        
        
    def sub_class(self, cls, par, graph, schema):

        if cls == par:
            return True

        for (s, p, o) in graph.triples((cls, SUB_CLASS_OF, None)):
            if self.sub_class(o, par, graph, schema):
                return True

        for (s, p, o) in schema.triples((cls, SUB_CLASS_OF, None)):
            if self.sub_class(o, par, graph, schema):
                return True

        return False

    def is_type(self, val, cls, graph, schema):

        if type(val) == Literal:
            if cls == LITERAL:
                return True
            if cls == URIRef("http://www.w3.org/2001/XMLSchema#date"):
                return True

        for (s, p, o) in graph.triples((val, IS_A, cls)):
            return True

        for (s, p, o) in schema.triples((val, IS_A, cls)):
            return True

        for (s, p, o) in graph.triples((val, IS_A, None)):
            if self.sub_class(o, cls, graph, schema):
                return True

        for (s, p, o) in schema.triples((val, IS_A, None)):
            if self.sub_class(o, cls, graph, schema):
                return True

        return False

    def check_type(self, val, allowed, graph, schema):

        for a in allowed:
            if self.is_type(val, a, graph, schema):
                return

        logging.error("Value not allowed %s" % val)
        logging.error("Does not match %s" % allowed)
        raise RuntimeError("Value %s not allowed" % val)
    
    def validate(self, graph):

        schema = self.schema

        for (s, p, o) in graph:

            if p in schema.properties:

                if p in schema.ranges:
                    try:
#                    logging.info("%s %s %s" % (s, p, o))
                        self.check_type(
                            o, schema.ranges[p], graph, schema.graph
                        )
                    except Exception as e:
                        logging.error(
                            "Validation range check for predicate " + str(p)
                        )
                        raise e


                if p in schema.domains:
#                    logging.info("%s %s %s" % (s, p, o))
                    try:
                        self.check_type(
                            s, schema.domains[p], graph, schema.graph
                        )
                    except Exception as e:
                        logging.error(
                            "Validation domain check for predicate " + str(p)
                        )
                        raise e

                continue
            
            if p in schema.classes:
                continue

            logging.error("Predicate not known: " + str(p))

            raise PredicateNotKnown(p, "Not known: " + str(p))
        
    # Walks a directory searching for sub-directories with metadata.json
    # files
    def walk(self, dir):

        g = Graph()

        # Add the schema to our output graph
        for tpl in self.schema.graph:
            g.add(tpl)

        for subdir, dirs, files in os.walk(dir):

            # Any sub-directory with a metadata.json file is processed
            ix_path = subdir + "/metadata.json"

            # Ignore directories with no metadata.json
            if not os.path.exists(ix_path):
                continue

            # Invoke processing
            sg = self.process(subdir)

            # Add the sub-graph to the conglomerate graph
            for tpl in sg.graph:
                g.add(tpl)

        logging.info("Processing done")

        # Validate against schema
        logging.info("Validating...")
        self.validate(g)
        logging.info("Validated successfully")

        return g

