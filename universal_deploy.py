import argparse
import os
from resource_wrangler.scripts.deploy import universal_build, universal_deploy


parser = argparse.ArgumentParser(description='Deploy a universal resource pack.')
parser.add_argument('pack', help='"fanver" or "jstr"')
parser.add_argument('minor_version', type=int)
parser.add_argument('project_id', type=int)

args = parser.parse_args()
output_dir = os.path.expanduser(f'~/graphics_merged/{args.pack}/universal-1.{args.minor_version}.x')

# print(f">>>> Building Universal 1.{args.minor_version}.x Pack")
# universal_build(
#     pack=args.pack,
#     minor_version=args.minor_version,
#     output_dir=output_dir)

print(f">>>> Deploying Universal 1.{args.minor_version}.x Pack")
universal_deploy(
    pack=args.pack,
    minor_version=args.minor_version,
    pack_dir=output_dir,
    project_id=args.project_id)
