def get_length(t,d) :
    if 'uint8array' == t :
        return 1 + d[0]
    if 'uint16array' == t :
        return 1 + d[0] + (d[1] << 8)
    value = lc.api['datatypes']['length'].get(t)
    if None == value :
        if 'sl_bt_' == t[:6] and '_t' == t[-2:] :
            value = lc.api['datatypes']['length'].get(t[6:-2])
            if None == value :
                print(lc.api['datatypes']['length'])
                raise RuntimeError(t)
    length = int(value)
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

like_uint16 = ['uint16','characteristic','descriptor','attribute_handle','errorcode','uuid_16']
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
    if 2 == s :
        for testt in like_uint16 :
            if testt == t : return '0x%02x%02x'%(d[1],d[0])

    if 'int8' == t :
        value = d[0]
        sign = 1 << 7
        if value & sign :
            value -= sign
        return '%+d'%value
    if 'int16' == t :
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
    elif 'uint16array' == t :
        s = '{'
        for b in d[2:] :
            s += ' %02x'%(b)
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

