#! /bin/env python3

import sys
import getopt
import bgapi_parser
import argparse
import os

def get_default_xapi() :
    GSDK = os.environ.get('GSDK')
    if None == GSDK :
        return None
    return GSDK + '/protocol/bluetooth/api/sl_bt.xapi'

parser = argparse.ArgumentParser()
parser.add_argument('--xapi',default=get_default_xapi(),help='file describing API {GSDK}/protocol/bluetooth/api/sl_bt.xapi')
parser.add_argument('--debug',action='store_true',help='show generally uninteresting info')
parser.add_argument('--filter',help='restrict classes to containing this substring')
parser.add_argument('--basename',required=True,help='basename for source and header files')
args = parser.parse_args()

if args.debug :
    print('args:',args)

def debug(message) :
    if args.debug :
        print(message)


lc = bgapi_parser.BgapiParser(args.xapi)

#print(lc.classes)
keys = []
for key in lc.classes :
    keys.append(key)
keys.sort()
#print(keys)

def struct_name(name) :
    return 'struct '+name+'_s'

def base_datatype(datatype) :
    return lc.api['datatypes']['base'][datatype]

def length_datatype(datatype) :
    return lc.api['datatypes']['length'][datatype]

class Parameter :
    def __init__(self,origin,datatype,name,is_pointer=False,is_return=False) :
        self.origin = origin
        self.datatype = datatype
        self.name = name
        self.is_return = is_return
        self.is_pointer = is_pointer
    def decl_datatype(self) :
        index = self.datatype.find('int') 
        if index < 0 or index > 1 : 
            return self.datatype
        lenbits = len(self.datatype) - index - 3
        if lenbits > 2 or lenbits < 1 :
            return self.datatype
        try :
            bits = int(self.datatype[index+3:])
            return self.datatype+'_t'
        except ValueError:
            pass
        return self.datatype
    def decl_name(self) :
        if self.is_pointer :
            return '*'+self.name
        return self.name
    def call_name(self) :
        return self.name
    
def parameter_expansion(param,is_return=False) :
    name = param['name']
    datatype = param['datatype']
    basetype = base_datatype(datatype)
    if 'uint8array' == basetype or 'uint16array' == basetype :
        if  is_return :
            return [Parameter(datatype,'size_t','%s_max_len'%(name)),
                    Parameter(datatype,'size_t','%s_len'%(name),is_return=True,is_pointer=True),
                    Parameter(datatype, 'uint8_t',name,is_return=True,is_pointer=True)]
        else :
            return [Parameter(datatype,'size_t','%s_len'%(name)), Parameter(datatype, 'uint8_t',name,is_pointer=True)]
    if 'byte_array' == basetype :
        return [Parameter(basetype,'sl_bt_'+datatype+'_t',name,is_return=is_return,is_pointer=True)]
    return [Parameter(datatype,basetype,name,is_return=is_return)]

def gen_struct(name,params,returns) :
    text = struct_name(name)+' {\n'
    for param in params :
        for t in parameter_expansion(param) :
            text += '  '+t.decl_datatype()+' '+t.decl_name()+';\n'
    if None != returns :
        for param in returns :
            if 'result' == param['name'] : continue
            for t in parameter_expansion(param,is_return=True) :
                text += '  '+t.decl_datatype()+' '+t.decl_name()+';\n'
    return text + '};\n'

