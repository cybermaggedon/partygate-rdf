
# Some common predicates

from rdflib import URIRef

LABEL=URIRef("http://www.w3.org/2000/01/rdf-schema#label")
DESCRIPTION=URIRef("http://pivotlabs.vc/challenges/p#description")
IS_A=URIRef("http://www.w3.org/1999/02/22-rdf-syntax-ns#type")
PROPERTY=URIRef("http://www.w3.org/2000/01/rdf-schema#Property")
CLASS=URIRef("http://www.w3.org/2000/01/rdf-schema#Class")
SEE_ALSO=URIRef("http://www.w3.org/2000/01/rdf-schema#seeAlso")
COMMENT=URIRef("http://www.w3.org/2000/01/rdf-schema#comment")
DOMAIN=URIRef("http://www.w3.org/2000/01/rdf-schema#domain")
RANGE=URIRef("http://www.w3.org/2000/01/rdf-schema#range")
LITERAL=URIRef("http://www.w3.org/2000/01/rdf-schema#Literal")
SUB_CLASS_OF=URIRef("http://www.w3.org/2000/01/rdf-schema#subClassOf")
EQUIVALENT_PROPERTY=URIRef("http://www.w3.org/2002/07/owl#equivalentProperty")
SUB_PROPERTY_OF=URIRef("http://www.w3.org/2000/01/rdf-schema#subPropertyOf")
EQUIVALENT_CLASS=URIRef("http://www.w3.org/2002/07/owl#equivalentClass")
