import os

from resource_wrangler.gui_builder import detect_regions, build_gui
from resource_wrangler.main import run

minor_versions = [16, 15, 12, 11, 10, 8, 7, 6, 5]


def test_gui_builder():
    template_dir = "/Users/michael/graphics/fanver/Resource-Wrangler/resource_wrangler/configs/gui_templates/"

    test_path = "/Users/michael/graphics/fanver/Templates/python_package/app_test.png"
    colossal_gui_path = "/Users/michael/graphics/default/Modded-1.15.x/Colossal_Chests/assets/colossalchests/textures/gui/colossal_chest.png"

    default_template_dir = os.path.join(template_dir, "default")
    fanver_wood_template_dir = os.path.join(template_dir, "fanver_wood")

    regions, size = detect_regions(
        default_gui_path=colossal_gui_path,
        default_template_dir=default_template_dir,
        debug_path=test_path)

    output_image = build_gui(
        regions=regions,
        size=size,
        resource_template_dir=fanver_wood_template_dir)

    output_image.save(test_path)


def port_complete_graph(resource_pack_name):
    import itertools
    import timeit

    # reverse-order so that newer textures get priority
    mc_versions = [f'1.{minor_version}.x' for minor_version in reversed(sorted(minor_versions))]
    pipeline = []
    for from_version, to_version in itertools.combinations_with_replacement(mc_versions, r=2):
        pipeline.append({
            "task": "port_patches",
            "default_prior": f"default-modded-{from_version}",
            "default_post": f"default-modded-{to_version}",
            "resource_prior": f"{resource_pack_name}-modded-{from_version}",
            "resource_post": f"{resource_pack_name}-modded-{to_version}",
            "action": "copy"
        })
        pipeline.append({
            'task': 'merge_patches',
            'resource': f'{resource_pack_name}-modded-{to_version}'
        })
        if from_version != to_version:
            pipeline.append({
                "task": "port_patches",
                "default_prior": f"default-modded-{to_version}",
                "default_post": f"default-modded-{from_version}",
                "resource_prior": f"{resource_pack_name}-modded-{to_version}",
                "resource_post": f"{resource_pack_name}-modded-{from_version}",
                "action": "copy"
            })
            pipeline.append({
                'task': 'merge_patches',
                'resource': f'{resource_pack_name}-modded-{from_version}'
            })

    elapsed_time = timeit.Timer(
        lambda: run(
            f"{resource_pack_name}_complete_port",
            pipelines={f"{resource_pack_name}_complete_port": pipeline}), 'gc.enable()'
    ).timeit(number=1)

    print(f"Elapsed time: {elapsed_time}")


port_complete_graph("fanver")
# port_complete_graph("jstr")

