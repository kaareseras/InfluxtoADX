# InfluxtoADX
Copy Home Assistant InfluxDB data to Azure Data Explorer

use folowing enviroment variables in a .env file

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