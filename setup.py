"""Python setup.py for sms-activate-email package"""
import io
import os
from setuptools import find_packages, setup


def read(*paths, **kwargs):
    content = ""
    with io.open(
        os.path.join(os.path.dirname(__file__), *paths),
        encoding=kwargs.get("encoding", "utf8"),
    ) as open_file:
        content = open_file.read().strip()
    return content


setup(
    name="sms-activate-email",
    version=read("sms_activate_email", "VERSION"),
    description="SMS-Activate Email API",
    long_description=read("README.md"),
    long_description_content_type="text/markdown",
    packages=find_packages(exclude=["tests", ".github"]),
    install_requires=[
        'setuptools~=68.2.0',
        'requests~=2.31.0'
    ],
    package_data={"sms_activate_email": ["VERSION"]}
)
