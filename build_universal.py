from resource_wrangler.main import run, load_resources
import os
from distutils.dir_util import copy_tree
import shutil
import argparse
from datetime import datetime

# patches to omit from the universal pack, for each minor version
blacklists = {
    7: ['Project_Red', 'Buildcraft']  # These patches are replaced by Buildcraft_7 and Project_Red_4_7
}

parser = argparse.ArgumentParser(description='Build a universal resource pack.')
parser.add_argument('pack', help='"fanver" or "jstr"')
parser.add_argument('minor_version', type=int, help='sum the integers (default: find the max)')

args = parser.parse_args()
pack = args.pack
minor_version = args.minor_version


output_dir = os.path.expanduser(f'~/graphics_merged/{pack}/universal-1.{minor_version}.x')

resources = load_resources()

patches_dir = os.environ.get(
    'TRAVIS_BUILD_DIR',
    os.path.expanduser(resources[f'{pack}-modded-1.{minor_version}.x']['patches_dir']))

# download resources and merge patches
run('prepare_universal',
    pipelines={'prepare_universal': [
        {'task': 'download_resource', 'resource': f'{pack}-vanilla-1.{minor_version}.x'},
        {'task': 'download_resource', 'resource': f'{pack}-modded-base'} if minor_version > 11 and pack == 'fanver' else None,
        {'task': 'merge_patches', 'resource': 'temp-modded', 'blacklist': blacklists.get(minor_version)},
    ]},
    resources={
        'temp-modded': {
            'patches_dir': patches_dir,
            'pack_dir': resources[f'{pack}-modded-1.{minor_version}.x']['pack_dir'],
            'enable_patch_map': False
        }
    })

shutil.rmtree(output_dir, ignore_errors=True)
os.makedirs(output_dir)

# copy vanilla into output_dir
copy_tree(
    os.path.expanduser(resources[f'{pack}-vanilla-1.{minor_version}.x']['download_dir']),
    output_dir)
if minor_version > 11 and pack == 'fanver':
    # copy modded base assets into output_dir
    copy_tree(
        os.path.join(os.path.expanduser(resources[f'{pack}-modded-base']['download_dir']), 'assets'),
        os.path.join(output_dir, 'assets'))
# copy merged patches into output_dir
copy_tree(
    os.path.expanduser(resources[f'{pack}-modded-1.{minor_version}.x']['pack_dir']),
    output_dir)

for file_dir, _, file_names in os.walk(output_dir):
    for file_name in file_names:
        if any(file_name.endswith(extension) for extension in ['.xcf', '.psd', '.iml', '.xml']):
            os.remove(os.path.join(file_dir, file_name))

if pack == 'fanver':
    with open(os.path.join(output_dir, 'license_modded_fanver.txt'), 'w') as modded_license_file:
        modded_license_file.write(f"""
Soartex Fanver and Soartex Fanver Mod Patches are community continuation to Soar49's work. As such, we have rules that you must agree to comply with when using our work. You can find these rules in the link below:

http://soartex.net/license/#fanver

Bare in mind that a whole communities' hard work is involved in this project and these rules are to protect such work.

This license solely applies to Soartex Fanver Resource Pack and Soartex Fanver Mod Patches.

© 2012-{datetime.now().year} Soartex Graphics. All rights reserved.
""")

    contributor_links = '\n'.join([
        f"[1.{v}.x]: https://github.com/Soartex-Modded/Modded-1.{v}.x/graphs/contributors"
        for v in [3, 4, 5, 6, 7, 8, 10, 11, 12, 15, 16]
    ])
    with open(os.path.join(output_dir, 'credits_modded_fanver.txt'), 'w') as modded_credits_file:
        modded_credits_file.write(f"""
Many thanks to all!

Original creator is Soar49:
http://www.minecraftforum.net/topic/150915-

The modded patches are created by an amazing community of contributors.
Please find them in their respective modded repositories.

{contributor_links}
""")
