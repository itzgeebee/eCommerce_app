from setuptools import find_packages, setup


setup(
    name="online_store",
    version="1.0.0",
    description="An online store",
    author="Gideon Balogun",
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        "flask"
    ]
)