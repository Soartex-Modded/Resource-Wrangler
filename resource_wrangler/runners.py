import os
import shutil

import resource_wrangler.scripts as scripts
import time
import json

# OVERVIEW
# functions in this file use the pipeline/task config and resource metadata to call out to functions in the scripts folder


def run_pipeline(config, resources, pipelines):
    """
    run a task that executes any pipeline or single task
    :param config: {'pipeline': str} or {'task': str}
    :param resources: dictionary of resources, each resource contains paths to important directories
    :param pipelines: dictionary of pipelines, each pipeline contains a list of tasks
    """
    print("Running pipeline:", config['pipeline'])
    task_runners = {
        'extract_default': run_extract_default,
        'merge_patches': run_merge_patches,
        'link_resources': run_link_resource,
        'watch_changes': run_watch_changes,
        'port_patches': run_port_patches,
        'prune_files': run_prune_files,
        'detect_overwrites': run_detect_overwrites,
        'remove_resource': run_remove_resource,
        'download_mods': run_download_mods,
        'download_resource': run_download_resource,
        'run_pipeline': run_pipeline,
        'run_parallel': run_parallel,
        'run_apply': run_apply,
        'run_subprocess': run_run_subprocess,
        'fix_mod_jsons': run_fix_mod_jsons,
        'build_guis': run_build_guis,
        'insert_placeholders': run_insert_placeholders,
        'find_similar': run_find_similar,
        'detect_broken_animations': run_detect_broken_animations
    }

    if config['pipeline'] not in pipelines:
        # if any individual task is passed to the run_pipeline task, direct it to the proper task
        if 'task' in config and config['task'] in task_runners:
            task_runners[config['task']](config, resources, pipelines)
        else:
            raise ValueError(f"Pipeline not recognized: {config['pipeline']}")

    # run every step in the pipeline
    for task in pipelines[config['pipeline']]:
        if task is None:
            continue
        task_runners[task['task']](task, resources, pipelines)


def run_parallel(config, resources, pipelines):
    """run a task that executes all tasks in a pipeline on different processes"""
    # This task probably doesn't have great benefits, as most of these scripts are bound by disk transfer
    print("Running in parallel:", config['pipeline'])
    if config['pipeline'] not in pipelines:
        raise ValueError(f"Pipeline not recognized: {config['pipeline']}")

    scripts.parallel(pipelines[config['pipeline']], run_pipeline, args=(resources, pipelines))


def run_apply(config, resources, pipelines):
    """run a task that sequentially executes the same task over multiple resources"""
    print("Applying task to multiple resources.")

    # construct a new pipeline
    resource_names = config.pop('resources')
    apply_task = config.pop('apply_task')

    pipeline = [{**config, 'resource': resource_name, 'task': apply_task} for resource_name in resource_names]

    # register pipeline
    pipeline_name = json.dumps(pipeline, indent=4)
    pipelines[pipeline_name] = pipeline

    # call registered pipeline
    run_pipeline({"task": "run_pipeline", "pipeline": pipeline_name}, resources, pipelines)


def run_extract_default(config, resources, pipelines):
    """run a task that unpacks mod .jar files into a patches directory"""
    resource = resources[config['resource']]
    print("Extracting mods.")
    scripts.extract_default(resource['mods_dirs'], resource['patches_dir'])


def run_link_resource(config, resources, pipelines):
    """run a task that creates symlinks from multiple minecraft instances to a resource pack directory"""
    resource = resources[config['resource']]
    print("Linking resources.")
    scripts.link_resource(resource['link_dirs'], resource['pack_dir'])


def run_unlink_resource(config, resources, pipelines):
    """run a task that destroys all symlinks currently associated with the resource"""
    resource = resources[config['resource']]
    print("Unlinking resources.")
    scripts.unlink_resource(resource['link_dirs'])


def run_merge_patches(config, resources, pipelines):
    """run a task that merges patches in a patch directory into a resource pack"""
    resource = resources[config['resource']]
    print("Resource:", json.dumps(resource, indent=4))
    print("Merging patches.")
    start_time = time.time()
    scripts.merge_patches(patches_dir=resource['patches_dir'], pack_dir=resource['pack_dir'],
                          pack_format=resource.get('pack_format'),
                          enable_patch_map=resource.get('enable_patch_map', True),
                          blacklist=config.get('blacklist'))
    elapsed_time = time.time() - start_time
    print(f"Patches merged in {round(elapsed_time)} seconds.")


def run_watch_changes(config, resources, pipelines):
    """run a task that watches for filesystem changes in a patches dir, and syncs those changes with a resource pack"""
    resources = [resources[resource_id] for resource_id in config['resources']]
    print(f"Watching for changes in {[res['patches_dir'] for res in resources]}.")
    scripts.watch_changes(resources)


