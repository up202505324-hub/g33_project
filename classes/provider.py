"""
Created on Fri Apr 24 16:20:32 2026

@author: Eduarda Venília Pinto Teixiera

"""

import datetime
from classes.gclass import Gclass

class Provider(Gclass):
    obj = dict()
    lst = list()
    pos = 0
    sortkey = ''
    att = ['_id', '_name', '_creation_date']
    header = 'Provider'
    des = ['Id', 'Name', 'Creation Date']
    def __init__(self, id, name, creation_date):
        super().__init__()
        id = Provider.get_id(id)
        self._id = id
        self._name = name
        self._creation_date = datetime.date.fromisoformat(str(creation_date))
        Provider.obj[id] = self
        Provider.lst.append(id)

    @property
    def id(self):
        return self._id

    @id.setter
    def id(self, id):
        self._id = id

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, name):
        self._name = name

    @property
    def creation_date(self):
        return self._creation_date

    @creation_date.setter
    def creation_date(self, creation_date):
        self._creation_date = datetime.date.fromisoformat(str(creation_date))
