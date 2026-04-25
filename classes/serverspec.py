"""
Created on Thu Apr 23 13:28:07 2026

@author: Asus
"""
from classes.gclass import Gclass

class ServerSpec(Gclass):
    obj = dict()
    lst = list()
    pos = 0
    sortkey = ''
    att = ['_id', '_ram_gb', '_cpu_cores', '_operating_system', '_storage_gb']
    header = 'ServerSpec'
    des = ['Id', 'RAM (GB)', 'CPU Cores', 'Operating System', 'Storage (GB)']
    def __init__(self, id, ram_gb, cpu_cores, operating_system, storage_gb):
        super().__init__()
        id = ServerSpec.get_id(id)
        self._id = id
        self._ram_gb = int(ram_gb)
        self._cpu_cores = int(cpu_cores)
        self._operating_system = operating_system
        self._storage_gb = int(storage_gb)
        ServerSpec.obj[id] = self
        ServerSpec.lst.append(id)

    @property
    def id(self):
        return self._id

    @id.setter
    def id(self, id):
        self._id = id

    @property
    def ram_gb(self):
        return self._ram_gb

    @ram_gb.setter
    def ram_gb(self, ram_gb):
        self._ram_gb = int(ram_gb)

    @property
    def cpu_cores(self):
        return self._cpu_cores

    @cpu_cores.setter
    def cpu_cores(self, cpu_cores):
        self._cpu_cores = int(cpu_cores)

    @property
    def operating_system(self):
        return self._operating_system

    @operating_system.setter
    def operating_system(self, operating_system):
        self._operating_system = operating_system

    @property
    def storage_gb(self):
        return self._storage_gb

    @storage_gb.setter
    def storage_gb(self, storage_gb):
        self._storage_gb = int(storage_gb)
