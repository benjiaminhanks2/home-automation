import pprint
import argparse
from datetime import datetime, timedelta

import pandas

import config
from data_source.home_automation.DataExtractor import DataExtractor


argparse = argparse.ArgumentParser()
argparse.add_argument("-o", "--output-file", required=True, dest="output_file",
                      help="Output file for the csv")
argparse.add_argument("-d", "--day-behind", required=True, dest="days_behind", type=int,
                      help="Days behind to be extracted in the file")
argparse.add_argument("-hg", "--hour-granularity", required=True, dest="hour_granularity", type=int,
                      help="Group by a day prediction number of hours")
args = vars(argparse.parse_args())

extractor = DataExtractor(config.url, config.sensors)

extracted_data = []
for day_behind in range(args['days_behind'], 0, -1):
    start_date = datetime.today() - timedelta(days=day_behind)
    print('Calculating for date: ' + start_date.strftime('%m-%d-%Y'))
    extracted_data = extracted_data + extractor.get_for(start_date, args['hour_granularity'])

dataframe = pandas.DataFrame(extracted_data).set_index('date')
pprint.pprint(dataframe.head())
print(dataframe.describe().T)

print('Writing csv file with name:' + args['output_file'])
dataframe.to_csv(args['output_file'], sep=',')