def run_port_patches(config, resources, pipelines):
    """run a task that uses md5 image hashes to detect and fill equivalent images"""
    print("Porting", config)
    scripts.port_patches(
        default_prior_dir=resources[config['default_prior']]['pack_dir'],
        default_post_dir=resources[config['default_post']]['pack_dir'],
        resource_prior_patches_dir=resources[config['resource_prior']]['patches_dir'],
        resource_post_patches_dir=resources[config['resource_post']]['patches_dir'],
        resource_post_dir=resources[config['resource_post']]['pack_dir'],
        resource_prior_dir=resources[config['resource_prior']]['pack_dir'],
        default_post_patches_dir=resources[config['default_post']]['patches_dir'],
        action=config.get('action')
    )


def run_prune_files(config, resources, pipelines):
    """run a task that removes files from a patches directory that are not present in the default textures"""
    print("Pruning files.")
    scripts.prune_files(
        patches_dir=resources[config['resource']]['patches_dir'],
        default_pack_dir=resources[config['resource_default']]['pack_dir'],
        pruned_dir=config['pruned_dir'],
        action=config.get('action')
    )


def run_detect_overwrites(config, resources, pipelines):
    """run a task that detects files that are duplicated in multiple patches"""
    print(f"Detecting overwritten files in {config['resource']}")
    scripts.detect_overwrites(patches_dir=resources[config['resource']]['patches_dir'])


def run_download_mods(config, resources, pipelines):
    """run a task that downloads the history of the top K mods from CurseForge"""
    print("Downloading mods.")
    scripts.download_mods(
        mods_dirs=config['mods_dirs'],
        database_path=config['database_path'],
        mod_limit=config['mod_limit']
    )


def run_download_resource(config, resources, pipelines):
    """run a task that downloads git, curseforge, or url assets, or unpacks vanilla .jar files, to set up a resource"""
    print("Downloading resource.")
    scripts.download_resource(
        resources[config['resource']]
    )


def run_remove_resource(config, resources, pipelines):
    """run a task that removes all files associated with a resource"""
    print("Removing", config['folder'])

    folder_dirs = resources[config['resource']][config['folder']]

    # somewhat hacky normalization of dicts and scalars to lists of paths
    if type(folder_dirs) is dict:
        folder_dirs = list(folder_dirs.values())

    if type(folder_dirs) is not list:
        folder_dirs = [folder_dirs]

    for folder_dir in folder_dirs:
        folder_dir = os.path.expanduser(folder_dir)
        if os.path.exists(folder_dir):
            shutil.rmtree(os.path.dirname(folder_dir))


def run_run_subprocess(config, resources, pipelines):
    """run a task that executes a shell command within a folder in a resource"""
    print("Running subprocess.")
    print("cmd:", config['cmd'])
    print("pwd:", resources[config['resource']][config['folder']])
    scripts.run_subprocess(cmd=config['cmd'], cwd=resources[config['resource']][config['folder']])


def run_fix_mod_jsons(config, resources, pipelines):
    """run a task that validates and fixes mod.json files in patch directories"""
    print("Fixing mod.jsons in", config['resource'])
    scripts.fix_mod_jsons(patches_dir=resources[config['resource']]['patches_dir'])


def run_build_guis(config, resources, pipelines):
    """run a task that detects and builds GUIs from template files"""
    print("Building GUIs.")
    scripts.build_guis(
        resource_dir=resources[config['resource']]['pack_dir'],
        resource_patches_dir=resources[config['resource']]['patches_dir'],
        default_dir=resources[config['resource_default']]['pack_dir'],
        default_patches_dir=resources[config['resource_default']]['patches_dir'],
        debug_path=config.get('debug_path'))


def run_insert_placeholders(config, resources, pipelines):
    """run a task that adds default textures to a patches directory"""
    print("Inserting placeholders.")
    scripts.insert_placeholders(
        scale=config['scale'],
        resource_dir=resources[config['resource']]['pack_dir'],
        resource_patches_dir=resources[config['resource']]['patches_dir'],
        default_dir=resources[config['resource_default']]['pack_dir'])


def run_find_similar(config, resources, pipelines):
    """run a task that assists in texturing many similar files at once"""
    print("Finding similar images.")
    scripts.find_similar(
        scale=config['scale'],
        resource_patches_dir=resources[config['resource']]['patches_dir'],
        default_dir=resources[config['resource_default']]['pack_dir'],
        develop_dir=config.get('develop_dir'))


def run_detect_broken_animations(config, resources, pipelines):
    """run a task that assists in texturing many similar files at once"""
    print("Detecting broken animations.")
    scripts.detect_broken_animations(pack_dir=resources[config['resource']]['pack_dir'])
