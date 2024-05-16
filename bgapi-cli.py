import argparse
import bgapi_parser
import os
import sys

def get_default_xapi() :
    GSDK = os.environ.get('GSDK')
    if None == GSDK :
        return None
    return GSDK + '/protocol/bluetooth/api/sl_bt.xapi'

parser = argparse.ArgumentParser()
parser.add_argument('--xapi',default=get_default_xapi(),help='file describing API {GSDK}/protocol/bluetooth/api/sl_bt.xapi')
origin = parser.add_mutually_exclusive_group(required=True)
origin.add_argument('--host',nargs=nargs,help='data from host')
origin.add_argument('--target',nargs=nargs,help='data from target')
parser.add_argument('--octal',action='store_true',help='data is octal')
parser.add_argument('--decimal',action='store_true',help='data is decimal')
parser.add_argument('--hex',action='store_true',help='data is hex')
parser.add_argument('--debug',action='store_true',help='show generally uninteresting info')
args = parser.parse_args()

options = {'mode':'commands','params':'params'}
if args.decimal :
    options['radix'] = 10
elif args.octal :
    options['radix'] = 8
else :
    options['radix'] = 16
    
debug = args.debug
data = []
if debug : print(args)
if args.host :
    params = args.host
else :
    params = args.target
    options['params'] = 'returns'
    
if 1 == len(params) :
    token = params[0]
    if args.decimal or args.octal :
        raise RuntimeError('single token must be hex')
    if len(token) & 1 :
        raise RuntimeError('If data in single token, length must be even')
    if '0x' == token[:2].lower() : token = token[2:]
    for i in range(len(token)>>1) :
        data.append(int(token[i<<1:][:2],16))
else :
    for param in params :
        if len(param) > 2 and '0x' == param[:2].lower() :
            data.append(int(param[2:],16))
        if len(param) > 2 and '0o' == param[:2].lower() :
            data.append(int(param[2:],0))
        else :
            data.append(int(param,options['radix']))
if debug : print('data: %s'%(data.__str__()))
print(data)
if 0xa0 == data[0] :
    options['mode'] = 'events'
    options['params'] = 'params'

lc = bgapi_parser.BgapiParser(args.xapi)

#print(lc.classes)
keys = []
for key in lc.classes :
    keys.append(key)
keys.sort()
#print(keys)

def get_length(t,d) :
    length = int(lc.api['datatypes']['length'][t])
    if 'uint8array' == t :
        return length + d[0]
    if 'uint8array' == t :
        return length + d[0] + (d[1] << 8)
    return length
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
        #print(length,body,type(length))
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