def gen_call(name,params,returns) :
    plist = []
    copy = ''
    for param in params :
        pe = parameter_expansion(param)
        plist += pe
        if 2 == len(pe) :
            lenname = pe[0].call_name()
            dataname = pe[1].call_name()
            copy += '  ptr->'+lenname+' = '+lenname+';\n'
            copy += '  assert((ptr->'+dataname+' = malloc('+lenname+')));\n'
            copy += '  memcpy(ptr->'+dataname+','+dataname+','+lenname+');\n'
        else :
            dataname = pe[0].call_name()
            copy += '  ptr->'+dataname+' = '+dataname+'; //\n'
    if len(plist) > 0 :
        copy = '\n'.join(['  ptr->%s = %s;'%(x.call_name(),x.call_name()) for x in plist])+'\n'
    else :
        copy = ''
    decls = [x.decl_datatype()+' '+x.decl_name() for x in plist]
    text =  'void push_'+name+'('+','.join(decls)+') {\n'
    text += '  struct command_s *cmd = push_command(%s);\n'%(name.upper())
    if len(copy) > 0 :
        text += '  %s *ptr = &cmd->%s;\n'%(struct_name(name),name)
    else :
        text += '  (void)cmd;\n'
    text += copy
    text += '};\n'
    return text

def gen_process(name,params,returns) :
    plist = []
    text = '  case %s :\n'%(name.upper())
    for param in params :
        plist += parameter_expansion(param)
    if None != returns :
        for param in returns :
            if 'result' == param['name'] : continue
            plist += parameter_expansion(param,is_return=True)
    s = 'ptr->%s.'%(name)
    plist = ['%sptr->%s.'%(['','&'][x.is_return and not x.is_pointer],name)+x.call_name() for x in plist]
    if None == returns :
        text +=  '    sl_bt_%s(%s);\n'%(name,', '.join(plist))
    else :
        text += '    sc = sl_bt_%s(%s);\n'%(name,', '.join(plist))
        text += '    ptr->result = sc;\n'
    text += '    break;\n'
    return text

enums = []
code = """
struct cmds_s {
  struct command_s *head, *tail;
} cmds = { .head= NULL, .tail = NULL };

struct command_s *push_command(enum CMD_TYPE type) {
  struct command_s *ptr;
  assert((ptr = malloc(sizeof(struct command_s))));
  if(cmds.tail) {
    cmds.tail->next = ptr;
    ptr->previous = cmds.tail;
    cmds.tail = ptr;
  } else {
    cmds.tail = ptr;
    cmds.head = ptr;
    ptr->previous = NULL;
    ptr->next = NULL;
  }
  ptr->type = type;
  return ptr;
}
"""
process_wrapper = """
void command_process(void) {
  sl_status_t sc;
  struct command_s *ptr = cmds.head;
  if(NULL == ptr) return;
  switch(ptr->type) {
%s  }
}
"""
process = ''
structs = ''
struct = 'struct command_s {\n  struct command_s *next, *previous;\n  enum CMD_TYPE type;\n  union {\n'
for key in keys :
    cls = lc.classes[key]['name']
    if None != args.filter and cls.find(args.filter) < 0 : continue
    db = lc.classes[key]['commands']
    for skey in db :
        name = cls+'_'+db[skey]['name']
        enums.append(name.upper())
        structs += gen_struct(name, db[skey]['params'], db[skey]['returns'])
        struct += '    '+struct_name(name)+' '+name+';\n'
        code += gen_call(name, db[skey]['params'], db[skey]['returns'])
        process += gen_process(name, db[skey]['params'], db[skey]['returns'])
struct += '  };\n  sl_status_t result;\n};\n'
fh = open('%s.h'%(args.basename ),'w')
fh.write('#include <sl_status.h>\n')
define = args.basename.upper().replace('-','_')
fh.write('#ifndef %s\n#define %s\n\n'%(define,define))
fh.write('enum CMD_TYPE { '+', '.join(enums) + ' };\n')
fh.write(structs)
fh.write(struct)
fh.write('\n#endif\n')
fh.close();
fh = open('%s.c'%(args.basename ),'w')
fh.write('#include <stdlib.h>\n')
fh.write('#include <string.h>\n')
fh.write('#include <assert.h>\n')
fh.write('#include <sl_bt_api.h>\n')
fh.write('#include "%s.h"\n'%(args.basename ))
fh.write(code)
fh.write(process_wrapper%(process))
fh.close()
