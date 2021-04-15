"""This module implements some machine processing utils specific to H2."""


from typing import Callable, List, Set


from waad.utils.asset import Machine


class MachinesProcessing:
    """This class implements a machines processing block. It is very specific to H2.

    Attributes:
        workstationname (Set[str]): All distinct elements in the `workstationname` column of the dataset.
        host (Set[str]): All distinct elements in the `host` column of the dataset.
        workstationname_machine_maker (Callable): Function to build a `Machine` object from a workstationname.
        host_machine_maker (Callable): Function to build a `Machine` object from a host.
    """

    def __init__(
        self, 
        workstationname: Set[str], 
        host: Set[str], 
        workstationname_machine_maker: Callable = lambda w: Machine(w) if w != '?' else None,
        host_machine_maker: Callable = lambda h: Machine(name=h.split(".")[0], domain=h.split(".")[1])
    ):
        self._input_workstationnames = workstationname
        self._input_hosts = host
        self._workstationname_machine_maker = workstationname_machine_maker
        self._host_machine_maker = host_machine_maker

        self.workstations: Set[Machine] = set()
        self.hosts: Set[Machine] = set()

    def run(self):
        # workstations part
        for wkname in self._input_workstationnames:
            try:
                m = self._workstationname_machine_maker(wkname)
                if m is not None:
                    self.workstations.add(m)
            except Exception:
                pass  

        # host part
        for host in self._input_hosts:
            try:
                m = self._host_machine_maker(host)
                if m is not None:
                    self.hosts.add(m)
            except Exception:
                pass
