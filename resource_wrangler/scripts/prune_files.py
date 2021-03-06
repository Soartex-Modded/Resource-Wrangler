import os
import shutil


def is_patch_in_default(patch_dir, default_pack):
    """
    Checks if any textures in the patch dir are shadowed in the default pack
    :param patch_dir: path to directory containing one mod patch
    :param default_pack: directory of a default texture pack
    :return: True if patch is represented in the default pack
    """
    for file_dir, _, file_names in os.walk(patch_dir):
        for file_name in file_names:
            patch_file_path = os.path.join(file_dir, file_name)
            relative_path = patch_file_path.replace(patch_dir, "")
            default_file_path = os.path.join(default_pack, *relative_path.split(os.sep))

            if os.path.exists(default_file_path):
                return True

    return False


def prune_files(patches_dir, default_pack_dir, pruned_dir, action=None):
    """
    Delete resources missing from the default pack, only from partially textured patches
    :param patches_dir: directory of mod patches
    :param default_pack_dir: directory of a default texture pack
    :param pruned_dir: directory to move dead files
    :param action: one of [None, '~unused', 'prune']
    """

    patches_dir = os.path.expanduser(patches_dir)
    default_pack_dir = os.path.expanduser(default_pack_dir)
    pruned_dir = os.path.expanduser(pruned_dir)

    for patch_name in os.listdir(patches_dir):
        if patch_name == '.git':
            continue

        patch_dir = os.path.join(patches_dir, patch_name)

        if not is_patch_in_default(patch_dir, default_pack_dir):
            continue

        for file_dir, _, file_names in os.walk(patch_dir):
            for file_name in file_names:
                patch_file_path = os.path.join(file_dir, file_name)
                relative_path = [i for i in patch_file_path.replace(patch_dir, "").split(os.sep) if i]
                default_file_path = os.path.join(default_pack_dir, *relative_path)

                if os.path.exists(default_file_path):
                    continue
                if default_file_path.endswith('mod.json'):
                    continue
                if '~alt' in default_file_path.lower():
                    continue
                if '~unused' in default_file_path.lower():
                    continue
                if default_file_path.lower().endswith('~untextured.txt'):
                    continue
                if default_file_path.endswith(".ctx"):
                    if os.path.exists(default_file_path.replace('.ctx', '.png')):
                        continue
                if default_file_path.endswith(".mcmeta"):
                    if os.path.exists(default_file_path.replace('.mcmeta', '')):
                        continue
                if default_file_path.endswith(".txt"):
                    if os.path.exists(default_file_path.replace('.txt', '.png')):
                        continue
                if patch_file_path.endswith(".DS_Store"):
                    os.remove(patch_file_path)
                    continue

                print(f"dead file: {os.sep.join(relative_path)}")

                if action == '~unused':
                    patch_file_dir, patch_filename = os.path.split(patch_file_path)
                    replace_path = os.path.join(patch_file_dir, '~unused', patch_filename)
                    os.makedirs(os.path.dirname(replace_path), exist_ok=True)
                    shutil.move(patch_file_path, replace_path)
                if action == 'prune':
                    replace_path = os.path.join(pruned_dir, *relative_path)
                    os.makedirs(os.path.dirname(replace_path), exist_ok=True)
                    shutil.move(patch_file_path, replace_path)

    for file_dir, dir_names, file_names in os.walk(patches_dir, topdown=False):
        if '.git' in file_dir:
            continue

        if not dir_names and not file_names:
            print(f"dead folder: {file_dir}")

            if action == 'move':
                os.rmdir(file_dir)
