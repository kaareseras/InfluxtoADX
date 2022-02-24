# InfluxtoADX
This code will copy Home Assistant data from local InfluxDB to Azure Data Explorer.

After a deployment of the Azure Data Explorer integration, users like to have their historical data migrated to ADX. This code will retrieve the data and write it to Azure Data Explorer

The same Service Principal can be used as in the integration [Home Assistant ADX integration](https://www.home-assistant.io/integrations/azure_data_explorer/) <-- go here for instructions for setting up ADX and service principal

When runing, use folowing enviroment variables in a .env file

```
CLUSTER=ingest_uri_for_adx_cluster
CLIENT_ID=Service_Principal_Client_ID
CLIENT_SECRET=ervice_Principal_Secret_Value
AUTHORITY_ID=Service_Principal_Azure_subsciption_ID
DATABASE_NAME=ADX_Database_Name
MAPPING=ADX_Mapping_Name
TABLE_NAME=ADX_Table_Name
IP=Influx_DB_IP_Address
```

Code is also avaiable as a docker image, run it with this command (ensure to have the .env file in same lib as command is executed from):

```
sudo docker run -d --env-file .env  --name influxtoadx --network host kaareseras/influxtoadx:latest
```
Follow along with the ingestion using this docker command:
```
sudo docker logs --follow influxtoadx
```

In ADX cluster, Create Folowing Table and Importmapping:

```
// Create table command
////////////////////////////////////////////////////////////
.create table ['import']  (['time']:datetime, ['freindly_name']:string, ['entity_id']:string, ['value']:real, ['unit']:string)

// Create mapping command
////////////////////////////////////////////////////////////
.create table ['import'] ingestion json mapping 'import_mapping' '[{"column":"time", "Properties":{"Path":"$[\'time\']"}},{"column":"freindly_name", "Properties":{"Path":"$[\'freindly_name\']"}},{"column":"entity_id", "Properties":{"Path":"$[\'entity_id\']"}},{"column":"value", "Properties":{"Path":"$[\'value\']"}},{"column":"unit", "Properties":{"Path":"$[\'unit\']"}}]'
```

