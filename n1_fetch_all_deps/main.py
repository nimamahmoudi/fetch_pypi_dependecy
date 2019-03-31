import numpy as np
import pandas as pd
import datetime


data_folder = 'data/'

df_dep = pd.read_csv(data_folder + 'pypi_dependencies.csv', error_bad_lines=False, warn_bad_lines=False)
df_proj = pd.read_csv(data_folder + 'pypi_projects.csv', error_bad_lines=False, warn_bad_lines=False,low_memory=False)
df_ver = pd.read_csv(data_folder + 'pypi_versions.csv', error_bad_lines=False, warn_bad_lines=False,low_memory=False)

for df in [df_proj, df_ver, df_dep]:
    time_fields = []
    for col in df.columns:
        if 'timestamp' in col:
            time_fields.append(col)
    for time_field in time_fields:
        try:
            df[time_field] = df[time_field].apply(lambda x: datetime.datetime.strptime(x, '%Y-%m-%d %H:%M:%S'))
        except:
            pass
        
del df

print(df_dep.shape)
print(df_proj.shape)
print(df_ver.shape)

new_deps = {}
for col in df_dep.columns:
    new_deps[col] = []
del new_deps['id']
print(new_deps)

import time
from xmlrpc import client as xmlrpclib

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

package_name = 'django'
release_version = '2.1.7'
print(robust_get_dependencies(package_name, release_version))


###################
import tarfile, re, requests, csv, json
from base64 import b64encode
import os

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
        return name
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
    
    return name
                
                
def extract_package(name, release, client=xmlrpclib.ServerProxy('http://pypi.python.org/pypi')):
#     for release in client.package_releases(name):
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

ensure_dir('packages')
ensure_dir('tmp')

import shutil

import time
from requirements_detector import find_requirements
from requirements_detector.detect import RequirementsNotFound
def robust_extract(package, version, client, retry=5):
    if retry == 0:
        return None, None
    try:
        name = extract_package(package, version, client)
        if name is not None:
            reqs = find_requirements(name)

            if os.path.isdir(name):
                shutil.rmtree(name)
            
            deps = []
            dep_reqs = []
            for req in reqs:
                dep = req.name
                if type(dep) == bytes:
                    dep = dep.decode("utf-8", "ignore")
                elif dep == None:
                    dep = "none"
                else:
                    dep = str(dep)
                dep_req = "*"
                if len(req.version_specs) > 0:
                    dep_req = "".join(list(req.version_specs[0]))
#                 print("++", dep, dep_req)
                deps.append(dep)
                dep_reqs.append(dep_req)
            return deps, dep_reqs
        else:
            return None, None
    except RequirementsNotFound:
        if os.path.isdir(name):
            shutil.rmtree(name)
        return None, None
#     except requests.exceptions.HTTPError as e:
    except Exception as e:
        # Whoops it wasn't a 200
        print("Error: " + str(e))
        time.sleep(5)
        return robust_extract(package, version, client, retry-1)

reqs = robust_extract('msrflux', '1.3', client)
# reqs = robust_extract('httpretty', '0.5', client)







total_vers = df_ver.shape[0]

count = 0
for index, row in df_ver.iterrows():
    count += 1
    if count % 1000 == 1:
        print(count, '/' , total_vers)
    # if count > 200:
    #     break

    package_name = df_ver.loc[index, 'project_name']
    release_version = df_ver.loc[index, 'number']
    # print(package_name, release_version)
    deps1, dep_reqs1 = robust_get_dependencies(package_name, release_version)
    deps2, dep_reqs2 = robust_extract(package_name, release_version, client)
    
    if deps1 is not None:
        deps1 = [x.lower() for x in deps1]
    if deps2 is not None:
        deps2 = [x.lower() for x in deps2]
    
    deps = None
    dep_reqs = None
    if deps1 is None:
        deps = deps2
        dep_reqs = dep_reqs2
    else:
        deps = deps1
        dep_reqs = dep_reqs1
        if deps2 is not None: # both not none:
            for i in range(len(deps2)):
                dep = deps2[i]
                dep_req = dep_reqs2[i]
                if dep not in deps:
                    deps.append(dep)
                    dep_reqs.append(dep_req)

    # if error happened
    if deps is None:
        print('Failed for:', package_name, release_version)
        continue

    dep_counts = len(deps)
    
    new_deps['platform'] += (['Pypi']*dep_counts)
    new_deps['project_name'] += ([package_name]*dep_counts)
    new_deps['project_id'] += ([df_ver.loc[index, 'project_id']]*dep_counts)
    new_deps['version_number'] += ([release_version]*dep_counts)
    new_deps['version_id'] += ([df_ver.loc[index, 'id']]*dep_counts)
    new_deps['dependency_name'] += deps
    new_deps['dependency_platform'] += (['Pypi']*dep_counts)
    new_deps['dependency_kind'] += (['runtime']*dep_counts)
    new_deps['optional_dependency'] += ([False]*dep_counts)
    new_deps['dependency_requirements'] += dep_reqs
    new_deps['dependency_project_id'] += ([np.nan]*dep_counts)




new_df = pd.DataFrame(data=new_deps)
print(new_df.head())

new_df.to_csv('output/new_reqs.csv')

new_deps2 = {
    'package_name': new_deps['project_name'],
    'requirement': new_deps['dependency_name'],
}
new_df2 = pd.DataFrame(data=new_deps2)
new_df2.to_csv('output/requirements.csv')
