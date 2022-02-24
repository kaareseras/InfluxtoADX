import json
import io
import os
from datetime import date
from datetime import datetime
from datetime import timedelta
from shutil import ExecError
from influxdb import InfluxDBClient
from azure.kusto.data import KustoConnectionStringBuilder
from azure.kusto.data.data_format import DataFormat
from decouple import config

from azure.kusto.ingest import (
    QueuedIngestClient,
    IngestionProperties,
    FileDescriptor,
    BlobDescriptor,
    StreamDescriptor,
    KustoStreamingIngestClient,
    ManagedStreamingIngestClient,
    IngestionStatus,
)


class Serie:

    def __init__(self, initstr: str) -> None:
        #'\\ ,domain=sensor,entity_id=32b8e7_energy_totalstarttime'
        self.unit = initstr.split(',')[0]
        self.domain = initstr.split(',')[1].split('=')[1]
        self.entity_id = initstr.split(',')[2].split('=')[1]

        if '.' in self.unit:
            self.unit = None

class Point:

    def __init__(self, time, freindly_name, entity_id, value, unit) -> None:

        self.time = time
        self.freindly_name = freindly_name
        self.entity_id = entity_id
        self.value = value
        self.unit = unit

class kustoClient:
    def __init__(self) -> None:

        cluster = config('CLUSTER')

        # In case you want to authenticate with AAD application.
        client_id = config('CLIENT_ID')
        client_secret = config('CLIENT_SECRET')

        # read more at https://docs.microsoft.com/en-us/onedrive/find-your-office-365-tenant-id
        authority_id = config('AUTHORITY_ID')

        database_name = config('DATABASE_NAME')
        table_name = config('TABLE_NAME')
        
        # there are a lot of useful properties, make sure to go over docs and check them out
        self.ingestion_props = IngestionProperties(
            database=database_name,
            table=table_name,
            data_format=DataFormat.MULTIJSON,
            ingestion_mapping_reference=config('MAPPING'),
        )

        kcsb = KustoConnectionStringBuilder.with_aad_application_key_authentication(cluster, client_id, client_secret, authority_id)

        # Create it from a dm connection string
        #self.client = ManagedStreamingIngestClient.from_dm_kcsb(kcsb)
        self.client = QueuedIngestClient(kcsb)

    def ingest(self, points: list[Point]) -> None:
        json_string = ""

        for point in points:
            json_string += json.dumps(point.__dict__)
        
        bytes_stream = io.StringIO(json_string)
        stream_descriptor = StreamDescriptor(bytes_stream)

        try:
            self.client.ingest_from_stream(stream_descriptor, ingestion_properties=self.ingestion_props)
        except Exception as e:
            print(e)

    
def main():
    """
    Main function.
    """
    client = InfluxDBClient(host=config('IP'), port=8086)
    adx_client = kustoClient()

    client.switch_database('home_assistant')

    data_series = get_series(client)

    length = len(data_series)

    for count,data_serie in enumerate (data_series):
        print (f"Fetching {count}/{length}. {data_series[count].entity_id}")
        retrieve_data_for_serie(client, adx_client, data_serie)



        
    client.close()

def get_series(client: InfluxDBClient) -> list[Serie]:
    """
    Get a list with all series in DB.
    """

    serieslist = client.get_list_series()

    series = []

    for item in serieslist:
        series.append(Serie(item))

    return series

def retrieve_data_for_serie(client: InfluxDBClient,adx_client: kustoClient, serie: Serie) -> int:
    points = []
    today = date.today()
    midnight = datetime.combine(today, datetime.min.time())
    start_time = midnight 
    end_time = midnight + timedelta(hours=240)
    count = 0
    
    while start_time.year > 2018:
        try:
            points = retrieve_data_for_serie_for_time(client, serie, start_time, end_time)
        except Exception as e:           
            break

        try:
            if len(points) > 0:
                count += len(points)
                adx_client.ingest(points)
        except Exception as e:           
            print(e)



        start_time = start_time - timedelta(hours=240)
        end_time = end_time - timedelta(hours=240)

    print(f"Fetched: {serie.entity_id} -----  count:  {count}    ---------- type: {serie.unit}")
    
    return count

       


def retrieve_data_for_serie_for_time(client: InfluxDBClient, serie: Serie,start_time:datetime, end_time:datetime) -> list[Point]:

    _start_date_utc_zformat=start_time.strftime('%Y-%m-%dT%H:%M:%SZ')
    _end_date_utc_zformat=end_time.strftime('%Y-%m-%dT%H:%M:%SZ')

    print(f"fetching data for {start_time}", end = "\r")

    data_points = []

    try:
    
        if serie.unit is None:
            query = f'SELECT * FROM "{serie.entity_id}" WHERE time > \'{_start_date_utc_zformat}\' AND time <= \'{_end_date_utc_zformat}\' ;'
            result = client.query(query)
            points = result.get_points()

            for point in points:
                data_points.append(
                    Point(
                        point['time'],
                        point['friendly_name_str'],
                        point['entity_id'],
                        point['state'],
                        None

                    )
                )

        else:
            query = f'SELECT * FROM "{serie.unit}" WHERE entity_id = \'{serie.entity_id}\' AND time > \'{_start_date_utc_zformat}\' AND time <= \'{_end_date_utc_zformat}\' ;'
            result = client.query(query)
            points = result.get_points()

            if serie.unit == serie.entity_id:
                unit = None
            else:
                unit = serie.unit

            for point in points:
                data_points.append(
                    Point(
                        point['time'],
                        point['friendly_name_str'],
                        point['entity_id'],
                        point['value'],
                        unit
                    )
                )

    except Exception as e:
        print ("Error Fetching data with this query")
        print (query)
        print ("From Series")
        print (serie.__dict__)
        print ("with unit")
        print( serie.unit)
        raise Exception("error retrieveing data")

    return data_points
    


if __name__ == "__main__":
    main()








