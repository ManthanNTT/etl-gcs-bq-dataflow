import logging
from etlPipeline import csvIngestionPipeline
# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    logging.getLogger().setLevel(logging.INFO)
    print('PyCharm')
    csvIngestionPipeline.run()

