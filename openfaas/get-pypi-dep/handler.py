import sys
import json

import time
# from xmlrpc import client as xmlrpclib
import xmlrpclib

# I need this to separate the package name from its version
client = xmlrpclib.ServerProxy('http://pypi.python.org/pypi')
def get_dependencies(package_name, release_version):
    rdata = client.release_data(package_name, release_version)
    deps = []
    dep_reqs = []
    
    if 'requires_dist' in rdata:
        for req in rdata['requires_dist']:
            a = req.split(';')
            a = a[0]
            b = a.split(' ')
            c = b[0]
            d = '*'
            if len(b) > 1:
                if len(b[1]) > 0:
                    d = b[1]
            d = d.strip('()')
            deps.append(c)
            dep_reqs.append(d)
    return deps, dep_reqs

def robust_get_dependencies(package_name, release_version, retry=5):
    if retry == 0:
        return None, None
    try:
        return get_dependencies(package_name, release_version)
    except Exception as e:
        print('Exception: ' + str(e))
        time.sleep(5)
        return robust_get_dependencies(package_name, release_version, retry-1)

def handle(req):
    """handle a request to the function
    Args:
        req (str): request body
    """
    status = 'Error!'

    parts = req.split('=')

    if len(parts) < 2:
        sys.stderr.write('You need to specify the version!\n')
        return json.dumps({"status": status})
    

    package_name = parts[0]
    release_version = parts[1]

    deps, dep_reqs = robust_get_dependencies(package_name, release_version)
    if deps is not None:
        status = 'OK'


    return json.dumps({"status": status,"deps": deps, "dep_reqs": dep_reqs})
