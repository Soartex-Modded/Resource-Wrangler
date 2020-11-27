import argparse
import os
import shutil

from resource_wrangler.scripts.deploy import universal_build, universal_deploy


parser = argparse.ArgumentParser(description='Deploy a universal resource pack.')
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

print(f">>>> Deploying {args.pack} universal 1.{args.minor_version}.x pack")
universal_deploy(
    pack=args.pack,
    minor_version=args.minor_version,
    pack_dir=output_dir)
