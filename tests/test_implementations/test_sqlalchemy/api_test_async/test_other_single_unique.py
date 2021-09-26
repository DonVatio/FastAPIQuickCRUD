import asyncio
import json
import os
import uuid
from copy import deepcopy
from datetime import datetime, timezone, date, timedelta
from http import HTTPStatus
from urllib.parse import urlencode

from fastapi import FastAPI
from sqlalchemy import ARRAY, BigInteger, Boolean, CHAR, Column, Date, DateTime, Float, Integer, \
    JSON, LargeBinary, Numeric, SmallInteger, String, Text, Time, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import INTERVAL, JSONB, UUID
from sqlalchemy.orm import declarative_base, sessionmaker, synonym
from starlette.testclient import TestClient

from src.fastapi_quickcrud import sqlalchemy_to_pydantic
from src.fastapi_quickcrud.crud_router import crud_router_builder
from src.fastapi_quickcrud.misc.type import CrudMethods

TEST_DATABASE_URL = os.environ.get('TEST_DATABASE_ASYNC_URL',
                                   'postgresql+asyncpg://postgres:1234@127.0.0.1:5432/postgres')
app = FastAPI()

Base = declarative_base()
metadata = Base.metadata
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

engine = create_async_engine(TEST_DATABASE_URL,
                             future=True,
                             echo=True,
                             pool_use_lifo=True,
                             pool_pre_ping=True,
                             pool_recycle=7200)
async_session = sessionmaker(autocommit=False,
                             autoflush=False,
                             bind=engine,
                             class_=AsyncSession)


async def get_transaction_session() -> AsyncSession:
    async with async_session() as session:
        yield session



class UUIDTable(Base):
    __tablename__ = 'test_single_unique_table_async'
    id = Column(UUID(as_uuid=True), primary_key=True,
                server_default=text("uuid_generate_v4()"))
    bool_value = Column(Boolean, nullable=False, server_default=text("false"))
    bytea_value = Column(LargeBinary)
    char_value = Column(CHAR(10))
    date_value = Column(Date, server_default=text("now()"))
    float4_value = Column(Float, nullable=False,unique=True)
    float8_value = Column(Float(53), nullable=False, server_default=text("10.10"))
    int2_value = Column(SmallInteger, nullable=True)
    int4_value = Column(Integer, nullable=True)
    int8_value = Column(BigInteger, server_default=text("99"))
    interval_value = Column(INTERVAL)
    json_value = Column(JSON)
    jsonb_value = Column(JSONB(astext_type=Text()))
    numeric_value = Column(Numeric)
    text_value = Column(Text)
    time_value = Column(Time)
    timestamp_value = Column(DateTime)
    timestamptz_value = Column(DateTime(True))
    timetz_value = Column(Time(True))
    varchar_value = Column(String)
    array_value = Column(ARRAY(Integer()))
    array_str__value = Column(ARRAY(String()))

def setup_module(module):

    async def create_table():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)


    loop = asyncio.get_event_loop()
    loop.run_until_complete(create_table())




route_1 = crud_router_builder(db_session=get_transaction_session,
                              db_model=UUIDTable,
                              crud_methods=[
                                  CrudMethods.FIND_ONE,
                                  CrudMethods.FIND_MANY,
                                  CrudMethods.UPSERT_MANY,
                                  CrudMethods.UPDATE_ONE,
                                  CrudMethods.UPDATE_MANY,
                                  CrudMethods.PATCH_MANY,
                                  CrudMethods.PATCH_ONE,
                                  CrudMethods.DELETE_MANY,
                                  CrudMethods.DELETE_ONE,
                              ],
                              exclude_columns=['bytea_value', 'xml_value', 'box_valaue'],
                              async_mode=True,
                              prefix="/test",
                              tags=["test"]
                              )


route_2 = crud_router_builder(db_session=get_transaction_session,
                              db_model=UUIDTable,
                              crud_methods=[
                                  CrudMethods.UPSERT_ONE,
                                  CrudMethods.POST_REDIRECT_GET,
                              ],
                              exclude_columns=['bytea_value', 'xml_value', 'box_valaue'],
                              async_mode=True,
                              prefix="/test_2",
                              tags=["test"]
                              )


route_3 = crud_router_builder(db_session=get_transaction_session,
                              db_model=UUIDTable,
                              crud_methods=[
                                  CrudMethods.FIND_ONE,
                                  CrudMethods.POST_REDIRECT_GET,
                              ],
                              exclude_columns=['bytea_value', 'xml_value', 'box_valaue'],
                              async_mode=True,
                              prefix="/test_3",
                              tags=["test"]
                              )

