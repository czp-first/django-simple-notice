# -*- coding: UTF-8 -*-
"""
@Summary : setup
@Author  : Rey
@Time    : 2022-04-02 14:00:57
"""
from notice import get_version
from setuptools import find_packages, setup


install_requires = ['Django >= 2.2',]

setup(
    name='django-simple-notice',
    version=get_version(),
    description='A very simple, yet powerful, Django notice application',
    long_description='A very simple, yet powerful, Django notice application',
    author='rey',
    author_email="zpcao.first@google.com",
    url='https://github.com/czp-first/django-simple-notice',
    license="MIT",
    packages=find_packages(exclude=["testproject", "testproject.*"]),
    classifiers=[
        "Environment :: Web Environment",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Topic :: Security",
        "Topic :: Internet :: WWW/HTTP",
        "Framework :: Django",
    ],
    include_package_data=True,
    zip_safe=False,
    install_requires=install_requires,
)