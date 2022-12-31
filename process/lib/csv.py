
# Handle CSV input

from rdflib import Graph
import csv
import hashlib

from . exceptions import *

def hash(x):
    return hashlib.md5(x.encode('utf-8')).hexdigest()[:16]

class Row:
    def __init__(self, row, fields):
        self.row = row
        self.fields = fields
    def get(self, id):
        if id not in self.fields:
            raise RuntimeError("No such field " + id)
        return self.row[self.fields[id]]

class Table:

    def __init__(self, path, fields=None, use_header=False, skip=0, limit=None):

        f = open(path)
        self.table = csv.reader(f)

        self.line = 0

        if use_header:
            flds = next(self.table)
            self.line += 1
        else:
            flds = fields
        fmap = {}

        for i in range(0, len(flds)):
            fmap[flds[i]] = i

        self.fields = fmap

        # Limit is compared to line numbers, so include the skip in the limit
        if limit:
            self.limit = limit + skip
        else:
            self.limit = None

        for i in range(0, skip):
            self.line += 1
            row = next(self.table)

    def __next__(self):

        if self.limit and self.line > self.limit:
            raise StopIteration

        row = next(self.table)

        self.line += 1

        if len(row) != len(self.fields):
            raise LineProcessingError(
                path, self.line,
                f"CSV row has {len(row)} cells, mismatches the field list"
            )

        return Row(row, self.fields)

    def __iter__(self):
        return self

class LiteralValue:
    def __init__(self, subdir, props, schema):

        self.schema = schema

        if "ignore" in props:
            self.ignore = set(props["ignore"])
        else:
            self.ignore = set()

        self.pred = schema.map(props["predicate"])
        self.field = props["field"]

        if "map" in props:
            self.mapping = props["map"]
        else:
            self.mapping = None

        if "datatype" in props:
            self.datatype = props["datatype"]
        else:
            self.datatype = None

    def handle(self, row, parent=None):

        if parent == None: return []

        value = row.get(self.field)
        raw = value

        if value in self.ignore: return []

        if self.mapping:
            if value not in self.mapping:
                return []
            else:
                value = self.mapping[value]

        if self.datatype:
            obj = self.schema.map(value, self.datatype)
        else:
            obj = self.schema.map(value)

        return [(parent, self.pred, obj)]

class HashId:
    def __init__(self, fields, pfx=None, ignore=None):
        self.prefix = pfx
        self.fields = fields
        self.ignore = ignore

    def handle(self, row):

        value = "///".join([
            row.get(fld)
            for fld in self.fields
        ])

        if self.ignore and value in self.ignore:
            return None

        value = hash(value)
        if self.prefix:
            return self.prefix + value
        else:
            return value

class DeriveId:
    def __init__(self, fields, pfx, ignore=None):
        self.prefix = pfx
        self.fields = fields
        self.ignore = ignore
        
    def handle(self, row):
        value = "//".join([
            row.get(fld)
            for fld in self.fields
        ])

        if self.ignore and value in self.ignore:
            return None

        value = value.replace(" ", "-")
        value = value.lower()
        value = self.prefix + value
        return value

class CopyId:
    def __init__(self, fieldsx, ignore=None):

        if len(fields) != 1:
            raise MetadataError("With 'copy' there must be exactly 1 field")
        self.fields = fields

    def handle(self, row):
        value = row.get(self.fields[0])
        if self.ignore and value in self.ignore: return None
        return value

class MapId:
    def __init__(self, fields, mapping, ignore=None):
        if len(fields) != 1:
            raise MetadataError("With 'copy' there must be exactly 1 field")
        self.fields = fields
        self.mapping = mapping
        self.ignore = ignore
    def handle(self, row):
        value = row.get(self.fields[0])
        if self.ignore and value in self.ignore: return None
        if value in self.mapping: return self.mapping[value]
        return None

class ObjectValue:
    def __init__(self, subdir, props, schema):

        self.schema = schema

        if "class" not in props:
            raise MetadataError(
                subdir, "The 'class' field does not exist"
            )

        if "properties" not in props:
            raise MetadataError(
                subdir, "The 'properties' field does not exist"
            )

        if "id-prefix" in props:
            id_prefix = props["id-prefix"]
        else:
            id_prefix = None

        if "ignore" in props:
            ignore = set(props["ignore"])
        else:
            ignore = set()

        if "predicate" in props:
            self.predicate = schema.map(props["predicate"])
        else:
            self.predicate = None

        if "with-id" not in props:
            raise MetadataError(
                subdir, "The 'with-id' field does not exist"
            )

        if "id-fields" not in props:
            raise MetadataError(
                subdir, "The 'id-fields' field does not exist"
            )

        id_fields = props["id-fields"]

        if props["with-id"] == "hash":
            self.derive_id = HashId(props["id-fields"], id_prefix, ignore)
        elif props["with-id"] == "derive":
            self.derive_id = DeriveId(props["id-fields"], id_prefix, ignore)
        elif props["with-id"] == "copy":
            self.derive_id = CopyId(props["id-fields"], ignore)
        elif props["with-id"] == "map":
            self.derive_id = MapId(props["id-fields"], props["map"], ignore)
        else:
            raise MetadataError(
                subdir, "Don't know with-id: '%s'" % props["with-id"]
            )

        self.cls = schema.map(props["class"])

        self.properties = []

        for prop in props["properties"]:
            if "class" in prop:
                self.properties.append(ObjectValue(subdir, prop, schema))
            else:
                self.properties.append(LiteralValue(subdir, prop, schema))

    def handle(self, row, parent=None):

        identity = self.derive_id.handle(row)

        if identity == None:

            tpls = []

            for prop in self.properties:
                if type(prop) == LiteralValue: continue
                tpls.extend(prop.handle(row, None))

            return tpls

        identity = self.schema.map(identity)

        tpls = [
            (identity, self.schema.map("rdf:type"), self.cls)
        ]

        for prop in self.properties:
            tpls.extend(prop.handle(row, identity))

        if parent and self.predicate:
            tpls.append((parent, self.predicate, identity))

        return tpls

class Csv:

    @staticmethod
    def load(subdir, metadata, schema):

        g = Graph()

        if "input" not in metadata:
            raise MetadataError(subdir, "The 'input' field does not exist")

        if "fields-from-header" in metadata and metadata["fields-from-header"]:
            from_header = True
        else:
            from_header = False

        if not from_header:
            if "fields" not in metadata:
                raise MetadataError(subdir, "The 'fields' field does not exist")
            fields = metadata["fields"]
        else:
            fields = None

        if "skip" in metadata:
            skip = int(metadata["skip"])
        else:
            skip = 0

        if "limit" in metadata:
            limit = int(metadata["limit"])
        else:
            limit = None

        tbl = Table(
            subdir + "/" + metadata["input"], fields=fields,
            use_header=from_header, skip=skip, limit=limit
        )
        
        if "objects" not in metadata:
            raise MetadataError(subdir, "The 'objects' field does not exist")

        objects = [
            ObjectValue(subdir, obj, schema)
            for obj in metadata["objects"]
        ]

        for row in tbl:

            for obj in objects:
                tpls = obj.handle(row)
                for tpl in tpls:
                    g.add(tpl)

        c = Csv()
        c.graph = g
        return c

