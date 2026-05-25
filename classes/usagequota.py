"""
Created on Thu Apr  16 18:49:12 2026

@author: gabri
"""

import datetime
from classes.provider import Provider
from classes.datacenter import Datacenter
from classes.gclass import Gclass
 
class UsageQuota(Gclass):
    obj = dict()
    lst = list()
    pos = 0
    sortkey = ''
    att = ['_id', '_provider_id', '_datacenter_id', '_usage_date', '_cost']
    header = 'UsageQuota'
    des = ['Id', 'Provider Id', 'Datacenter Id', 'Usage Date', 'Cost']
 
    fk = {'_provider_id': Provider, '_datacenter_id': Datacenter}
 
    def __init__(self, id, provider_id, datacenter_id, usage_date, cost):
        super().__init__()
        provider_id = int(provider_id)
        datacenter_id = int(datacenter_id)
        if provider_id not in Provider.lst:
            raise ValueError(f'Provider {provider_id} not found')
        if datacenter_id not in Datacenter.lst:
            raise ValueError(f'Datacenter {datacenter_id} not found')
 
        id = UsageQuota.get_id(id)
        self._id = id
        self._provider_id = provider_id
        self._datacenter_id = datacenter_id
        self._usage_date = datetime.date.fromisoformat(str(usage_date))
        self._cost = float(cost)
        UsageQuota.obj[id] = self
        UsageQuota.lst.append(id)
 
    @property
    def id(self):
        return self._id
    @id.setter
    def id(self, id):
        self._id = id
 
    @property
    def provider_id(self):
        return self._provider_id
    @provider_id.setter
    def provider_id(self, provider_id):
        if provider_id in Provider.lst:
            self._provider_id = provider_id
        else:
            raise ValueError(f'Provider {provider_id} not found')
 
    @property
    def datacenter_id(self):
        return self._datacenter_id
    @datacenter_id.setter
    def datacenter_id(self, datacenter_id):
        if datacenter_id in Datacenter.lst:
            self._datacenter_id = datacenter_id
        else:
            raise ValueError(f'Datacenter {datacenter_id} not found')
 
    @property
    def usage_date(self):
        return self._usage_date
    @usage_date.setter
    def usage_date(self, usage_date):
        self._usage_date = datetime.date.fromisoformat(str(usage_date))
 
    @property
    def cost(self):
        return self._cost
    @cost.setter
    def cost(self, cost):
        self._cost = float(cost)
