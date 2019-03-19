from xmlrpc import client as xmlrpclib
# only one api server so we'll use the mirror for downloading
client = xmlrpclib.ServerProxy('http://pypi.python.org/pypi')
packages = client.list_packages()

import tarfile, re, requests, csv, json
from base64 import b64encode
import os
import time

tmp_tar = 'tmp/temp_tar'

def ensure_dir(path):
    try:
        dir_name = os.path.dirname(path)
        os.makedirs(dir_name, exist_ok=True)  # succeeds even if directory exists.
    except:
        os.makedirs(path, exist_ok=True)  # succeeds even if directory exists.


def _save_file(pathname, member, tar_file):
    try:
        content = tar_file.extractfile(member).read()
    except:
        return

    outfilename = '{}{}'.format(pathname, os.path.basename(member.name))
    ensure_dir(outfilename)
    with open(outfilename, 'wb') as outfile:
        outfile.write(content)
    return


def _extract_files(package_file, name):
    try:
        tar_file = tarfile.open(fileobj=package_file)
    except:
        return
    for member in tar_file.getmembers():
        if 'setup.py' in member.name or 'requirements' in member.name:
            _save_file(name, member, tar_file)
        #    content = tar_file.extractfile(member).read()
        #    with open('{}{}'.format(name, os.path.basename(member.name)), 'w') as outfile:
        #        outfile.write(content)
        #elif 'requirements' in member.name:
        #    content = tar_file.extractfile(member).read()
        #    with open('{}{}'.format(name, os.path.basename(member.name)), 'w') as outfile:
        #        outfile.write(content)


def extract_package(name, client=xmlrpclib.ServerProxy('http://pypi.python.org/pypi')):
    for release in client.package_releases(name):
        outdir = 'packages/{}-{}/'.format(name, release)
        doc = client.release_urls(name, release)
        if doc:
            url = None
            for d in doc:
                if d['python_version'] == 'source' and d['url'].endswith('gz'):
                    url = d['url']
            if url:
                #print(doc[3])
                #url = doc[0].get('url')#.replace("http://pypi.python.org/", "http://f.pypi.python.org/")
                #print "Downloading url %s" % url
                req = requests.get(url)
                if req.status_code != 200:
                    print("Could not download file %s" % req.status_code)
                else:
                    #print(outdir)
                    ensure_dir('{}'.format(outdir))
                    with open(tmp_tar, 'wb') as tar_file:
                        tar_file.write(req.content)
                    with open(tmp_tar, 'rb') as tar_file:
                        return _extract_files(tar_file, name=outdir)

def robust_extract(package, client):
    try:
        extract_package(package, client)
    except requests.exceptions.HTTPError as e:
        # Whoops it wasn't a 200
        print("Error: " + str(e))
        time.sleep(10)
        robust_extract(package, client)

if __name__=='__main__':
    ensure_dir('packages')
    ensure_dir('tmp')

    print('starting...')
    for i, package in enumerate(packages[118300+4100:]):
        if i % 100 == 0:
            print('Extracting package {} / {}'.format(i+1, len(packages)))
        #print(package)

        robust_extract(package, client)
    print('done!')