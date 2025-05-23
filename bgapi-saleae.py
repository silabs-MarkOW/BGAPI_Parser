import sys
import getopt
import bgapi_parser
import Parse_Options
import render_dump

cli = Parse_Options.CliParser()

#cli.add_option('rodata',(int,str),params="<size,name>",desc="generate <size> bytes sized variable called <name> in .rodata")
#cli.add_option('data',(int,str),params="<size,name>",desc="generate <size> bytes sized variable called <name> in .data")
#cli.add_option('binary-image',(str,str),params="<filename,name>",desc="place contents of <filename> in variable called <name> in .rodata")
cli.add_option('xapi',str,params="<xapi-file>",desc="file describing BGAPI, see $SDK/protocol/bluetooth/api/sl_bt.axpi")
cli.add_option('tx',str,params="<tx-label>",desc="label of the channel containing TX data from NCP target",default='TX')
cli.add_option('rx',str,params="<rx-label>",desc="label of the channel containing RX data from NCP target",default='RX')

options,params = cli.parse()

if len(params) != 1 :
    cli.exit_help('expecting single parameter, <Saleae-capture-file>')

filename = params[0]

fh = open(filename,'r')
text = fh.read()
fh.close()

lines = text.split('\n')
state = 'None'

def setState(newState) :
    global state
    if state == newState : return state
    print('State: %s -> %s'%(state,newState))
    state = newState

class BgapiStream :
    def __init__(s) :
        s.state = 'waitHeader'
        s.packet = b''
        s.debug = False
    def setDebug(self,debug=True) :
        self.debug = debug
    def process(s,octet) :
        if s.debug : print('0x%02x %s %s'%(octet,s.state,s.packet.__str__()))
        if 'waitHeader' == s.state :
            if 0x20 == octet or 0xa0 == octet :
                s.state = 'waitLength'
                s.packet = octet.to_bytes(1,'little')
            return
        s.packet += octet.to_bytes(1,'little')
        if 'waitLength' == s.state :
            s.length = octet
            s.state = 'waitClass'
            if s.debug : print(s.state)
            return
        elif 'waitClass' == s.state :
            s.state = 'waitSub'
            if s.debug : print(s.state)
            return
        elif 'waitSub' == s.state :
            s.state = 'body'
            if s.debug : print(s.state)
        if 'body' == s.state :
            if 0 == s.length :
                s.state = 'waitHeader'
                if s.debug : print(s.state)
                return s.packet
        else :
            raise RuntimeError('Fail! state:%s'%(s.state))    
        s.length -= 1
        
rx = BgapiStream()
tx = BgapiStream()
# rx.setDebug(True)

lc = bgapi_parser.BgapiParser(options['xapi'])
parser = render_dump.Renderer(lc)

def dump(packet) :
    s = ''
    for b in packet :
        s += ('%02x'%(b))
    print(s)
    
setState('Start')
for line in lines :
    tokens = line.split(',')
    if len(tokens) < 6 : continue
    if 'Start' == state :
        if 'name' == tokens[0] :
            setState('Ready')
            continue
        raise RuntimeError('Expecting header, got "%s"'%(line))
    elif 'Ready' == state :
        if '"data"' == tokens[1] :
            if '"' != tokens[0][0] or '"' != tokens[0][3] :
                raise RuntimeError(line)
            channel = tokens[0][1:3]
            octet = int(tokens[4],16)
            if 'RX' == channel :
                packet = rx.process(octet)
            elif 'TX' == channel :
                packet = tx.process(octet)
            if None == packet : continue
            if 'TX' == channel and 0xa0 == packet[0] :
                if 0x05 == packet[2] and 0x00 == packet[3] : continue
                if 85 == packet[2] and 0x00 == packet[3] : continue
            if 'RX' == channel :
                #dump(packet)
                parser.render_command(packet)
            elif 'TX' == channel :
                if 0x20 == packet[0] :
                    #dump(packet)
                    parser.render_response(packet)
                elif 0xa0 == packet[0]:
                    #dump(packet)
                    parser.render_event(packet)
            else :
                print('%s: %s'%(channel,packet.__str__()))