[app.include_router(i) for i in [route_1, route_2, route_3]]

client = TestClient(app)


def test_get_one_data_and_create_one_data():
    headers = {
        'accept': 'application/json',
        'Content-Type': 'application/json',
    }
    data = '{"float4_value": 0.443}'
    response = client.post('/test_2', headers=headers, data=data)
    assert response.status_code == 201
    create_response = response.json()
    find_target = create_response['id']
    response = client.get(f'/test/{find_target}', headers=headers, data=data)
    assert response.status_code == 200
    assert response.json() == create_response
    create_response.pop('id')
    query_param = urlencode(create_response)
    response = client.get(f'/test/{find_target}?{query_param}', headers=headers, data=data)
    assert response.status_code == 200


def test_get_many_data_and_create_many_data():
    headers = {
        'accept': 'application/json',
        'Content-Type': 'application/json',
    }

    data = '''{ "insert": [ { "bool_value": true, "char_value": "string    ", "date_value": "2021-07-23", "float4_value": 0.12, "float8_value": 0, "int2_value": 0, "int4_value": 0, "int8_value": 0, "interval_value": 0, "json_value": {}, "jsonb_value": {}, "numeric_value": 0, "text_value": "string", "timestamp_value": "2021-07-23T02:38:24.963000", "timestamptz_value": "2021-07-23T02:38:24.963000+00:00","varchar_value": "string", "array_value": [ 0 ], "array_str__value": [ "string" ] }, { "bool_value": true, "char_value": "string    ", "date_value": "2021-07-23", "float4_value": 1.2, "float8_value": 0, "int2_value": 0, "int4_value": 0, "int8_value": 0, "interval_value": 0, "json_value": {}, "jsonb_value": {}, "numeric_value": 0, "text_value": "string", "timestamp_value": "2021-07-23T02:38:24.963000", "timestamptz_value": "2021-07-23T02:38:24.963000+00:00", "varchar_value": "string", "array_value": [ 0 ], "array_str__value": [ "string" ] },{ "bool_value": true, "char_value": "string    ", "date_value": "2021-07-23", "float4_value": 9.3, "float8_value": 0, "int2_value": 0, "int4_value": 0, "int8_value": 0, "interval_value": 0, "json_value": {}, "jsonb_value": {}, "numeric_value": 0, "text_value": "string", "timestamp_value": "2021-07-23T02:38:24.963000", "timestamptz_value": "2021-07-23T02:38:24.963000+00:00", "varchar_value": "string", "array_value": [ 0 ], "array_str__value": [ "string" ] } ] }'''
    data_dict = json.loads(data)['insert']
    response = client.post('/test', headers=headers, data=data)
    assert response.status_code == 201
    response_result = response.json()
    for index, value in enumerate(data_dict):
        res_result_by_index = response_result[index]
        for k, v in value.items():
            assert res_result_by_index[k] == v


def test_update_one_data():
    headers = {
        'accept': 'application/json',
        'Content-Type': 'application/json',
    }
    data = '{"float4_value": 0.98}'
    response = client.post('/test_2', headers=headers, data=data)
    assert response.status_code == 201
    create_response = response.json()
    created_primary_key = create_response['id']
    update_data = {"bool_value": False, "char_value": "string_u  ", "date_value": "2022-07-24", "float4_value": 12.7,
                   "float8_value": 10.5, "int2_value": 10, "int4_value": 10, "int8_value": 10, "interval_value": 3600,
                   "json_value": {'test': 'hello'}, "jsonb_value": {'test': 'hello'}, "numeric_value": 10,
                   "text_value": "string_update",
                   "timestamp_value": "2022-07-24T02:54:53.285000",
                   "timestamptz_value": "2022-07-24T02:54:53.285000+00:00", "varchar_value": "string",
                   "array_value": [1, 2, 3, 4, 5],
                   "array_str__value": ["test"], "time_value": "18:19:18", "timetz_value": "18:19:18+00:00"}
    query_param = urlencode(update_data)
    response = client.put(f'/test/{created_primary_key}?{query_param}', data=json.dumps(update_data))
    response_data = response.json()
    assert response_data
    for i in update_data:
        assert response_data[i] == update_data[i]


