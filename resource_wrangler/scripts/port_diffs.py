import json
import os
import shutil
import subprocess
import tempfile

from resource_wrangler.main import load_resources
from resource_wrangler.scripts.merge_patches import merge_patches
from resource_wrangler.scripts.port_patches import port_patches

# WARNING: this script assumes a certain structure to the resource naming:
#           f`{pack}-modded-1.{minor_version}.x`

def port_diffs(
        pack,
        minor_version,
        git_hashes_path,
        all_minor_versions):
    """
    apply changes in pack's minor version since the stored git hash to all patches directories
    :param pack: 'fanver', 'jstr', etc.
    :param minor_version: semver minecraft minor version
    :param git_hashes_path: path to .json file storing last-synced git hash
    :param all_minor_versions: all minor versions in the pack's history
    """

    git_hashes_path = os.path.expanduser(git_hashes_path)

    if not os.path.exists(git_hashes_path):
        with open(git_hashes_path, 'w') as git_hashes_file:
            json.dump({}, git_hashes_file, indent=4)

    resources = load_resources()
    resource_prior = resources[f'{pack}-modded-1.{minor_version}.x']
    default_prior = resources[f'default-modded-1.{minor_version}.x']


    # get current git hash
    prior_patches_dir = os.path.expanduser(resource_prior['patches_dir'])
    current_git_hash = get_current_hash(prior_patches_dir)

    # get prior git hash
    with open(git_hashes_path, 'r') as git_hashes_file:
        prior_git_hash = json.load(git_hashes_file).get(str(minor_version), current_git_hash)

    # data is already current
    if prior_git_hash == current_git_hash:
        print("Repository is already current.")
        return

    # retrieve all added/modified files since last known hash
    diff_text = subprocess.check_output(["git", "diff", "--name-status", prior_git_hash, current_git_hash], cwd=prior_patches_dir).decode('utf-8')
    new_paths = []
    for diff_line in diff_text.split('\n'):
        filter_char, *relative_paths = diff_line.split('\t')
        if filter_char in ['A', 'M']:
            new_paths.append(relative_paths[0])
        if filter_char.startswith('R') or filter_char.startswith('C'):
            new_paths.append(relative_paths[1])

    with tempfile.TemporaryDirectory() as diff_dir, tempfile.TemporaryDirectory() as merged_diff_dir:

        # make a fake patches dir
        for relative_path in new_paths:
            prior_path = os.path.join(prior_patches_dir, relative_path)
            temp_path = os.path.join(diff_dir, relative_path)

            os.makedirs(os.path.dirname(temp_path), exist_ok=True)
            shutil.copy2(prior_path, temp_path)
        for patch_name in os.listdir(diff_dir):
            post_mod_json_path = os.path.join(diff_dir, patch_name, 'mod.json')
            prior_mod_json_path = os.path.join(prior_patches_dir, patch_name, 'mod.json')
            if os.path.exists(prior_mod_json_path) and not os.path.exists(post_mod_json_path):
                shutil.copy2(prior_mod_json_path, post_mod_json_path)

        # merge fake patches
        merge_patches(diff_dir, merged_diff_dir)

        # port diff patches to other repos
        for to_minor_version in all_minor_versions:
            if to_minor_version == minor_version:
                continue

            resource_post = resources[f'{pack}-modded-1.{to_minor_version}.x']
            default_post = resources[f'default-modded-1.{to_minor_version}.x']

            port_patches(
                default_prior_dir=default_prior['pack_dir'],
                default_post_dir=default_post['pack_dir'],
                resource_prior_patches_dir=diff_dir,
                resource_post_patches_dir=resource_post['patches_dir'],
                resource_post_dir=resource_post['pack_dir'],
                resource_prior_dir=merged_diff_dir,
                default_post_patches_dir=default_post['patches_dir'],
                action='copy-overwrite')

    # update file contents with current hash
    with open(git_hashes_path, 'r') as git_hashes_file:
        git_hashes = json.load(git_hashes_file)
    git_hashes[str(minor_version)] = current_git_hash
    with open(git_hashes_path, 'w') as git_hashes_file:
        json.dump(git_hashes, git_hashes_file)


def get_current_hash(patches_dir):
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=patches_dir).strip().decode("utf-8")


if __name__ == "__main__":
    # call this like:
    # python3 resource_wrangler/scripts/port_diffs.py fanver 16
    import argparse
    minor_versions = [16, 15, 12, 11, 10, 8, 7, 6, 5]

    parser = argparse.ArgumentParser(description='Port differences since last git SHA to all other patch repositories.')
    parser.add_argument('pack', help='"fanver" or "jstr"')
    parser.add_argument('minor_version', type=int)

    args = parser.parse_args()

    git_hashes_path = f"~/graphics/{args.pack}/git_hashes.json"
    port_diffs(args.pack, args.minor_version, git_hashes_path, minor_versions)
