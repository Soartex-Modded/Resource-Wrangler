import requests

from resource_wrangler.main import run, load_resources
import os
from distutils.dir_util import copy_tree
import shutil
from datetime import datetime

# patches to omit from the universal pack, for each minor version
blacklists = {
    # These patches are replaced by Project_Red_4_7, Buildcraft_7 and GregTech
    7: ['Project_Red', 'Buildcraft', 'GregTech_v6']
}

# pack_formats = {1: [6, 7, 8], 2: [9, 10], 3: [11, 12], 4: [13, 14], 5: [15], 6: [16], 7: [17]}

# mapping of 1.{minor_version}.x: gameVersionTypeID
version_ids = {5: 11, 6: 6, 7: 5, 8: 4, 10: 572, 11: 599, 12: 628, 15: 68722, 16: 70886}

project_ids = {'fanver': 227770, 'invictus': 228360}


def universal_build(pack, minor_version, output_dir):

    modded_pack = pack
    if modded_pack == 'invictus':
        modded_pack = 'fanver'

    resources = load_resources()

    patches_dir = os.environ.get(
        'TRAVIS_BUILD_DIR',
        os.path.expanduser(resources[f'{modded_pack}-modded-1.{minor_version}.x']['patches_dir']))

    merged_patches_dir = os.path.expanduser(resources[f'{modded_pack}-modded-1.{minor_version}.x']['pack_dir'])
    if os.path.exists(merged_patches_dir):
        shutil.rmtree(merged_patches_dir)

    # download resources and merge patches
    run('prepare_universal',
        pipelines={'prepare_universal': [
            {'task': 'download_resource', 'resource': f'{pack}-vanilla-1.{minor_version}.x'},
            {'task': 'download_resource', 'resource': f'{modded_pack}-modded-base'} if minor_version > 11 and modded_pack == 'fanver' else None,
            {'task': 'merge_patches', 'resource': 'temp-modded', 'blacklist': blacklists.get(minor_version)},
        ]},
        resources={
            'temp-modded': {
                'patches_dir': patches_dir,
                'pack_dir': resources[f'{modded_pack}-modded-1.{minor_version}.x']['pack_dir'],
                'enable_patch_map': False
            }
        })

    shutil.rmtree(output_dir, ignore_errors=True)
    os.makedirs(output_dir)

    print(">> Copy vanilla into output_dir")
    copy_tree(
        os.path.expanduser(resources[f'{pack}-vanilla-1.{minor_version}.x']['download_dir']),
        output_dir)
    if minor_version > 11 and modded_pack == 'fanver':
        print(">> Copy modded base assets into output_dir")
        copy_tree(
            os.path.join(os.path.expanduser(resources[f'{modded_pack}-modded-base']['download_dir']), 'assets'),
            os.path.join(output_dir, 'assets'))
    print(">> Copy merged patch assets into output_dir")
    copy_tree(
        merged_patches_dir,
        output_dir)

    whitelist_extensions = ['.png', '.txt', '.properties']
    if minor_version > 5:
        whitelist_extensions.extend(['.json', '.mcmeta'])

    if minor_version == 5:
        # Curseforge considers periods in folder names to be file extensions
        for walk_dir, folder_names, _ in os.walk(output_dir):
            for folder_name in folder_names:
                if '.' in folder_name:
                    hazard_dir = os.path.join(walk_dir, folder_name)
                    print("Removing hazard dir:", hazard_dir)
                    shutil.rmtree(hazard_dir, ignore_errors=True)

    print(f'>> Pruning to {whitelist_extensions}')
    for file_dir, _, file_names in os.walk(output_dir):
        for file_name in file_names:
            if any(file_name.endswith(extension) for extension in whitelist_extensions):
                continue
            print('Removing:', os.path.join(file_dir, file_name))
            os.remove(os.path.join(file_dir, file_name))

    if modded_pack == 'fanver':
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


def universal_deploy(pack, minor_version, pack_dir, cleanup=False):

    CURSEFORGE_TOKEN = os.environ[f'CURSEFORGE_{pack.upper()}_TOKEN']

    if pack == 'fanver':
        now = datetime.now()
        display_name = f'Fanver-Universal-1.{minor_version}.x'
        release_filename = f'Soartex_Fanver_Universal_1.{minor_version}.x_{now.year}_{now.month:02}_{now.day:02}.zip'
    elif pack == 'invictus':
        now = datetime.now()
        display_name = f'Invictus-Universal-1.{minor_version}.x'
        release_filename = f'Invictus_Universal_1.{minor_version}.x_{now.year}_{now.month:02}_{now.day:02}.zip'
    else:
        raise ValueError('Unrecognized pack name')

    print(f'>> Retrieving relevant game ids')
    version_data = requests.get(
        "https://minecraft.curseforge.com/api/game/versions",
        headers={"X-Api-Token": CURSEFORGE_TOKEN}).json()

    game_ids = [i['id'] for i in version_data
                if i['name'].startswith(f'1.{minor_version}')
                and i['gameVersionTypeID'] == version_ids[int(minor_version)]]

    print("game ids", game_ids)

    release_path = os.path.join(os.path.dirname(pack_dir), release_filename)
    if os.path.exists(release_path):
        os.remove(release_path)

    print('>> Building the release .zip')
    shutil.make_archive(release_path.replace('.zip', ''), 'zip', pack_dir)

    print('>> Uploading the release .zip')
    # with open(release_path, 'rb') as release_file:
    #     requests.post(
    #         f"https://minecraft.curseforge.com/api/projects/{project_ids[pack]}/upload-file",
    #         headers={"X-Api-Token": CURSEFORGE_TOKEN},
    #         data={
    #             "changelog": f"https://github.com/Soartex-Modded/Modded-1.{minor_version}.x/commits/master",
    #             "changelogType": "text",
    #             "displayName": display_name,
    #             "gameVersions": game_ids,
    #             "releaseType": "release"
    #         },
    #         files={
    #             'file': (release_filename, release_file)
    #         })

    if cleanup:
        os.remove(release_path)


if __name__ == "__main__":
    # call this like:
    # python3 resource_wrangler/scripts/universal.py --deploy fanver 16
    import argparse

    parser = argparse.ArgumentParser(description='Build/Deploy a universal resource pack.')
    parser.add_argument('--deploy', action="store_true")
    parser.add_argument('pack', help='"fanver", "invictus" or "jstr"')
    parser.add_argument('minor_version', type=int)

    args = parser.parse_args()
    output_dir = os.path.expanduser(f'~/graphics_merged/{args.pack}/Universal-1.{args.minor_version}.x')

    if os.path.exists(output_dir):
        print('>> Removing output dir')
        shutil.rmtree(output_dir, ignore_errors=True)

    print(f">>>> Building {args.pack} universal 1.{args.minor_version}.x pack")
    universal_build(
        pack=args.pack,
        minor_version=args.minor_version,
        output_dir=output_dir)

    if args.deploy:
        print(f">>>> Deploying {args.pack} universal 1.{args.minor_version}.x pack")
        universal_deploy(
            pack=args.pack,
            minor_version=args.minor_version,
            pack_dir=output_dir)
