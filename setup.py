import setuptools

REQUIRED_PACKAGES = [
    "apache-beam[gcp]",
    "apache_beam[dataframe]",
    "google-cloud-storage",
    "google-cloud-bigquery"
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