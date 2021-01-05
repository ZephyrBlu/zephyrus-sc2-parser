import setuptools

with open('README.md', 'r') as fh:
    long_description = fh.read()

setuptools.setup(
    name="zephyrus-sc2-parser",
    version="0.2.30",
    author="Luke Holroyd",
    author_email="hello@zephyrus.gg",
    description="Parser for SC2 replay files",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/ZephyrBlu/zephyrus-sc2-parser",
    packages=setuptools.find_packages(),
    install_requires=[
        'requests',
        'mpyq',
        'pytz',
        # 'sc2_simulator',
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: Games/Entertainment :: Real Time Strategy",
    ],
    python_requires='>=3.6',
    entry_points={
        'console_scripts': ['s2_cli=zephyrus_sc2_parser.s2protocol_fixed.s2_cli:main']
    }
)
