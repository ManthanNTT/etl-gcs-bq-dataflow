import argparse
import json

import apache_beam as beam

from apache_beam.io.gcp.bigquery_tools import parse_table_schema_from_json
from apache_beam.io.gcp import bigquery
from google.cloud import storage


storage_client = storage.Client()

def readConfig(bucketName, filename):
    bucket = storage_client.get_bucket(bucketName)
    blob = bucket.blob(filename)
    content = blob.download_as_string()
    json_object = json.loads(content)
    return json_object


class PrintRecords(beam.DoFn):
    def process(self, record):
        print("ParDo --> ",record)

class ValidateAndConvertFn(beam.DoFn):

    def __init__(self, data_conf_headers):
        self.data_conf_headers = data_conf_headers

    def process(self, element):

        data_dict = {}
        for i, value in enumerate(element):
            key = self.data_conf_headers[i]
            data_dict[key] = value

        # print("validation --> ", data_dict)
        yield data_dict    #json.dumps(data_dict) was not working, BQ expects dictionary instead of JSON object  # Assuming JSONObject import


def run(argv=None, self=None):
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--bucket",
        dest="BUCKET",
        help="GCS Configuration Bucket Name",
    )

    parser.add_argument(
        "--envConfigFolder",
        dest="ENV_CONFIG_FOLDER",
        help="GCS Environment Configuration Folder",
    )

    parser.add_argument(
        "--dataConfigFolder",
        dest="DATA_CONFIG_FOLDER",
        help="GCS Data Configuration Folder",
    )

    known_args, pipeline_args = parser.parse_known_args(argv)

    envConfig = readConfig(known_args.BUCKET, known_args.ENV_CONFIG_FOLDER)
    print(envConfig)

    bucket_object = storage_client.get_bucket(known_args.BUCKET)
    dataConfigList = bucket_object.list_blobs(prefix=envConfig["entityDataConf"], delimiter="/")


    with beam.Pipeline(argv=pipeline_args) as p:

        print("Blobs:")
        for blob in dataConfigList:
            if blob.name.endswith(".json"):
                dataConfig = readConfig(known_args.BUCKET, blob.name)
                print(dataConfig)
                print(dataConfig["schema"])

                schema = json.dumps(dataConfig["schema"])
                tableSchema = parse_table_schema_from_json(schema)

                print(tableSchema)

                table_id = envConfig["projectId"] + ":" + dataConfig["dataset"] + "." + dataConfig["table"]

                input_file_path = "gs://"+ dataConfig["input_bucket"] + "/" + dataConfig["input_folder"] + dataConfig["entityName"] + ".csv"

                output_file_path = "gs://"+ dataConfig["input_bucket"]+ "/" + dataConfig["input_folder"] + "output/" + dataConfig["entityName"]

                csv_data = (
                    p
                    | f"ReadFromGCS{dataConfig["entityName"]}" >> beam.io.ReadFromText("gs://" + input_file_path, skip_header_lines=1)
                    | f"Parse CSV - {dataConfig["entityName"]}" >> beam.Map(lambda line: line.strip().split(','))
                )

                # csv_data | "csvRecords" >> beam.ParDo(PrintRecords())

                validated_json = ( csv_data | f"ValidateCSV-{dataConfig["entityName"]}" >> beam.ParDo(ValidateAndConvertFn(dataConfig["file-header"])))

                validated_json | f"WriteToGCS-{dataConfig["entityName"]}" >> beam.io.WriteToText(output_file_path, file_name_suffix=".json", shard_name_template='')#beam.io.WriteToText('gs://bkt-df-metadata-01/input-data/csv-ingestion-pipeline/output.json')

                # validated_json | "jsonRecords" >> beam.ParDo(PrintRecords())

                validated_json | f"WriteToBQ-{dataConfig["entityName"]}" >> beam.io.WriteToBigQuery(
                    table=table_id,
                    schema=tableSchema,
                    batch_size=100,
                    write_disposition=beam.io.BigQueryDisposition.WRITE_APPEND,
                    create_disposition=beam.io.BigQueryDisposition.CREATE_IF_NEEDED, #Test if we don't have tales created before, can table get created automatically with proper schema
                    custom_gcs_temp_location=envConfig["tempLocation"]
                )
