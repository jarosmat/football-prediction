from typing import Protocol, runtime_checkable

@runtime_checkable
class Stringable(Protocol):
    """
    Protocol for duck typing that requires the parameter to implement __str__ dunder method.
    """
    def __str__(self) -> str: ...