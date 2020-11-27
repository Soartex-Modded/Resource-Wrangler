import os
import argparse
from resource_wrangler.scripts.deploy import universal_build


parser = argparse.ArgumentParser(description='Build a universal resource pack.')
parser.add_argument('pack', help='"fanver" or "jstr"')
parser.add_argument('minor_version', type=int)

args = parser.parse_args()
pack = args.pack
minor_version = args.minor_version
output_dir = os.path.expanduser(f'~/graphics_merged/{pack}/universal-1.{minor_version}.x')

universal_build(pack, minor_version, output_dir)
