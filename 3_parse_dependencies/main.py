import pandas as pd
from collections import defaultdict
import os
import numpy as np
import requirements
# import xmlrpclib
from xmlrpc import client as xmlrpclib

# I need this to separate the package name from its version
client = xmlrpclib.ServerProxy('http://pypi.python.org/pypi')
packages = client.list_packages()



datadict = defaultdict(list)
with open('packages/extracted_reqs.txt', 'r') as infile:
    new_package = True
    for line in infile:
        if line.strip() == '':
            new_package = True
            #print(package_name)
            if package_name not in datadict['package']:
                datadict['package'].append(package_name)
                datadict['requirement'].append(np.nan)
            continue
        
        if new_package:
            # If this is the case, the current line gives the name of the package
            package_name = os.path.basename(line).strip()
            new_package = False
        else:
            # This line gives a requirement for the current package
            try:
                for req in requirements.parse(line.strip()):
                    datadict['package'].append(package_name)
                    datadict['requirement'].append(req.name)
            except ValueError:
                pass
                

# Convert to dataframe
df = pd.DataFrame(data=datadict)
print(df.head())




df['package_name'] = np.nan
df['package_version'] = np.nan
for i, package in enumerate(packages):
    if i % 100 == 0:
        print('Package {}: {}'.format(i+1, package))
    for release in client.package_releases(package):
        pkg_str = '{}-{}'.format(package, release)
        idx = df.loc[df.package == pkg_str].index
        if len(idx) > 0:
            df.loc[idx, 'package_name'] = package
            df.loc[idx, 'package_version'] = release
print(df.head())




# Save to file
df.to_csv('packages/requirements.csv', index=False)




class Tree(object):
    def __init__(self, name):
        self.name = name
        self.children = []
        return

    def __contains__(self, obj):
        return obj == self.name or any([obj in c for c in self.children])
    
    def add(self, obj):
        if not self.__contains__(obj):
            self.children.append(Tree(obj))
            return True
        return False
    
    def get_base_requirements(self):
        base = []
        for child in self.children:
            if len(child.children) == 0:
                base.append(child.name)
            else:
                for b in [c.get_base_requirements() for c in child.children()]:
                    base.extend(b)
        return np.unique(base)
    

def get_requirements(package):
    return df.loc[(df.package == package) & (df.requirement.notnull()), 'requirement'].values


def get_dependency_tree(package, tree):
    reqs = get_requirements(package)
    for req in reqs:
        #print(req)
        flg = tree.add(req)
        if not flg:
            continue
        # tree = get_base_dependencies(req, tree)
        tree = get_dependency_tree(req, tree)
    return tree

    
    



p = '115wangpan'
p = 'astroquery'
get_dependency_tree(p, Tree(p)).get_base_requirements()






datadict = defaultdict(list)
for i, package in enumerate(df.package_name.unique()):
    if i % 100 == 0:
        print('Package {}: {}'.format(i+1, package))
    try:
        deptree = get_dependency_tree(package, Tree(package))
    except:
        print('Failure getting base dependencies for {}'.format(package))
        raise ValueError
    for dependency in deptree.get_base_requirements():
        datadict['package_name'].append(package)
        datadict['requirements'].append(dependency)

base_df = pd.DataFrame(data=datadict)
print(base_df.head())





base_df.to_csv('packages/base_requirements.csv', index=False)
