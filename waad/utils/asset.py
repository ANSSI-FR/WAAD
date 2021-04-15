"""This module implements the `Asset` objects and related."""

from abc import ABC, abstractmethod
from typing import Any, Optional


class Asset(ABC):
    """This class defines a `Asset` and is abstract."""

    @abstractmethod
    def to_tuple(self):
        pass

    @abstractmethod
    def __eq__(self, obj: Any):
        pass

    @abstractmethod
    def __hash__(self):
        pass

    @abstractmethod
    def __repr__(self):
        pass


class Machine(Asset):
    """This class defines a `Machine` object as a tuple (name, domain), child of `Asset`."""

    def __init__(self, name: Optional[str] = None, domain: Optional[str] = None):
        self.name = name
        self.domain = domain

    def to_tuple(self):
        return (self.name, self.domain)

    def __eq__(self, obj: Any):
        return isinstance(obj, Machine) and obj.name == self.name and obj.domain == self.domain

    def __hash__(self):
        return hash((self.name, self.domain))

    def __repr__(self):
        return f"{self.name} - {self.domain}"


class Account(Asset):
    """This class defines an `Account` object as a tuple (name, domain, sid), child of `Asset`."""

    def __init__(self, name: Optional[str] = None, domain: Optional[str] = None, sid: Optional[str] = None):
        self.name = name
        self.domain = domain
        self.sid = sid

    def to_tuple(self):
        return (self.name, self.domain, self.sid)

    def __eq__(self, obj: Any):
        return isinstance(obj, Account) and obj.name == self.name and obj.domain == self.domain and obj.sid == self.sid

    def __hash__(self):
        return hash((self.name, self.domain, self.sid))

    def __repr__(self):
        if self.sid is not None:
            return f"{self.name} - {self.domain} - {self.sid}"
        return f"{self.name} - {self.domain}"


class IP(Asset):
    """This class defines an `IP` object as a child of `Asset`."""

    def __init__(self, address: str):
        self.address = address

    def to_tuple(self):
        return (self.address,)

    def __eq__(self, obj: Any):
        return isinstance(obj, IP) and obj.address == self.address

    def __hash__(self):
        return hash(self.address)

    def __repr__(self):
        return self.address