def test_update_many_data():
    headers = {
        'accept': 'application/json',
        'Content-Type': 'application/json',
    }

    data = {"insert": [{"bool_value": True, "char_value": "string", "date_value": "2021-07-24", "float4_value": 3.5,
                        "float8_value": 0, "int2_value": 0, "int4_value": 0, "int8_value": 0, "interval_value": 0,
                        "json_value": {}, "jsonb_value": {}, "numeric_value": 0, "text_value": "string",
                        "timestamp_value": "2021-07-24T02:54:53.285", "timestamptz_value": "2021-07-24T02:54:53.285Z",
                        "varchar_value": "string",
                        "array_value": [0],
                        "array_str__value": ["string"], "time_value": "18:18:18", "timetz_value": "18:18:18+00:00"},

                       {"bool_value": True, "char_value": "string", "date_value": "2021-07-24", "float4_value": 3.6,
                        "float8_value": 0, "int2_value": 0, "int4_value": 0, "int8_value": 0, "interval_value": 0,
                        "json_value": {}, "jsonb_value": {}, "numeric_value": 0, "text_value": "string",
                        "time_value": "18:18:18",
                        "timestamp_value": "2021-07-24T02:54:53.285",
                        "timestamptz_value": "2021-07-24T02:54:53.285Z",
                         "varchar_value": "string",
                        "array_value": [0], "array_str__value": ["string"], "timetz_value": "18:18:18+00:00"},

                       {"bool_value": True, "char_value": "string", "date_value": "2021-07-24", "float4_value": 3.7,
                        "float8_value": 0, "int2_value": 0, "int4_value": 0, "int8_value": 0, "interval_value": 0,
                        "json_value": {}, "jsonb_value": {}, "numeric_value": 0, "text_value": "string",
                        "timestamp_value": "2021-07-24T02:54:53.285",
                        "timestamptz_value": "2021-07-24T02:54:53.285Z",
                         "varchar_value": "string",
                        "array_value": [0], "array_str__value": ["string"], "time_value": "18:18:18",
                        "timetz_value": "18:18:18+00:00"},
                       ]}

    response = client.post('/test', headers=headers, data=json.dumps(data))
    assert response.status_code == 201
    insert_response_data = response.json()

    primary_key_list = [i['id'] for i in insert_response_data]
    params = {"bool_value____list": True,
              "char_value____str": 'string%',
              "char_value____str_____matching_pattern": 'case_sensitive',
              "date_value____from": "2021-07-22",
              "date_value____to": "2021-07-25",
              "float4_value____from": -1,
              "float4_value____to": 200,
              "float8_value____from": -1,
              "float8_value____to": 2,
              "float8_value____list": 0,
              "int2_value____from": -1,
              "int2_value____to": 9,
              "int2_value____list": 0,
              "int4_value____from": -1,
              "int4_value____to": 9,
              "int4_value____list": 0,
              "int8_value____from": -1,
              "int8_value____to": 9,
              "int8_value____list": 0,
              "interval_value____from": -1,
              "interval_value____to": 9,
              "interval_value____list": 0,
              "numeric_value____from": -1,
              "numeric_value____to": 9,
              "numeric_value____list": 0,
              "text_value____list": "string",
              "time_value____from": '18:18:18',
              "time_value____to": '18:18:18',
              "time_value____list": '18:18:18',
              "timestamp_value_value____from": "2021-07-24T02:54:53.285",
              "timestamp_value_value____to": "2021-07-24T02:54:53.285",
              "timestamp_value_value____list": "2021-07-24T02:54:53.285",
              "timestamptz_value_value____from": "2021-07-24T02:54:53.285Z",
              "timestamptz_value_value____to": "2021-07-24T02:54:53.285Z",
              "timestamptz_value_value____list": "2021-07-24T02:54:53.285Z",
              "time_value____from": '18:18:18+00:00',
              "time_value____to": '18:18:18+00:00',
              "time_value____list": '18:18:18+00:00',
              "varchar_value____str": 'string',
              "varchar_value____str_____matching_pattern": 'case_sensitive',
              "varchar_value____list": 'string',
              }
    from urllib.parse import urlencode
    query_string = urlencode(params)+f'&id____list={primary_key_list[0]}&id____list={primary_key_list[1]}&id____list={primary_key_list[2]}&float4_value____list=3.5&float4_value____list=3.6&float4_value____list=3.7'
    update_data = {"bool_value": False, "char_value": "string_u  ", "date_value": "2022-07-24", "float4_value": 10.58,
                   "float8_value": 10.5, "int2_value": 10, "int4_value": 10, "int8_value": 10, "interval_value": 3600,
                   "json_value": {'test': 'hello'}, "jsonb_value": {'test': 'hello'}, "numeric_value": 10,
                   "text_value": "string_update",
                   "timestamp_value": "2022-07-24T02:54:53.285000",
                   "timestamptz_value": "2022-07-24T02:54:53.285000+00:00",
                   "varchar_value": "string",
                   "array_value": [1, 2, 3, 4, 5],
                   "array_str__value": ["test"], "time_value": "18:19:18", "timetz_value": "18:19:18+00:00"}
    response = client.put(f'/test?{query_string}', data=json.dumps(update_data))
    # FIXME: update the unique column will conflict, it may not a issue, because it should input all columns, you can use the patch
    assert response.status_code == 409
    # response_data = response.json()
    # assert len(response_data) == 3
    # for k in response_data:
    #     for i in update_data:
    #         assert k[i] == update_data[i]


