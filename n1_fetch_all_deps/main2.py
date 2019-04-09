import numpy as np
import pandas as pd
import datetime

from funcs import *

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


package_name = 'django'
release_version = '2.1.7'
print(robust_get_dependencies(package_name, release_version))


ensure_dir('packages')
ensure_dir('tmp')

# reqs = robust_extract('msrflux', '1.3', client)
# reqs = robust_extract('httpretty', '0.5', client)
print(robust_extract('msrflux', '1.3', client))

new_deps = {}
for col in df_dep.columns:
    new_deps[col] = []
del new_deps['id']

total_vers = df_ver.shape[0]
# total_vers = 1000
inputs = range(total_vers)


from tqdm import tqdm

print('Starting Multiprocessing...')

# from multiprocessing import Pool, cpu_count
# with Pool(2) as p:
#     print('running the pool...')
    # all_res = (p.map(processInput2, zip([df_ver.iloc[i,:] for i in inputs],list(inputs))))
    # all_res = list(tqdm.tqdm(p.imap(processInput2, zip([df_ver.iloc[i,:] for i in inputs],list(inputs))), total=len(inputs)))

# all_res = list(map(processInput2, zip([df_ver.iloc[i,:] for i in inputs],list(inputs))), total=len(inputs))

all_res = []
for i in tqdm(range(total_vers)):
    all_res.append(processInput2(df_ver.iloc[i,:]))

for res in all_res:
    if res is None:
        continue
    if type(res) != dict:
        continue
    for k in res.keys():
        new_deps[k] += res[k]

new_df = pd.DataFrame(data=new_deps)
print(new_df.head())
print(new_df.shape)

new_df.to_csv('output/new_reqs.csv')

new_deps2 = {
    'package_name': new_deps['project_name'],
    'requirement': new_deps['dependency_name'],
}
new_df2 = pd.DataFrame(data=new_deps2)
new_df2.to_csv('output/requirements.csv')