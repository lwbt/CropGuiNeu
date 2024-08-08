from setuptools import setup, find_packages

# TODO
# # Maps empty string to 'source' directory
# package_dir = {'': 'source'}
# # Search for packages within 'source'
# packages = find_packages(where='source')

setup(
    name="crop_gui_neu",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        "PyGObject",
    ],
    entry_points={
        "console_scripts": [
            "crop_gui_neu=crop_gui_neu.gui:main",
        ],
    },
    author="Benjamin Tegge",
    # TODO
    # author_email="your.email@example.com",
    description="A simple GTK application to crop JPEG images",
    long_description=open("README.adoc").read(),
    long_description_content_type="text/asciidoc",
    url="https://github.com/lwbt/GropGuiNeu",
    license="MIT",
)
