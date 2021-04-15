"""This module implements some facilities to deal with PostgreSQL database."""


from io import StringIO
import numpy as np
from os import listdir
from os.path import isfile, join
import pandas as pd
from pandas.errors import EmptyDataError
import psycopg2
from psycopg2.extras import Json, DictCursor
from tqdm import tqdm
from typing import Dict, List, Optional


from waad.utils.constants import DATABASE_FIELDS


class Database:
    """Defines an object to interact with a postgreSQL database.

    Attributes:
        host (str): Address of the host.
        port (str): Port on the host.
        user (str): User name.
        password (str): Password to access the `psql` instance.
        db_name (str): Name of the `psql` instance.
        connection (pg.connection): Connection object on the database.
    """

    def __init__(self, host: str, port: str, user: str, password: str, db_name: str):
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.db_name = db_name

        self.connection: psycopg2.connection

    def connect(self):
        self.connection = psycopg2.connect(user=self.user, password=self.password, host=self.host, port=self.port, database=self.db_name)

    def disconnect(self):
        self.connection.close()

    def commit(self):
        self.connection.commit()

    def execute_command(self, sql_command: str):
        self.connect()
        cursor = self.connection.cursor()

        cursor.execute(sql_command)
        self.commit()

        self.disconnect()

    def get_command(self, sql_command: str):
        self.connect()
        df = pd.read_sql_query(sql_command, self.connection)
        self.disconnect()
        return df

    def get_iterator_from_command(self, sql_command: str, chunk_size: int = 1000000):
        self.connect()
        cursor = self.connection.cursor(name='custom_cursor')
        cursor.itersize = chunk_size
        cursor.execute(sql_command)
        return cursor

    def create_table(self, table_name: str, fields=DATABASE_FIELDS):
        s = ", ".join([k + " " + v for k, v in fields.items()])
        sql_command = f"""CREATE TABLE {table_name} ({s});"""
        self.execute_command(sql_command)

    def drop_table(self, table_name: str):
        self.execute_command(f"DROP TABLE {table_name};")