def test_patch_one_data():
    headers = {
        'accept': 'application/json',
        'Content-Type': 'application/json',
    }

    data = {"insert": [
        {"bool_value": True, "char_value": "string", "date_value": "2021-07-24", "float4_value": 5.78,
         "float8_value": 0, "int2_value": 0, "int4_value": 0, "int8_value": 0, "interval_value": 0,
         "json_value": {}, "jsonb_value": {}, "numeric_value": 0, "text_value": "string",
         "timestamp_value": "2021-07-24T02:54:53.285",
         "timestamptz_value": "2021-07-24T02:54:53.285Z", "varchar_value": "string",
         "array_value": [0], "array_str__value": ["string"], "time_value": "18:18:18",
         "timetz_value": "18:18:18+00:00"},
    ]}

    response = client.post('/test', headers=headers, data=json.dumps(data))
    assert response.status_code == 201
    insert_response_data = response.json()

    primary_key, = [i['id'] for i in insert_response_data]
    params = {"bool_value____list": True,
              "char_value____str": 'string%',
              "char_value____str_____matching_pattern": 'case_sensitive',
              "date_value____from": "2021-07-22",
              "date_value____to": "2021-07-25",
              "float4_value____from": -1,
              "float4_value____to": 500,
              "float4_value____list": 5.78,
              "float8_value____from": -1,
              "float8_value____to": 2,
              "float8_value____list": 0,
              "int2_value____from": -1,
              "int2_value____to": 9,
              "int2_value____list": 0,
              "int4_value____from": -1,
              "int4_value____to": 9,
              "int4_value____list": 0,
              "int8_value____from": -1,
              "int8_value____to": 9,
              "int8_value____list": 0,
              "interval_value____from": -1,
              "interval_value____to": 9,
              "interval_value____list": 0,
              "numeric_value____from": -1,
              "numeric_value____to": 9,
              "numeric_value____list": 0,
              "text_value____list": "string",
              "time_value____from": '18:18:18',
              "time_value____to": '18:18:18',
              "time_value____list": '18:18:18',
              "timestamp_value_value____from": "2021-07-24T02:54:53.285",
              "timestamp_value_value____to": "2021-07-24T02:54:53.285",
              "timestamp_value_value____list": "2021-07-24T02:54:53.285",
              "timestamptz_value_value____from": "2021-07-24T02:54:53.285Z",
              "timestamptz_value_value____to": "2021-07-24T02:54:53.285Z",
              "timestamptz_value_value____list": "2021-07-24T02:54:53.285Z",
              "time_value____from": '18:18:18+00:00',
              "time_value____to": '18:18:18+00:00',
              "time_value____list": '18:18:18+00:00',
              "varchar_value____str": 'string',
              "varchar_value____str_____matching_pattern": 'case_sensitive',
              "varchar_value____list": 'string',
              }
    from urllib.parse import urlencode
    query_string = urlencode(params)
    update_data = {"bool_value": False}
    response = client.patch(f'/test/{primary_key}?{query_string}', data=json.dumps(update_data))
    response_data = response.json()
    assert response_data
    for i in update_data:
        assert response_data[i] == update_data[i]
    params['bool_value____list'] = False
    query_string = urlencode(params)
    update_data = {"char_value": "string_u  "}
    response = client.patch(f'/test/{primary_key}?{query_string}', data=json.dumps(update_data))
    response_data = response.json()
    assert response_data
    for i in update_data:
        assert response_data[i] == update_data[i]
    params['char_value____str'] = "string_u  "
    query_string = urlencode(params)
    update_data = {"date_value": "2022-07-24"}
    response = client.patch(f'/test/{primary_key}?{query_string}', data=json.dumps(update_data))
    response_data = response.json()
    assert response_data
    for i in update_data:
        assert response_data[i] == update_data[i]
    params['date_value____from'] = "2022-07-23"
    params['date_value____to'] = "2022-07-25"
    query_string = urlencode(params)
    update_data = {"bool_value": False, "char_value": "string_u  ", "date_value": "2022-07-24", "float4_value": 1.70,
                   "float8_value": 10.5, "int2_value": 10, "int4_value": 10, "int8_value": 10, "interval_value": 3600,
                   "json_value": {'test': 'hello'}, "jsonb_value": {'test': 'hello'}, "numeric_value": 10,
                   "text_value": "string_update",
                   "timestamp_value": "2022-07-24T02:54:53.285000",
                   "timestamptz_value": "2022-07-24T02:54:53.285000+00:00", "varchar_value": "string",
                   "array_value": [1, 2, 3, 4, 5],
                   "array_str__value": ["test"], "time_value": "18:19:18", "timetz_value": "18:19:18+00:00"}
    response = client.patch(f'/test/{primary_key}?{query_string}', data=json.dumps(update_data))
    response_data = response.json()
    assert response_data
    for i in update_data:
        assert response_data[i] == update_data[i]


