class TupleHashMixin:
    def as_tuple(self):
        raise NotImplementedError("Subclasses must implement as_tuple()")

    def __eq__(self, other):
        if not isinstance(other, type(self)):
            return NotImplemented
        return self.as_tuple() == other.as_tuple()

    def __hash__(self):
        return hash(self.as_tuple())