class Table:
    def __init__(self, database: Database, table_name: str):
        """Defines an object to interact with a postgreSQL table.

        Attributes:
            database (Database): `Database` object containing the table.
            table_name (str): Name of the `psql` table.
        """

        self.database = database
        self.table_name = table_name

    def add_to_table(self, dataframe: pd.DataFrame):
        """Fastest way to insert a large amount of data in the table we found."""

        self.database.connect()
        cursor = self.database.connection.cursor()

        cpy = StringIO()
        for row in dataframe.values:
            # Insert repr() for `int` data    # Not really generic
            cpy.write(
                "\t".join(
                    [
                        repr(row[0]),
                        repr(row[1]),
                        row[2],
                        row[3],
                        row[4],
                        row[5],
                        row[6],
                        row[7],
                        row[8],
                        row[9],
                        row[10],
                        row[11],
                        row[12],
                        row[13],
                        row[14],
                        repr(row[15]),
                        row[16],
                        row[17],
                        row[18],
                        row[19],
                        row[20],
                        row[21],
                        row[22],
                        repr(row[23]),
                        row[24],
                        row[25],
                        row[26],
                        row[27],
                        row[28],
                        row[29],
                        row[30],
                        repr(row[31]),
                        row[32],
                        row[33],
                        repr(row[34]),
                        repr(row[35]),
                        row[36],
                        row[37],
                        row[38],
                        row[39],
                        row[40],
                        row[41],
                        row[42],
                    ]
                )
                + "\n"
            )

        cpy.seek(0)
        cursor.copy_from(cpy, self.table_name)
        self.database.commit()
        cursor.close()
        self.database.disconnect()

    def fill_table_from_ANSSI_dataset(self, folder_path: str):
        """Fill the ``Table`` object with all authentications contained in hosts computers.

        In the folder at ``folder_path`` there is one file per host. This method populate the table with all logs gathered by ``ORC``.
        """
        onlyfiles = [f for f in listdir(folder_path) if isfile(join(folder_path, f))]

        # Internal function to convert hidden string digits to int
        def to_int(x):
            if x.isdigit():
                return int(x)
            else:
                return -1

        pbar = tqdm(total=len(onlyfiles))
        while onlyfiles != []:
            current_file = onlyfiles.pop(0)

            CONVERTERS = {"LogonType": to_int, "IpPort": to_int}
            try:
                df_auth = pd.read_csv(join(folder_path, current_file), converters=CONVERTERS, low_memory=False)
                df_auth = df_auth.replace({np.nan: "?"})  # Replace ``np.nan`` by '?' to avoid PostgreSQL bug.
                self.add_to_table(df_auth)
                pbar.update(1)
            except EmptyDataError:
                print(current_file, " is empty")
                pbar.update(1)
                continue
        pbar.close()

    def execute_command(self, sql_command: str):
        self.database.execute_command(sql_command)

    def get_command(self, sql_command: str):
        df = self.database.get_command(sql_command)
        return df

    @staticmethod
    def and_join(input_dict: Optional[Dict] = None, input_list: Optional[List] = None):
        res = [] if input_list is None else input_list

        if input_dict is not None:
            for e, v in input_dict.items():
                if isinstance(v, list) or isinstance(v, tuple):
                    res.append(f"{e} IN {tuple(v)}")
                else:
                    res.append(f"{e} = '{v}'")

        return f"({' AND '.join(res)})"

    @staticmethod
    def or_join(input_dict: Optional[Dict] = None, input_list: Optional[List] = None):
        res = [] if input_list is None else input_list

        if input_dict is not None:
            for e, v in input_dict.items():
                if isinstance(v, list) or isinstance(v, tuple):
                    res.append(f"{e} IN {tuple(v)}")
                else:
                    res.append(f"{e} = '{v}'")

        return f"({' OR '.join(res)})"

    def custom_psql_request(self, input_dict: Dict, distinct: bool = False):
        """Create a custom request from input_dict.

        Args:
            input_dict (Dict): Columns to request with conditions. Inside every dictionnary in 'filters' list will be applied AND
                for values in it. Between 'filters' dictionnaries, it is an OR condition.
            distinct (bool): Boolean whether or not to apply DISTINCT on request.

        Examples:
            .. code-block:: python

                input_dict = {
                    'fields_to_request': ('targetusersid', 'targetusername', 'targetdomainname'),
                    'filters': [{'eventid': [4624, 4634]}]
                }
        """
        ands = [Table.and_join(condition) for condition in input_dict["filters"]]
        if isinstance(input_dict['fields_to_request'], str):
            fields_to_request = input_dict['fields_to_request']
        else:
            fields_to_request = ', '.join(input_dict['fields_to_request'])

        request = f"""
            SELECT {' DISTINCT ' if distinct else ''}
                {fields_to_request}
            FROM {self.table_name}
            {' WHERE ' + Table.or_join(input_list = ands) if ands != ['()'] else ''};
        """
        return request

    def get_custom_request(self, input_dict: Dict, distinct: bool = False):
        """Create and look for a custom request on ``Table``.

        Args:
            input_dict (Dict): Columns to request with conditions. Inside every dictionnary in 'filters' list will be applied AND
                for values in it. Between 'filters' dictionnaries, it is an OR condition.
            distinct (bool): Boolean whether or not to apply DISTINCT on request.

        Examples:
            .. code-block:: python

                input_dict = {
                    'fields_to_request': ('targetusersid', 'targetusername', 'targetdomainname'),
                    'filters': [{'eventid': [4624, 4634]}]
                }
        """
        return self.get_command(self.custom_psql_request(input_dict=input_dict, distinct=distinct))

    def delete_postgre_data(self):
        self.database.execute_command(f"DELETE FROM {self.table_name};")

    def create_index(self, column_name: str):
        self.database.execute_command(f"CREATE INDEX {self.table_name}_idx_{column_name} ON {self.table_name} USING btree ({column_name});")

    def drop_index(self, column_name: str):
        self.database.execute_command(f"DROP INDEX {self.table_name}_idx_{column_name};")

    def cluster(self, index_name: str):
        self.database.execute_command(f"CLUSTER {index_name} ON {self.table_name};")

    def query_column(self, column_name: str):
        return self.get_command(f"SELECT {column_name} FROM {self.table_name};")

    def get_field_filtered_on_value(self, field_name: str, field_value: str):
        return self.get_command(f"SELECT * FROM {self.table_name} WHERE {field_name} = '{field_value}';")

    def remove_duplicates(self, keys: List[str]):
        self.execute_command(
            f"""
            DELETE FROM {self.table_name} a USING (
                SELECT MIN(ctid) as ctid, {', '.join(keys)}
                    FROM {self.table_name}
                    GROUP BY {', '.join(keys)} HAVING COUNT(*) > 1
                ) b
            WHERE {' AND '.join([f'a.{k} = b.{k}' for k in keys])}
            AND a.ctid <> b.ctid
        """
        )

    def get_duplicates(self, keys: List[str]):
        return self.get_command(
            f"""
            SELECT * FROM (
                SELECT *, ROW_NUMBER() OVER(PARTITION BY {', '.join(keys)} ORDER BY {', '.join(keys)}) AS row_number
                FROM {self.table_name}
            ) temp WHERE row_number > 1
        """
        )
