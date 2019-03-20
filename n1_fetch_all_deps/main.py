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
            
    time.sleep(.18)
    return deps, dep_reqs


def robust_get_dependencies(package_name, release_version):
    try:
        return get_dependencies(package_name, release_version)
    except Exception as e:
        print('Exception: ' + str(e))
        time.sleep(5)
        return robust_get_dependencies(package_name, release_version)

package_name = 'django'
release_version = '2.1.7'
print(robust_get_dependencies(package_name, release_version))

total_vers = df_ver.shape[0]

count = 0
for index, row in df_ver.iterrows():
    count += 1
    if count % 100 == 1:
        print(count, '/' , total_vers)
    # if count > 200:
    #     break

    package_name = df_ver.loc[index, 'project_name']
    release_version = df_ver.loc[index, 'number']
    # print(package_name, release_version)
    deps, dep_reqs = robust_get_dependencies(package_name, release_version)
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
