#! /bin/env python3

import xml.etree.ElementTree as ET
import sys

class BgapiParser :
    def __init__(self, xapi) :
        tree = ET.parse(xapi)
        root = tree.getroot()
        if 'api' != root.tag :
            raise RuntimeError("root.tag: %s"%(root.tag))
        self.device_id = int(root.attrib['device_id'])
        found = False
        for device_id in [0,4,5] :
            if device_id == self.device_id :
                found = True
                break
        if not found :
            raise RuntimeError("root.attrib['device_id']: %s"%(root.attrib['device_id']))
        self.device_name = root.attrib['device_name']
        found = False
        for name in [ "dumo", "ble", "gecko", "bt", "btmesh" ] :
            if name == self.device_name :
                found = True
                break
        if not found :
            raise RuntimeError("Unknown device  name: %s"%(self.device_name))
        self.api = { 'device_name':self.device_name, 'classes':[] }

        for first in root :
            if 'class' == first.tag :
                if 'mesh_' == first.attrib['name'][:5] : continue
                if 'proxy_' == first.attrib['name'][:6] : continue
                if 'cte' == first.attrib['name'][:3] : continue
                if 'qualtester' == first.attrib['name'][:10] : continue
                self.api['classes'].append(self.unpack_class(first))
            elif 'datatypes' == first.tag : continue
            else :
                raise RuntimeError('Unhandled first.tag: %s'%(first.tag))
        print(self.api['classes'])
        self.classes = {}
        for c in self.api['classes'] :
            ci = int(c['index'])
            ed = {}
            md = {}
            for e in c['events'] :
                ei = int(e['index'])
                ed[ei] = { 'name':e['name'],'params':e['params'] }
            self.classes[ci] = { 'name':c['name'], 'events':ed }
            for m in c['commands'] :
                mi = int(m['index'])
                md[mi] = { 'name':m['name'],'params':m['params'],'returns':m.get('returns') }
            self.classes[ci]['commands'] = md

    def unpack_class(self, class_tree) :
        print(class_tree)
        contents = { 'name': class_tree.attrib['name'], 'commands':[], 'events':[], 'enums':[], 'defines':[], 'index':class_tree.attrib['index'] }
        for second in class_tree :
            if 'event' == second.tag :
                contents['events'].append(self.unpack_event(second))
            elif 'command' == second.tag :
                if second.attrib['name'] == 'debug_command' : continue
                if second.attrib['name'] == 'debug_counter' : continue
                if second.attrib['name'] == 'find_primary_service' : continue
                contents['commands'].append(self.unpack_command(second))
            elif 'enums' == second.tag :
                contents['enums'].append(self.unpack_enum(second))
            elif 'defines' == second.tag :
                contents['defines'].append(self.unpack_define(second))
            else :
                print('unpack_class::Unhandled second.tag: %s'%(second.tag))
        return contents
    def unpack_command(self, command_tree) :
        contents = { 'name': command_tree.attrib['name'], 'index':command_tree.attrib['index'] }
        for third in command_tree :
            if 'params' == third.tag :
                if None != contents.get('params') :
                    raise RuntimeError("Multiple params")
                contents['params'] = self.unpack_params(third)
            elif 'returns' == third.tag :
                if None != contents.get('returns') :
                    raise RuntimeError("Multiple returns")
                contents['returns'] = self.unpack_params(third)
            else :
                print('unpack_event::Unhandled third.tag: %s'%(third.tag))
        return contents
    def unpack_params(self, params_tree) :
        contents = []
        for p in params_tree :
            if 'param' == p.tag :
                contents.append({ 'name':p.attrib['name'], 'datatype':p.attrib['datatype'], 'type':p.attrib['type'] })
            else :
                print('unpack_params::Unhandled param.tag: %s'%(p.tag))
        return contents
    def unpack_event(self,event_tree) :
        contents = { 'name': event_tree.attrib['name'], 'index':event_tree.attrib['index'] }
        for third in event_tree :
            if 'params' == third.tag :
                if None != contents.get('params') :
                    raise RuntimeError("Multiple params")
                contents['params'] = self.unpack_params(third)
            else :
                print('unpack_event::Unhandled third.tag: %s'%(third.tag))
        return contents
    def unpack_enum(self, enum_tree) :
        contents = { 'name': enum_tree.attrib['name'], 'values':{} }
        for third in enum_tree :
            if 'enum' == third.tag :
                contents['values'][third.attrib['name']] = third.attrib['value']
            else :
                print('unpack_enum::Unhandled third.tag: %s'%(third.tag))
        return contents
    def unpack_define(self, define_tree) :
        contents = { 'name': define_tree.attrib['name'], 'values':{} }
        for third in define_tree :
            if 'define' == third.tag :
                contents['values'][third.attrib['name']] = third.attrib['value']
            else :
                print('unpack_define::Unhandled third.tag: %s'%(third.tag))
        return contents





#x = BgapiParser(sys.argv[1])
