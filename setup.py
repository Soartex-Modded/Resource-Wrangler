from setuptools import setup

setup(
    package_data={
        "resource_wrangler.utilities": [
            "root/pack.png",
            "root/README.md"
        ],
        "resource_wrangler": [
            "configs/pipelines.toml",
            "configs/resources.toml"
        ]
    },
    entry_points={
        'console_scripts': [
            'wrangle_resource = resource_wrangler.main:main',
        ],
    },
)
