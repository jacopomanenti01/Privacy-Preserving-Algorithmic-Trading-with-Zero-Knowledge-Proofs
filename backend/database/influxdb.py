import datetime 
import influxdb_client, os, time
import logging
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api_async import WriteApiAsync
from influxdb_client.client.write_api import SYNCHRONOUS
from influxdb_client.client.influxdb_client_async import InfluxDBClientAsync
import numpy as np
import uuid


from dotenv import load_dotenv

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


load_dotenv()

INFLUX_TOKEN = os.environ["INFLUXDB_ADMIN_TOKEN"]
INFLUX_ORG = os.environ["INFLUXDB_ORG"]
THROUGHPUT_BUCKET = os.environ["INFLUXDB_BUCKET"]
url = "http://" + os.getenv("INFLUX_ADDRESS", "localhost:8086")


async def get_influx_client() -> InfluxDBClientAsync:
    return InfluxDBClientAsync(url=url, token=INFLUX_TOKEN, org=INFLUX_ORG)

async def close_throughput(write_api: WriteApiAsync, datapoint: dict, price) -> None:
    print("\n ''''''''''''''''''''''''")
    print("\ncreating data point for closed position:")
    point = Point("closed_position")
    point = point.field('OrderID', str(datapoint.id))
    point = point.field('symbol', str(datapoint.symbol))

    point = point.field('OrderSide', datapoint.side)
    point = point.field('OrderQTY', float(datapoint.qty))
    point = point.field('ClosePrice', price)
    point = point.time(datapoint.submitted_at)
    
    await write_api.write(bucket=THROUGHPUT_BUCKET, org=INFLUX_ORG, record=point)
    print("New closed position data point saved on influxdb")




async def write_throughput(write_api: WriteApiAsync, datapoint: dict, price, is_updated) -> None:

    if not is_updated:
        print("\n ''''''''''''''''''''''''")
        print("\ncreating data point:")
        point = Point("orders")
        

        print(datapoint)
        
        point = point.field('OrderID', str(datapoint.id))
        point = point.field('symbol', datapoint.symbol)
        point = point.field('OrderClass', datapoint.order_class)
        point = point.field('OrderSide', datapoint.side)
        point = point.field('OrderQTY', float(datapoint.qty))
        point = point.field('TakeProfitID', str(datapoint.legs[0].id))
        point = point.field('TakeProfit', float(datapoint.legs[0].limit_price))
        point = point.field('StopLossID', str(datapoint.legs[1].id))
        point = point.field('StopLoss', float(datapoint.legs[1].stop_price))
        point = point.field('OrderPrice', price)

        point = point.time(datapoint.submitted_at)
        
        '''
        point = point.field('OrderLastUpdate', str(datapoint.updated_at.isoformat()))

        point = point.field('OrderHasBeenUpdated', bool(is_updated))
        point = point.field('OrderUpdatesCounts', float(0))

        point = point.field('NewTakeProfit', float(datapoint.legs[0].limit_price))
        point = point.field('NewLossProfit', float(datapoint.legs[1].stop_price))
        point = point.field('NewTakeProfitID', str(datapoint.legs[0].id))
        point = point.field('NewLossProfitID', str(datapoint.legs[1].id))
        '''

        await write_api.write(bucket=THROUGHPUT_BUCKET, org=INFLUX_ORG, record=point)
        print("New data point saved on influxdb")

    elif is_updated:
        print("Trying to update existing datapoint")
        print(f"\n{datapoint}")

        old_take_id = str(datapoint[0].replaces)
        old_stop_id = str(datapoint[1].replaces)

        new_take_id = str(datapoint[0].id)
        new_stop_id = str(datapoint[1].id)

        new_take = float(datapoint[0].limit_price)
        new_stop = float(datapoint[1].stop_price)


        query = f'''
        from(bucket: "{THROUGHPUT_BUCKET}")
            |> range(start: -24h)
            |> filter(fn: (r) => r._measurement == "orders")
            |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
            |> filter(fn: (r) => r.TakeProfitID == "{old_take_id}")
            |> yield(name: "last")
        '''

        print(f"old take profit id {old_take_id}")
        print(f"new take profit id {new_take_id}")
        client = await get_influx_client()
        query_api = client.query_api()

        result = await query_api.query_data_frame(query=query)

        if not result.empty:
            take_profit = float(result["TakeProfit"].iloc[0])
            stop_loss = float(result["StopLoss"].iloc[0])
        elif result.empty:
            query = f'''
        from(bucket: "{THROUGHPUT_BUCKET}")
            |> range(start: -24h)
            |> filter(fn: (r) => r._measurement == "bracket_updates")
            |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
            |> filter(fn: (r) => r.NewTakeProfitID == "{old_take_id}")
            |> yield(name: "last")
        '''
            result = await query_api.query_data_frame(query=query)
            take_profit = float(result["NewTakeProfit"].iloc[0])
            stop_loss = float(result["NewStopLoss"].iloc[0])


        point = Point("bracket_updates") \
        .field('symbol', datapoint[0].symbol)\
        .field('OrderSide', datapoint[0].side)\
        .field("OldTakeProfitID",old_take_id)\
        .field("OldStopLossID",old_stop_id)\
        .field("OldTakeProfit",take_profit)\
        .field("OldStopLoss",stop_loss)\
        .field("NewTakeProfitID", new_take_id)\
        .field("NewStopLossID", new_stop_id)\
        .field("NewTakeProfit", new_take)\
        .field("NewLossProfit", new_stop)\
        .field('OrderLastUpdate', str(datapoint[0].updated_at.isoformat()))

        await write_api.write(bucket=THROUGHPUT_BUCKET, org=INFLUX_ORG, record=point)
        
        print("Datapoint updated")

        print("Closing influxDB client")
        await client.close()        
        print("InfluxDB client closed")

        





