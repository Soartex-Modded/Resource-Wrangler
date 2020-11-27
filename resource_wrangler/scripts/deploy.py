import tempfile
import zipfile

import requests

from resource_wrangler.main import run, load_resources
import os
from distutils.dir_util import copy_tree
import shutil
from datetime import datetime

# patches to omit from the universal pack, for each minor version
blacklists = {
    7: ['Project_Red', 'Buildcraft', 'GregTech_v6']  # These patches are replaced by Buildcraft_7 and Project_Red_4_7
}


def universal_build(pack, minor_version, output_dir):
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

    print(">> Copy vanilla into output_dir")
    copy_tree(
        os.path.expanduser(resources[f'{pack}-vanilla-1.{minor_version}.x']['download_dir']),
        output_dir)
    if minor_version > 11 and pack == 'fanver':
        print(">> Copy modded base assets into output_dir")
        copy_tree(
            os.path.join(os.path.expanduser(resources[f'{pack}-modded-base']['download_dir']), 'assets'),
            os.path.join(output_dir, 'assets'))
    print(">> Copy merged patch assets into output_dir")
    copy_tree(
        os.path.expanduser(resources[f'{pack}-modded-1.{minor_version}.x']['pack_dir']),
        output_dir)

    blacklist_extensions = ['.xcf', '.psd', '.iml', '.xml']
    print(f'>> Pruning {blacklist_extensions}')
    for file_dir, _, file_names in os.walk(output_dir):
        for file_name in file_names:
            if any(file_name.endswith(extension) for extension in blacklist_extensions):
                os.remove(os.path.join(file_dir, file_name))

    if pack == 'fanver':
        print(f'>> Writing fanver license/credits')
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


def universal_deploy(pack, minor_version, pack_dir, project_id):

    CURSEFORGE_FANVER_TOKEN = os.environ[f'CURSEFORGE_{pack.upper()}_TOKEN']

    if pack == 'fanver':
        display_name = 'Fanver-Universal'
        release_filename = 'Soartex_Fanver_Modded_Universal.zip'
    else:
        raise ValueError('Unrecognized pack name')

    print(f'>> Retrieving relevant game ids')
    version_data = requests.get("https://minecraft.curseforge.com/api/game/versions", headers={
        "X-Api-Token": CURSEFORGE_FANVER_TOKEN
    }).json()

    # mapping of 1.{minor_version}.x: gameVersionTypeID
    version_ids = {7: 5, 8: 4, 10: 572, 11: 599, 12: 628, 15: 68722, 16: 70886}

    game_ids = [i['id'] for i in version_data
                if i['name'].startswith(f'1.{str(minor_version)}')
                and i['gameVersionTypeID'] == version_ids[int(minor_version)]]

    with tempfile.TemporaryDirectory() as temp_dir, \
            zipfile.ZipFile(os.path.join(temp_dir, release_filename), 'w', zipfile.ZIP_DEFLATED) as release_file:

        print('>> Building the release .zip')
        for walk_dir, _, file_names in os.walk(pack_dir):
            for file_name in file_names:
                release_file.write(os.path.join(walk_dir, file_name))

        print('>> Uploading the release .zip')
        requests.post(
            f"https://minecraft.curseforge.com/api/projects/{project_id}/upload-file",
            headers={"X-Api-Token": CURSEFORGE_FANVER_TOKEN},
            data={
                "changelog": f"https://github.com/Soartex-Modded/Modded-1.{minor_version}.x/commits/master",
                "changelogType": "text",
                "displayName": display_name,
                "gameVersions": game_ids,
                "releaseType": "release"
            },
            files={
                'file': release_file
            })
