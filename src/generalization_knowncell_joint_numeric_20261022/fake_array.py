"""Small standard-library test double, never a numerical runtime substitute.

It deliberately uses math.fsum and simple Python loops. Passing tests here
checks deferred control flow and equations, not BLAS/SciPy/native parity.
"""
import math
from itertools import product


class DType:
    def __init__(self, kind): self.kind = kind


class Array:
    def __init__(self, data, dtype=None):
        if isinstance(data, Array): data = data.tolist()
        assert isinstance(data, (list, tuple))
        self.data = [list(row) for row in data] if data and isinstance(data[0], (list, tuple)) else list(data)
        self.shape = (len(data), len(data[0])) if data and isinstance(data[0], (list, tuple)) else (len(data),)
        self.ndim = len(self.shape)
        assert self.ndim == 1 or all(len(row) == self.shape[1] for row in self.data)
        values = self.flat()
        kind = 'f' if dtype == 'float64' or any(isinstance(v, float) for v in values) else ('b' if values and all(isinstance(v, bool) for v in values) else 'i')
        self.dtype = DType(kind)
        if dtype == 'float64': self.data = self._build(self.shape, lambda index: float(self.at(index)))

    def __len__(self): return self.shape[0]
    def flat(self): return [v for row in self.data for v in row] if self.ndim == 2 else list(self.data)
    def at(self, index): return self.data[index[0]][index[1]] if self.ndim == 2 else self.data[index[0]]
    @staticmethod
    def _build(shape, function):
        if len(shape) == 1: return [function((i,)) for i in range(shape[0])]
        return [[function((i, j)) for j in range(shape[1])] for i in range(shape[0])]
    def tolist(self): return [list(row) for row in self.data] if self.ndim == 2 else list(self.data)
    def all(self): return all(self.flat())
    def any(self): return any(self.flat())
    def copy(self): return Array(self)
    @property
    def T(self):
        assert self.ndim == 2
        return Array([[self.data[i][j] for i in range(self.shape[0])] for j in range(self.shape[1])])
    @staticmethod
    def indices(key, size):
        if isinstance(key, slice): return list(range(size))[key]
        if isinstance(key, Array):
            assert key.ndim == 1
            if key.dtype.kind == 'b':
                assert len(key) == size
                return [i for i, use in enumerate(key.data) if use]
            return key.data
        assert isinstance(key, int)
        return [key]
    def __getitem__(self, key):
        if isinstance(key, tuple):
            assert len(key) == 2
            if self.ndim == 1:
                assert key[1] is None
                return Array([[self.data[i]] for i in self.indices(key[0], len(self))])
            rows, columns = self.indices(key[0], len(self)), self.indices(key[1], self.shape[1])
            return Array([[self.data[i][j] for j in columns] for i in rows])
        indices = self.indices(key, len(self))
        if isinstance(key, int): return self.data[key]
        return Array([self.data[i] for i in indices])
    def __setitem__(self, key, value):
        assert self.ndim == 2 and isinstance(key, tuple) and not isinstance(value, Array)
        for i in self.indices(key[0], len(self)):
            for j in self.indices(key[1], self.shape[1]): self.data[i][j] = value
    @staticmethod
    def shape_for(*values):
        shapes = [value.shape if isinstance(value, Array) else () for value in values]
        width = max(map(len, shapes)); shapes = [(1,) * (width-len(shape)) + shape for shape in shapes]
        result = tuple(max(axis) for axis in zip(*shapes))
        assert all(all(a == 1 or a == b for a, b in zip(shape, result)) for shape in shapes)
        return result
    @staticmethod
    def broadcast(value, index, shape):
        if not isinstance(value, Array): return value
        local = index[len(shape)-value.ndim:]
        return value.at(tuple(0 if size == 1 else i for i, size in zip(local, value.shape)))
    @staticmethod
    def apply(function, *values):
        shape = Array.shape_for(*values)
        return Array(Array._build(shape, lambda index: function(*(Array.broadcast(v, index, shape) for v in values))))
    def __add__(self, other): return self.apply(lambda a, b: a+b, self, other)
    def __radd__(self, other): return self + other
    def __sub__(self, other): return self.apply(lambda a, b: a-b, self, other)
    def __rsub__(self, other): return self.apply(lambda a, b: a-b, other, self)
    def __mul__(self, other): return self.apply(lambda a, b: a*b, self, other)
    def __rmul__(self, other): return self * other
    def __truediv__(self, other): return self.apply(lambda a, b: a/b, self, other)
    def __pow__(self, other): return self.apply(lambda a, b: a**b, self, other)
    def __neg__(self): return self.apply(lambda a: -a, self)
    def __invert__(self): return self.apply(lambda a: not a, self)
    def __eq__(self, other): return self.apply(lambda a, b: a == b, self, other)
    def __ge__(self, other): return self.apply(lambda a, b: a >= b, self, other)
    def __matmul__(self, other):
        assert isinstance(other, Array) and other.ndim == 1
        if self.ndim == 1:
            assert self.shape == other.shape
            return math.fsum(a*b for a, b in zip(self.data, other.data))
        assert self.shape[1] == len(other)
        return Array([math.fsum(a*b for a, b in zip(row, other.data)) for row in self.data])


class FakeNP:
    float64 = 'float64'
    @staticmethod
    def array(value, dtype=None, order='C', copy=True):
        assert order == 'C' and copy is True
        return Array(value, dtype)
    @staticmethod
    def asarray(value): return value if isinstance(value, Array) else Array(value)
    @staticmethod
    def zeros(size, dtype='float64'):
        assert dtype == 'float64'
        return Array([0.] * size)
    @staticmethod
    def isfinite(value): return Array.apply(math.isfinite, value)
    @staticmethod
    def sqrt(value): return Array.apply(math.sqrt, value)
    @staticmethod
    def all(value): return value.all()
    @staticmethod
    def sum(value, axis):
        assert value.ndim == 2 and axis == 0
        return Array([math.fsum(row[j] for row in value.data) for j in range(value.shape[1])])
    @staticmethod
    def where(condition, yes, no): return Array.apply(lambda flag, a, b: a if flag else b, condition, yes, no)
    @staticmethod
    def concatenate(values):
        assert all(value.ndim == 1 for value in values)
        return Array([v for value in values for v in value.data])
    @staticmethod
    def logaddexp(left, right):
        return Array.apply(lambda a, b: max(a, b)+math.log1p(math.exp(-abs(a-b))), left, right)


def expit(value):
    def scalar(x):
        if x >= 0: return 1./(1.+math.exp(-x))
        y = math.exp(x); return y/(1.+y)
    return Array.apply(scalar, value)
