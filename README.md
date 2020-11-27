# Resource Wrangler
This is a Python package containing scripts for working on repositories of resource pack patches, such as [Soartex-Modded-1.12.x](https://github.com/Soartex-Modded/Modded-1.12.x/) or [JSTR-Modded-1.12.x](https://github.com/John-Smith-Modded/JSTR-Modded-1.12.x).

```python
# example python usage
from resource_wrangler import scripts
scripts.merge_patches("~/graphics/fanver/Modded-1.12.x/","~/graphics-merged/fanver/Modded-1.12.x/",pack_format=3)
```

## Pipelines and Resources
The package also has a "pipeline" system to run multiple scripts sequentially with preset paths.   

```shell script
wrangle_resource 1.12_merge_fanver
``` 
This terminal command runs the `1.12_merge_fanver` pipeline. 
A pipeline runs multiple tasks sequentially. 
Each task runs a script with filesystem paths pulled from resources.
Resources contain paths to a patch directory, pack directory, git remote, locations of mod directories, etc.  

Feel free to edit pipelines and resources in [resource_wrangler/configs](resource_wrangler/configs) to your liking. 

One useful terminal command is `wrangle_resource 1.12_dev_soartex`.
This pipeline merges patches, creates symlinks to the merged pack from your minecraft instances, and starts a file-system watcher that re-applies changes made in the patches repository to the merged resource pack.
While the terminal session is running, any edits made to the patch repository will appear [when you refresh assets with F3+T](https://minecraft.gamepedia.com/Debug_screen#More_debug-keys) in-game. 

## Installation
1. Install Python
    - at least version 3.6
    - If using an installer, be sure to enable "Add Python 3.x to PATH"
2. Install Git
    - Windows: consider 'Git for Windows'
    - Mac or Linux: try typing `git` in the terminal 
2. Run the following in the terminal.
```shell script
git clone git@github.com:Soartex-Modded/Resource-Wrangler.git
cd Resource-Wrangler
pip3 install -r requirements.txt
pip3 install -e .
````
3. Edit any relevant paths in [resources.toml](resource_wrangler/configs/resources.toml) to suit your filesystem. 


## Scripts

### Extract Default
Unzip resources from a list of folder paths containing mod jars.

### Merge Patches
Merge mod patches (soartex, invictus, default, jstr, etc.) into a single resource pack.

### Link Resources
Create the symbolic links described in the resource `link_dirs` to the `pack_dir`.

### Watch Changes
Script to live-maintain multiple resource packs built from mod patches, from multiple repositories of mod patches.  

### Port Patches
Use MD5 hashes to detect identical files between two different resources.
Then port textures from one resource to the other, based on the discovered mapping.

### Prune Files
Delete files from a directory of mod patches that are not present in a merged default pack.
This task does not delete files from a patch if no textures from the patch are detected in the merged default pack.
This task moves files into a temporary directory, instead of deleting them.

### Download Mods
Uses the CurseForge api to download the top k most downloaded mods for each specified minecraft version into a mods folder.

### Download Resource
Clones or downloads the necessary assets from a git repository or CurseForge.
The default resources.toml contains all the necessary info for automatically collecting all of the resources.

### Detect Overwrites
Log files that are present in multiple patches.

### Fix mod.json
Logs inconsistencies and enforces proper formatting in mod.json files.

### Build GUIs
Detects templates in default GUI files and uses a bank of resource pack textures to reconstruct textured versions.

### Insert Placeholders
Inserts resized textures prefixed with `__default_` for any untextured assets into the patches directories they belong in.

### Find Similar
Creates a workspace containing textures similar to an example. 
Once you finish texturing assets in the workspace, they are moved into the patches directory.
If the watch changes script is running, the merged resource pack will also be updated with your changes. 

### Run Pipeline
A task that runs another pipeline by name.