def test_patch_many_data():
    headers = {
        'accept': 'application/json',
        'Content-Type': 'application/json',
    }

    data = {"insert": [{"bool_value": True, "char_value": "string", "date_value": "2021-07-24", "float4_value": 0.91,
                        "float8_value": 0, "int2_value": 0, "int4_value": 0, "int8_value": 0, "interval_value": 0,
                        "json_value": {}, "jsonb_value": {}, "numeric_value": 0, "text_value": "string",
                        "timestamp_value": "2021-07-24T02:54:53.285", "timestamptz_value": "2021-07-24T02:54:53.285Z",
                        "varchar_value": "string",
                        "array_value": [0],
                        "array_str__value": ["string"], "time_value": "18:18:18", "timetz_value": "18:18:18+00:00"},

                       {"bool_value": True, "char_value": "string", "date_value": "2021-07-24", "float4_value": 0.92,
                        "float8_value": 0, "int2_value": 0, "int4_value": 0, "int8_value": 0, "interval_value": 0,
                        "json_value": {}, "jsonb_value": {}, "numeric_value": 0, "text_value": "string",
                        "time_value": "18:18:18",
                        "timestamp_value": "2021-07-24T02:54:53.285",
                        "timestamptz_value": "2021-07-24T02:54:53.285Z",
                         "varchar_value": "string",
                        "array_value": [0], "array_str__value": ["string"], "timetz_value": "18:18:18+00:00"},

                       {"bool_value": True, "char_value": "string", "date_value": "2021-07-24", "float4_value": 0.93,
                        "float8_value": 0, "int2_value": 0, "int4_value": 0, "int8_value": 0, "interval_value": 0,
                        "json_value": {}, "jsonb_value": {}, "numeric_value": 0, "text_value": "string",
                        "timestamp_value": "2021-07-24T02:54:53.285",
                        "timestamptz_value": "2021-07-24T02:54:53.285Z",
                         "varchar_value": "string",
                        "array_value": [0], "array_str__value": ["string"], "time_value": "18:18:18",
                        "timetz_value": "18:18:18+00:00"},
                       ]}

    response = client.post('/test', headers=headers, data=json.dumps(data))
    assert response.status_code == 201
    insert_response_data = response.json()

    primary_key_list = [i['id'] for i in insert_response_data]
    params = {
              "bool_value____list": True,
              "char_value____str": 'string%',
              "char_value____str_____matching_pattern": 'case_sensitive',
              "date_value____from": "2021-07-22",
              "date_value____to": "2021-07-25",
              "float4_value____from": -1,
              "float4_value____to": 500,
              "float8_value____from": -1,
              "float8_value____to": 2,
              "float8_value____list": 0,
              "int2_value____from": -1,
              "int2_value____to": 9,
              "int2_value____list": 0,
              "int4_value____from": -1,
              "int4_value____to": 9,
              "int4_value____list": 0,
              "int8_value____from": -1,
              "int8_value____to": 9,
              "int8_value____list": 0,
              "interval_value____from": -1,
              "interval_value____to": 9,
              "interval_value____list": 0,
              "numeric_value____from": -1,
              "numeric_value____to": 9,
              "numeric_value____list": 0,
              "text_value____list": "string",
              "time_value____from": '18:18:18',
              "time_value____to": '18:18:18',
              "time_value____list": '18:18:18',
              "timestamp_value_value____from": "2021-07-24T02:54:53.285",
              "timestamp_value_value____to": "2021-07-24T02:54:53.285",
              "timestamp_value_value____list": "2021-07-24T02:54:53.285",
              "timestamptz_value_value____from": "2021-07-24T02:54:53.285Z",
              "timestamptz_value_value____to": "2021-07-24T02:54:53.285Z",
              "timestamptz_value_value____list": "2021-07-24T02:54:53.285Z",
              "time_value____from": '18:18:18+00:00',
              "time_value____to": '18:18:18+00:00',
              "time_value____list": '18:18:18+00:00',
              "varchar_value____str": 'string',
              "varchar_value____str_____matching_pattern": 'case_sensitive',
              "varchar_value____list": 'string',
              }
    from urllib.parse import urlencode
    query_string = urlencode(
        params) + f'&id____list={primary_key_list[0]}&id____list={primary_key_list[1]}&id____list={primary_key_list[2]}&float4_value____list=0.91&float4_value____list=0.92&float4_value____list=0.93'

    update_data = {"bool_value": False, "char_value": "string_u  ", "date_value": "2022-07-24",
                   "float8_value": 10.5, "int2_value": 10, "int4_value": 10, "interval_value": 3600,
                   "json_value": {'test': 'hello'}, "jsonb_value": {'test': 'hello'}, "numeric_value": 10,
                   "text_value": "string_update",
                   "timestamp_value": "2022-07-24T02:54:53.285000",
                   "timestamptz_value": "2022-07-24T02:54:53.285000+00:00","varchar_value": "string",
                   "array_value": [1, 2, 3, 4, 5],
                   "array_str__value": ["test"], "time_value": "18:19:18", "timetz_value": "18:19:18+00:00"}
    response = client.patch(f'/test?{query_string}', data=json.dumps(update_data))
    response_data = response.json()
    assert len(response_data) == 3
    for k in response_data:
        for i in update_data:
            print(i)
            print(k[i])
            assert k[i] == update_data[i]


