from random import random
import cockroach_manager
import arg_manager
import time
import psycopg2
import psycopg2.extras
import uuid
import numpy
from faker import Faker
from faker.providers import person


if __name__ == '__main__':
    psycopg2.extras.register_uuid()
    fake = Faker()

    NUMBER_OF_USERS_TO_INSERT = 100
    NUMBER_OF_ORGANISATIONS_PER_USER = 100

    arg_mgr = arg_manager.ArgManager()

    connect_dict =     {
        "user": arg_mgr.args['USER'],
        "host": arg_mgr.args['HOST'],
        "port": arg_mgr.args['PORT'],
        "dbname": arg_mgr.args['DBNAME'],
        "sslrootcert": arg_mgr.args['SSLROOTCERT']
    }

    crdb = cockroach_manager.CockroachManager(connect_dict, True)
    cursor = crdb.connection.cursor()
    cursor.execute('select crdb_internal.node_id(), gateway_region()')
    cluster_node, gateway_region = cursor.fetchone()
    application_name = 'MultiRegionTest_GatewayRegion:{}_Node:{}'.format(gateway_region, cluster_node)
    cursor.execute('SET application_name = %s',(application_name,))

    execution_time_per_insert_users = []
    execution_time_per_insert_organisations = []
    user_insert_stmnt = 'INSERT INTO users (id, auth_id, first_name, last_name, email) VALUES (%s,%s,%s,%s,%s) RETURNING id;'
    organisation_insert_stmnt = 'INSERT INTO organisations (id, name, subdomain, workspace_type, creator) VALUES (%s,%s,%s,%s,%s) RETURNING id;'

    for user in range(NUMBER_OF_USERS_TO_INSERT):
        id = uuid.uuid4()
        auth_id = fake.swift11()
        first_name = fake.first_name()
        last_name = fake.last_name()
        email = fake.email()
        tic=time.perf_counter()
        cursor.execute(user_insert_stmnt, (id, auth_id, first_name, last_name, email))
        execution_time_per_insert_users.append(time.perf_counter()-tic)
        user_id = cursor.fetchone()[0]
        print(user_id)
        for org in range(NUMBER_OF_ORGANISATIONS_PER_USER):
            id = uuid.uuid4()
            name = fake.text(10)
            subdomain = fake.text(60)
            workspace_type = fake.text(10)
            tic=time.perf_counter()
            cursor.execute(organisation_insert_stmnt, (id, name, subdomain, workspace_type, user_id))
            execution_time_per_insert_organisations.append(time.perf_counter()-tic)

    a = numpy.array(execution_time_per_insert_users)
    print("User Insert Execution Times For Region {}\tp50: {}\tp95: {}\tp99: {}".format(gateway_region, round(numpy.percentile(a, 50),5), round(numpy.percentile(a,95),5), round(numpy.percentile(a,99),5)))
    a = numpy.array(execution_time_per_insert_organisations)
    print("Organisation Insert Execution Times For Region {}\tp50: {}\tp95: {}\tp99: {}".format(gateway_region, round(numpy.percentile(a, 50),5), round(numpy.percentile(a,95),5), round(numpy.percentile(a,99),5)))
   
    

