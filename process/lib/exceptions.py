# Various exceptions used to capture processing errors

class MetadataError(Exception):
   def __init__(self, dir, msg):
      self.dir = dir
      super().__init__(msg)

class FileProcessingError(Exception):
   def __init__(self, file, msg):
      self.file = file
      super().__init__(msg)

class LineProcessingError(Exception):
   def __init__(self, file, line, msg):
      self.file = file
      self.line = line
      super().__init__(msg)

class PredicateNotKnown(Exception):
   def __init__(self, predicate, msg):
      self.predicate = predicate
      super().__init__(msg)
