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
    if 1 == s :
        for tt in ['uint8','connection'] :
            if tt == t : return '0x%02x'%(d[0])
    if 4 == s :
        for tt in ['uint32','service'] :
            s = '0x'
            for i in range(4) :
                s += '%02x'%(d[3-i])
            return s
            
    if 'uint16' == t or 'characteristic' == t : return '0x%02x%02x'%(d[1],d[0])
    elif 'errorcode' == t : return '0x%02x%02x'%(d[1],d[0])
    elif 'int16' == t :
        value = 0
        for i in range(2) :
            value += d[i] << (i << 3)
        sign = 1 << 15
        if value & sign :
            value -= sign
        return '%+d'%value
    elif 'uint8array' == t or 'uuid' == t :
        s = '{'
        for i in range(d[0]) :
            s += ' %02x'%(d[1+i])
        return s + ' }'
    elif 'bd_addr' == t :
        d.reverse()
        return ':'.join(["%02x"%(b) for b in d])
    elif 'dbm' == t :
        return "%.1f dBm"%(0.1*d[0])
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

def set_lc(value) :
    global lc
    lc = value
    
class Renderer :
    def __init__(self,lc) :
        self.lc = lc
    def setup(self,mode,pmode,data) :
        cls = self.lc.classes.get(data[2])
        subcls = cls.get(mode)
        obj = subcls[data[3]]
        print(cls.get('name'),obj.get('name'))
        set_lc(self.lc)
        parse_params(list(data[4:]),obj[pmode])
    def render_command(self,packet) :
        print("Command: ",end='')
        self.setup('commands','params',packet)
    def render_event(self,packet) :
        print("Event: ",end='')
        self.setup('events','params',packet)
    def render_response(self,packet) :
        print("Response: ",end='');
        self.setup('commands','returns',packet)

