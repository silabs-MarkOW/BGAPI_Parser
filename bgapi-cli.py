#! /bin/env python3

import sys
import getopt
import bgapi_parser

def usage(error=None) :
    if None != error :
        print('Error: %s'%(error))
    print('Usage: %s --xapi <xapi-xml-file> [ -c ][ -r ][ -e ][ --octal ][ --decimal ][ --hex ]'%(sys.argv[0]))
    quit()

debug = False
longopts = ['xapi=','octal','decimal','hex']
options = {'mode':"events",'params':'params','radix':16}
opts,params = getopt.getopt(sys.argv[1:],"dhcer",longopts)
for opt in opts :
    if '-h' == opt[0] :
        usage()
for opt,param in opts :
    print(opt)
    if '-h' == opt :
        continue
    elif '--xapi' == opt :
        options['xapi'] = param
    elif '-c' == opt :
        options['mode'] = 'commands'
        options['params'] = 'params'
    elif '-r' == opt :
        options['mode'] = 'commands'
        options['params'] = 'returns'
    elif '-e' == opt :
        options['mode'] = 'events'
    elif '-d' == opt :
        debug = True
    else :
        print('Unexpected option: "%s"'%(opt))

data = []
if debug : print('params: %s'%(params.__str__()))
if 0 == len(params) :
    usage('missing data to parse')
elif 1 == len(params) :
    token = params[0] 
    if len(token) & 1 :
        usage('If data in single token, length must be even')
    for i in range(len(token)>>1) :
        data.append(int(token[i<<1:][:2],16))
else :
    for param in params :
        if len(param) > 2 and '0x' == param[:2].lower() :
            data.append(int(param[2:],16))
        else :
            data.append(int(param,options['radix']))
if debug : print('data: %s'%(data.__str__()))        

lc = bgapi_parser.BgapiParser(options['xapi'])

#print(lc.classes)
keys = []
for key in lc.classes :
    keys.append(key)
keys.sort()
#print(keys)

def get_length(t,d) :
    length1 = ['uint8','int8']
    length2 = ['uint16','int16']
    length4 = ['uint32']
    for t1 in length1 :
        if t1 == t : return 1
    for t2 in length2 :
        if t2 == t : return 2
    for t4 in length4 :
        if t4 == t : return 4
    if 'uint8array' == t : return 1+d[0]
    raise RuntimeError(t)

def render(t,d,s) :
    if 'uint8' == t : return '0x%02x'%(d[0])
    elif 'uint16' == t : return '0x%02x%02x'%(d[1],d[0])
    elif 'errorcode' == t : return '0x%02x%02x'%(d[1],d[0])
    elif 'uint32' == t :
        s = '0x'
        for i in range(4) :
            s += '%02x'%(d[3-i])
        return s
    elif 'int16' == t :
        value = 0
        for i in range(2) :
            value += d[i] << (i << 3)
        sign = 1 << 15
        if value & sign :
            value -= sign
        return '%+d'%value
    elif 'uint8array' == t :
        s = '{'
        for i in range(d[0]) :
            s += ' %02x'%(d[1+i])
        return s + ' }'
    else :
        raise RuntimeError('%s(%d)'%(t,s))
    
def parse_params(body, plist) :
    for p in plist :
        length = get_length(p['type'],body)
        datatype = p['datatype']
        data = body[:length]
        body = body[length:]    
        print('  ',datatype,p['name'],render(datatype,data,length))
        
if data[1] != len(data) - 4 :
    print('Invalid length header:%d, data:%d'%(data[1],len(data)-4))

print('class: 0x%02x, %s: 0x%02x'%(data[2],options['mode'],data[3]))
cls = lc.classes.get(data[2])
print("class name: %s"%(cls.get('name')))
subcls = cls.get(options['mode'])
if None == subcls :
    print("cls.get(%s) failed"%(options['mode']))
    print('cls:',cls)
    quit()
obj = subcls[data[3]]
print("%s name: %s"%(options['mode'],obj.get('name')))
parse_params(data[4:],obj[options['params']])
