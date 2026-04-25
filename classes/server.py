"""
Created on Wed Apr 22 18:29:51 2026

@author: Rosa Helena Dias Coelho

"""

from classes.provider import Provider
from classes.serverspec import ServerSpec
from classes.gclass import Gclass

class Server(Gclass):
    obj = dict()
    lst = list()
    pos = 0
    sortkey = ''
   
    att = ['_id', '_extra_info', '_provider_id', '_spec_id']
    
    header = 'Server'
   
    des = ['Id', 'Extra Info', 'Provider Id', 'Spec Id']
    
    def __init__(self, id, extra_info, provider_id, spec_id):
        super().__init__()
        
        provider_id = int(provider_id)
        spec_id = int(spec_id)
        if provider_id in Provider.lst:
            if spec_id in ServerSpec.lst:
                id = Server.get_id(id)
                self._id = id
                self._extra_info = extra_info
                self._provider_id = provider_id
                self._spec_id = spec_id
                
                Server.obj[id] = self
              
                Server.lst.append(id)
            else:
                print('ServerSpec', spec_id, 'not found')
        else:
            print('Provider', provider_id, 'not found')

   
    @property
    def id(self):
        return self._id

    @id.setter
    def id(self, id):
        self._id = id


    @property
    def extra_info(self):
        return self._extra_info

    @extra_info.setter
    def extra_info(self, extra_info):
        self._extra_info = extra_info

    
    @property
    def provider_id(self):
        return self._provider_id

    @provider_id.setter
    def provider_id(self, provider_id):
        if provider_id in Provider.lst:
            self._provider_id = provider_id
        else:
            print('Provider', provider_id, 'not found')

    
    @property
    def spec_id(self):
        return self._spec_id

    @spec_id.setter
    def spec_id(self, spec_id):
        if spec_id in ServerSpec.lst:
            self._spec_id = spec_id
        else:
            print('ServerSpec', spec_id, 'not found')
