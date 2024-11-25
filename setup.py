import setuptools

REQUIRED_PACKAGES = [
    "apache-beam[gcp]==2.42.0",
]

setuptools.setup(
    name='etl-gcs-bq',
    version='1.0',
    author="ETL",
    author_email="abc@xyz.com",
    url="https://hahaha.com",
    install_requires=REQUIRED_PACKAGES,
    packages=setuptools.find_packages()
)