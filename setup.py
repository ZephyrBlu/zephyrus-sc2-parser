import setuptools

with open('README.md', 'r') as fh:
    long_description = fh.read()

setuptools.setup(
    name="zephyrus-sc2-parser",
    version="0.2.0",
    author="ZephyrBlu/Luke Holroyd",
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
        'pytest',
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: Games/Entertainment :: Real Time Strategy",
    ],
    python_requires='>=3.6',
)
