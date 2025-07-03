import argparse
import os

def get_default_xapi() :
    SSDK = os.environ.get('SSDK')
    GSDK = os.environ.get('GSDK')
    for sdk in [SSDK, GSDK] :
        if None != sdk :
            return sdk + '/protocol/bluetooth/api/sl_bt.xapi'
    return None

def get_global_options() :
    parser = argparse.ArgumentParser()
    parser.add_argument('--xapi',default=get_default_xapi(),help='file describing API {[SG]SDK}/protocol/bluetooth/api/sl_bt.xapi')
    parser.add_argument('--debug',action='store_true',help='show generally uninteresting info')
    return parser
