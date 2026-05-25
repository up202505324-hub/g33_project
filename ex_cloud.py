"""
Created on Thu Apr  23 19:23:35 2026

@author: Rosa Helena Dias Coelho
"""

import datetime
 
from classes.provider import Provider
from classes.datacenter import Datacenter
from classes.serverspec import ServerSpec
from classes.server import Server
from classes.usagequota import UsageQuota
 
Provider.read('data/cloud.db')
Datacenter.read('data/cloud.db')
ServerSpec.read('data/cloud.db')
Server.read('data/cloud.db')
UsageQuota.read('data/cloud.db')
 
print('Choose a class to test:')
print('1 - Provider')
print('2 - Datacenter')
print('3 - ServerSpec')
print('4 - Server')
print('5 - UsageQuota')
choice = input('? ')
 
if choice == '1':
    test_class = Provider
    ob = '0;NewProvider;2024-01-01'
elif choice == '2':
    test_class = Datacenter
    ob = '0;NewDatacenter;category1'
elif choice == '3':
    test_class = ServerSpec
    ob = '0;64;8;Ubuntu 22.04;512'
elif choice == '4':
    test_class = Server
    ob = '0;extra_info;1;1'
elif choice == '5':
    test_class = UsageQuota
    ob = '0;1;1;2024-01-01;100.0'
else:
    print('Invalid choice')
    test_class = Provider
    ob = '0;NewProvider;2024-01-01'
 
op = ''
while op != 'q':
    print('')
    print('Choose one letter for select the option')
    print('---------------')
    print('l - list')
    print('b - beginning')
    print('n - next')
    print('p - previous')
    print('e - end')
    print('---------------')
    print('i - insert')
    print('m - modify')
    print('r - remove')
    print('---------------')
    print('s - sort by attribute')
    print('f - find by attribute')
    print('---------------')
    print('q - quit')
    print('---------------')
    p = test_class.current()
    print(f'\n{p}')
    op = input('? ')
 
    if op == 'b':
        test_class.first()
    elif op == 'n':
        test_class.nextrec()
    elif op == 'p':
        test_class.previous()
    elif op == 'e':
        test_class.last()
    elif op == 'i':
        p1 = None
        if len(test_class.lst) == 0:
            p = eval('test_class.from_string("' + ob + '")')
            p1 = p
        str_list = list(p.__dict__.keys())
        attrib = str_list[0]
        print('leave blank to auto-increment')
        id = input(f'{attrib[1:]} = ')
        if id == '':
            id = 0
        else:
            id = int(id)
        strarg = f'test_class({id}'
        fk = getattr(test_class, 'fk', {})
        valid = True
        for i in range(1, len(str_list)):
            attrib = str_list[i]
            atype = type(getattr(p, attrib))
            if atype == datetime.date or atype == str:
                value = input(f'{attrib[1:]} = ')
                strarg += f',"{value}"'
            else:
                value = atype(input(f'{attrib[1:]} = '))
                strarg += f',{value}'
            # validate foreign key immediately after this input
            if attrib in fk:
                ref_class = fk[attrib]
                if int(value) not in ref_class.lst:
                    print(f'Error: {ref_class.__name__} {int(value)} not found')
                    valid = False
                    break
        if valid:
            strarg += ')'
            if p1 is not None:
                test_class.remove(getattr(p, str_list[0]))
            try:
                pobj = eval(strarg, {'test_class': test_class})
                attrib = str_list[0]
                code = getattr(pobj, attrib)
                obj = test_class.current(code)
                test_class.insert(code)
            except ValueError as e:
                print(f'Error: {e}')
 
    elif op == 'm':
        str_list = list(p.__dict__.keys())
        attrib = str_list[0]
        id = input(f'Record {attrib[1:]} = ')
        if id != '':
            id = int(id)
            obj = test_class.current(id)
            print('Leave blank or new value to modify')
            fk = getattr(test_class, 'fk', {})
            valid = True
            for attrib in str_list[1:]:
                value = input(f'{attrib[1:]} = ')
                if value != '':
                    atype = type(getattr(p, attrib))
                    if attrib in fk:
                        ref_class = fk[attrib]
                        if int(value) not in ref_class.lst:
                            print(f'Error: {ref_class.__name__} {int(value)} not found')
                            valid = False
                            break
                    try:
                        if atype == datetime.date:
                            setattr(obj, attrib, datetime.date.fromisoformat(value))
                        else:
                            setattr(obj, attrib, atype(value))
                    except ValueError as e:
                        print(f'Error: {e}')
            if valid:
                test_class.update(id)
 
    elif op == 'r':
        str_list = list(p.__dict__.keys())
        attrib = str_list[0]
        atype = type(getattr(p, attrib))
        cod = atype(input(f'{attrib[1:]} = '))
        if cod in test_class.lst:
            print(test_class.obj[cod])
            print('Confirm that you want to delete the record (y/n)?', end='')
            if input().upper() == 'Y':
                test_class.remove(cod)
 
    elif op == 'l':
        for code in test_class.lst:
            print(test_class.obj[code])
 
    elif op == 's':
        attrib = input('sort by attribute name: ')
        if '_' + attrib in list(p.__dict__.keys()):
            reverse = False
            if input('Reverse (False): '):
                reverse = True
            codep = p.id
            test_class.sort(attrib, reverse)
            for code in test_class.lst:
                print(test_class.obj[code])
            test_class.current(codep)
 
    elif op == 'f':
        attrib = input('Attribute name: ')
        if '_' + attrib in list(p.__dict__.keys()):
            atype = type(getattr(p, attrib))
            value = atype(input('Value: '))
            fobjs = test_class.find(value, attrib)
            if len(fobjs) > 0:
                test_class.current(fobjs[0].id)
                for obj in fobjs:
                    print(obj)