def test_delete_one_data():
    headers = {
        'accept': 'application/json',
        'Content-Type': 'application/json',
    }

    data = {"insert": [
        {"bool_value": True, "char_value": "string", "date_value": "2021-07-24", "float4_value": 2.54,
         "float8_value": 0, "int2_value": 0, "int4_value": 0, "int8_value": 0, "interval_value": 0,
         "json_value": {}, "jsonb_value": {}, "numeric_value": 0, "text_value": "string",
         "timestamp_value": "2021-07-24T02:54:53.285",
         "timestamptz_value": "2021-07-24T02:54:53.285",
         "varchar_value": "string",
         "array_value": [0], "array_str__value": ["string"], "time_value": "18:18:18",
         "timetz_value": "18:18:18+00:00"},
    ]}

    response = client.post('/test', headers=headers, data=json.dumps(data))
    assert response.status_code == 201
    insert_response_data = response.json()

    primary_key, = [i['id'] for i in insert_response_data]
    params = {"bool_value____list": True,
              "char_value____str": 'string%',
              "char_value____str_____matching_pattern": 'case_sensitive',
              "date_value____from": "2021-07-22",
              "date_value____to": "2021-07-25",
              "float4_value____from": -1,
              "float4_value____to": 500,
              "float4_value____list": 2.54,
              "float8_value____from": -1,
              "float8_value____to": 2,
              "float8_value____list": 0,
              "int2_value____from": -1,
              "int2_value____to": 9,
              "int2_value____list": 0,
              "int4_value____from": -1,
              "int4_value____to": 9,
              "int4_value____list": 0,
              "int8_value____from": -1,
              "int8_value____to": 9,
              "int8_value____list": 0,
              "interval_value____from": -1,
              "interval_value____to": 9,
              "interval_value____list": 0,
              "numeric_value____from": -1,
              "numeric_value____to": 9,
              "numeric_value____list": 0,
              "text_value____list": "string",
              "time_value____from": '18:18:18',
              "time_value____to": '18:18:18',
              "time_value____list": '18:18:18',
              "timestamp_value_value____from": "2021-07-24T02:54:53.285",
              "timestamp_value_value____to": "2021-07-24T02:54:53.285",
              "timestamp_value_value____list": "2021-07-24T02:54:53.285",
              "timestamptz_value_value____from": "2021-07-24T02:54:53.285Z",
              "timestamptz_value_value____to": "2021-07-24T02:54:53.285Z",
              "timestamptz_value_value____list": "2021-07-24T02:54:53.285Z",
              "time_value____from": '18:18:18+00:00',
              "time_value____to": '18:18:18+00:00',
              "time_value____list": '18:18:18+00:00',
              "varchar_value____str": 'string',
              "varchar_value____str_____matching_pattern": 'case_sensitive',
              "varchar_value____list": 'string',
              }
    from urllib.parse import urlencode
    query_string = urlencode(params)
    response = client.delete(f'/test/{primary_key}?{query_string}')
    assert response.status_code == 200
    assert response.headers['x-total-count'] == '1'


