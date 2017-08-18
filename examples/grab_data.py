from __future__ import print_function

import csv
import sys
import yaml
from pyoanda import Client, TRADE
from pyoanda.exceptions import BadRequest
from datetime import datetime, timedelta

# Get my credentials
#
# YAML format, please see:
#    http://ess.khhq.net/wiki/YAML_Tutorial
#
# Config file for connecting to Oanda
#
# ACCOUNT_NUM: Integer number
# ACCOUNT_KEY: String of your account Key


with open("Config.yaml") as f:
    config = yaml.load(f.read())

client = Client(
    TRADE,
    account_id=config['ACCOUNT_NUM'],
    access_token=config['ACCOUNT_KEY']
)

DAYS = 50
GRAN = 'M15'
INST = 'EUR_JPY'
start = datetime.now() - timedelta(days=DAYS)

with open('data/data-set-{}-days.csv'.format(DAYS), 'w') as f:

    # We will map fields of the returned data to a more human readable format.
    mapFields = {}

    # Remove ""Mids", remove "Complete"
    mapFields['time'] = 'time'
    mapFields['lowMid'] = 'low'
    mapFields['complete'] = None
    mapFields['highMid'] = 'high'
    mapFields['openMid'] = 'open'
    mapFields['volume'] = 'volume'
    mapFields['closeMid'] = 'close'

    # Create the writer which will output to file
    writer = csv.DictWriter(f, fieldnames=mapFields.values())
    writer.writeheader()

    print('Fetching data from server...')
    print('-'*100)

    # Save the day to display progression output
    lastPct = 0.

    # Loop through every day and save the data found
    for day in range(DAYS):

        # Flush previously written output to file (Force write)
        f.flush()

        for _ in range(2):  # 24/12 hours

            # Find the start time from which to begin retrieving data
            end = start + timedelta(hours=12)

            # Create the dictionary which will be sent to PyOanda
            kwargs = dict(
                count=None,
                instrument=INST,
                granularity=GRAN,
                candle_format="midpoint",
                end=end.strftime("%Y-%m-%dT%H:%M:%S.%f%z"),
                start=start.strftime("%Y-%m-%dT%H:%M:%S.%f%z")
            )

            # Try to retrieve the data from Oanda
            try:

                # Fetch the data from Oanda
                candles = client.get_instrument_history(**kwargs)["candles"]

                # Remove 'Mid' from the key names
                for candle in candles:
                    for key, newKey in mapFields.items():

                        # Does the key exist in the candle?
                        if key in candle:

                            # Does the new key exist? (Delete it if not)
                            if newKey is None:
                                del candle[key]

                            # Change the key name
                            else:
                                candle[newKey] = candle.pop(key)

                # Try to fetch and write the data to the file
                writer.writerows(candles)

                # Print progress to the terminal
                pct = int(float(day) / DAYS * 100.0)
                # print pct
                if pct != lastPct:
                    strToWrite = '#'
                    if pct - lastPct > 1:
                        strToWrite *= int(pct-lastPct)

                    sys.stdout.write(strToWrite)
                    sys.stdout.flush()
                lastPct = pct

            # Catch any bad requests to Oanda and print the error
            except BadRequest as br:

                # print 'PyOanda suffered a bad request exception:', br
                pass

            # Catch generic exceptions
            except Exception as e:
                print('GrabData suffered an exception:', e)
                print('GrabData will now terminate!')
                print('-'*100)
                exit()

            # Reset the end time to the last candle retrieved
            start = end
print()
print('-'*100)