def test_delete_many_data():
    headers = {
        'accept': 'application/json',
        'Content-Type': 'application/json',
    }

    data = {"insert": [{"bool_value": True, "char_value": "string", "date_value": "2021-07-24", "float4_value": 0.875,
                        "float8_value": 0, "int2_value": 0, "int4_value": 0, "int8_value": 0, "interval_value": 0,
                        "json_value": {}, "jsonb_value": {}, "numeric_value": 0, "text_value": "string",
                        "timestamp_value": "2021-07-24T02:54:53.285", "timestamptz_value": "2021-07-24T02:54:53.285Z",
                         "varchar_value": "string",
                        "array_value": [0],
                        "array_str__value": ["string"], "time_value": "18:18:18", "timetz_value": "18:18:18+00:00"},

                       {"bool_value": True, "char_value": "string", "date_value": "2021-07-24", "float4_value": 0.876,
                        "float8_value": 0, "int2_value": 0, "int4_value": 0, "int8_value": 0, "interval_value": 0,
                        "json_value": {}, "jsonb_value": {}, "numeric_value": 0, "text_value": "string",
                        "time_value": "18:18:18",
                        "timestamp_value": "2021-07-24T02:54:53.285",
                        "timestamptz_value": "2021-07-24T02:54:53.285Z", "varchar_value": "string",
                        "array_value": [0], "array_str__value": ["string"], "timetz_value": "18:18:18+00:00"},

                       {"bool_value": True, "char_value": "string", "date_value": "2021-07-24", "float4_value": 0.877,
                        "float8_value": 0, "int2_value": 0, "int4_value": 0, "int8_value": 0, "interval_value": 0,
                        "json_value": {}, "jsonb_value": {}, "numeric_value": 0, "text_value": "string",
                        "timestamp_value": "2021-07-24T02:54:53.285",
                        "timestamptz_value": "2021-07-24T02:54:53.285Z", "varchar_value": "string",
                        "array_value": [0], "array_str__value": ["string"], "time_value": "18:18:18",
                        "timetz_value": "18:18:18+00:00"},
                       ]}

    response = client.post('/test', headers=headers, data=json.dumps(data))
    assert response.status_code == 201
    insert_response_data = response.json()

    primary_key_list = [i['id'] for i in insert_response_data]
    params = {
              "bool_value____list": True,
              "char_value____str": 'string%',
              "char_value____str_____matching_pattern": 'case_sensitive',
              "date_value____from": "2021-07-22",
              "date_value____to": "2021-07-25",
              "float4_value____from": -1,
              "float4_value____to": 500,
              "float8_value____from": -1,
              "float8_value____to": 2,
              "float8_value____list": 0,
              "int2_value____from": -1,
              "int2_value____to": 9,
              "int2_value____list": 0,
              "int4_value____from": -1,
              "int4_value____to": 9,
              "int4_value____list": 0,
              "int8_value____from": -1,
              "int8_value____to": 9,
              "int8_value____list": 0,
              "interval_value____from": -1,
              "interval_value____to": 9,
              "interval_value____list": 0,
              "numeric_value____from": -1,
              "numeric_value____to": 9,
              "numeric_value____list": 0,
              "text_value____list": "string",
              "time_value____from": '18:18:18',
              "time_value____to": '18:18:18',
              "time_value____list": '18:18:18',
              "timestamp_value_value____from": "2021-07-24T02:54:53.285",
              "timestamp_value_value____to": "2021-07-24T02:54:53.285",
              "timestamp_value_value____list": "2021-07-24T02:54:53.285",
              "timestamptz_value_value____from": "2021-07-24T02:54:53.285Z",
              "timestamptz_value_value____to": "2021-07-24T02:54:53.285Z",
              "timestamptz_value_value____list": "2021-07-24T02:54:53.285Z",
              "time_value____from": '18:18:18+00:00',
              "time_value____to": '18:18:18+00:00',
              "time_value____list": '18:18:18+00:00',
              "varchar_value____str": 'string',
              "varchar_value____str_____matching_pattern": 'case_sensitive',
              "varchar_value____list": 'string',
              }
    from urllib.parse import urlencode
    query_string = urlencode(
        params) + f'&id____list={primary_key_list[0]}&id____list={primary_key_list[1]}&id____list={primary_key_list[2]}&float4_value____list=0.875&float4_value____list=0.876&&float4_value____list=0.877'

    response = client.delete(f'/test?{query_string}')
    assert response.status_code == 200
    assert response.headers['x-total-count'] == '3'


def test_post_redirect_get_data():
    headers = {
        'accept': '*/*',
        'Content-Type': 'application/json',
    }

    change = {}

    bool_value_change = False
    char_value_change = "test"
    date_value_change = str(date.today() - timedelta(days=1))
    float8_value_change = 0.1
    int2_value_change = 100
    int8_value_change = 100
    interval_value_change = float(5400)
    json_value_change = {"hello": "world"}
    jsonb_value_change = {"hello": "world"}
    numeric_value_change = 19
    text_value_change = 'hello world'
    time_value_change = '18:18:18'
    timestamp_value_change = str(datetime.utcnow().isoformat())
    timestamptz_value_change = str(datetime.utcnow().replace(tzinfo=timezone.utc).isoformat())
    timetz_value_change = '18:18:18+00:00'
    varchar_value_change = 'hello world'
    array_value_change = [1, 2, 3, 4]
    array_str__value_change = ['1', '2', '3', '4']

    change['bool_value'] = bool_value_change
    change['char_value'] = char_value_change
    change['date_value'] = date_value_change
    change['float8_value'] = float8_value_change
    change['int2_value'] = int2_value_change
    change['int8_value'] = int8_value_change
    change['float4_value'] = 55.7
    change['int4_value'] = 4
    change['interval_value'] = interval_value_change
    change['json_value'] = json_value_change
    change['jsonb_value'] = jsonb_value_change
    change['numeric_value'] = numeric_value_change
    change['text_value'] = text_value_change
    change['time_value'] = time_value_change
    change['timestamp_value'] = timestamp_value_change
    change['timestamptz_value'] = timestamptz_value_change
    change['timetz_value'] = timetz_value_change
    change['varchar_value'] = varchar_value_change
    change['array_value'] = array_value_change
    change['array_str__value'] = array_str__value_change
    data_ = json.dumps(change)
    response = client.post('/test_3', headers=headers, data=data_, allow_redirects=True)
    assert response.status_code == HTTPStatus.OK
    response_data = response.json()
    assert 'id' in response_data
    for k, v in response_data.items():
        if k in change:
            if isinstance(v, str):
                v = v.strip()
            response_ = json.dumps(v).strip()
            request_ = json.dumps(change[k]).strip()
            assert request_ == response_
    return response_data



def test_upsert_one():
    headers = {
        'accept': 'application/json',
        'Content-Type': 'application/json',
    }
    data = '{"float4_value": 12.784}'
    response = client.post('/test_2', headers=headers, data=data)
    assert response.status_code == 201
    create_response = response.json()
    updated_data = {}
    for k,v in create_response.items():
        if k not in data:
            updated_data[k] = v
    updated_data['numeric_value'] = 100
    # conflict
    upsert_data = deepcopy(updated_data)
    upsert_data['on_conflict'] = {'update_columns':['numeric_value']}
    response = client.post('/test_2', headers=headers, data=json.dumps(dict(upsert_data, **json.loads(data))))
    assert response.status_code == 201

    # create
    response = client.post('/test_2', headers=headers, data=json.dumps(dict(updated_data, **json.loads(data))))
    assert response.status_code == 409


def teardown_module(module):
    async def create_table():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)

    loop = asyncio.get_event_loop()
    loop.run_until_complete(create_table())