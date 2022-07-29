import psycopg2
import logging
import json
import os

logger = logging.getLogger(__name__)

class CockroachManager():
    """A Note on connecting:

    Database Connection Parameters: https://www.postgresql.org/docs/current/libpq-connect.html#LIBPQ-CONNSTRING
    psycopg2 module: https://www.psycopg.org/docs/module.html#psycopg2.connect
    cockroachdb client connection docs: https://www.cockroachlabs.com/docs/stable/connection-parameters.html#additional-connection-parameters

    if you want to use secrets to connect to the database, you to have boto3, base64 and botocore.exceptions in the python environment (pip3 install boto3, etc.)
    To use secrets, you must have set up an IAM Policy and Role for the user who's secret and secret key has been defined and you must have run aws configure to set those values.

    To connect using a dictionary, the following is an example of the data you need in the dictionary
    {
        "user": "put your database username here",
        "password": "put your database password here",
        "host": "put your hostname or ip address here",
        "port": "26257",
        "dbname": "put your dbname here",
        "sslrootcert": "put the location and name of your ca.crt here"
    }    """
    def __init__(self, connect_dict, auto_commit=False):
        """Return a connection to CockroachDB
        
        auto_commit boolean:
            do you want the connection to be autocommited?
        """

        # if we have the password or if we're connecting via an sslcert, then we 
        # have all the info we need.  Otherwise, the password was not supplied
        # in the connect_dict (or via the secret) and we need to see if we 
        # can get the password from the envrionment
        if ("password" not in connect_dict) and ("sslcert" not in connect_dict):
            try:
                crdb_password = os.environ['password']
                connect_dict['password'] = crdb_password
            except:
                print('the "password" environment variable has not been set.')
                exit(1)

        # convert the incoming dictionary to a string (data source name)
        connect_dsn = ' '.join([(key + '='+ val) for (key, val) in connect_dict.items()])
        try:
            self.connection = psycopg2.connect(connect_dsn)
        # try:
        #     self.connection = psycopg2.connect(
        #         user = connect_dict['user'],
        #         host = connect_dict['host'],
        #         port =  connect_dict['port'],
        #         database =  connect_dict['database'],
        #         sslmode = connect_dict['sslmode'],
        #         sslrootcert =  connect_dict['sslrootcert'],
        #         sslcert = connect_dict['sslcert'],
        #         sslkey = connect_dict['sslkey']
        #     )
            self.connection.set_session(autocommit=auto_commit)
        except (Exception, psycopg2.DatabaseError) as error:
            logger.exception("Error while connecting to PostgreSQL", error) 
            self.connection = False
        
        logger.info('Successfully connected to the Cockroach Cluster')

    def __del__(self):
        self.connection.close()   

    @classmethod
    def use_secret(cls, secret_name, region_name, auto_commit=False):
        # TODO:  I do not seem to be getting error information when there are problems with the boto3 client
        # for a quick test, change the region and "nothing" happens... no error gets raised.  Not sure what's
        # going on 
        import boto3
        import base64
        from botocore.exceptions import ClientError
        import json
        """Return a secret from AWS Secret Manager"""

        # Create a Secrets Manager client
        try:
            session = boto3.session.Session()
            client = session.client(
                service_name='secretsmanager',
                region_name=region_name
            )
        except:
            logger.exception('Unable to establish a client.')
            raise

        if not client:
            logger.exception('Unable to establish a boto3 client')

      
        # In this sample we only handle the specific exceptions for the 'GetSecretValue' API.
        # See https://docs.aws.amazon.com/secretsmanager/latest/apireference/API_GetSecretValue.html
        # We rethrow the exception by default.

        try:
            get_secret_value_response = client.get_secret_value(
                SecretId=secret_name
            )
        except ClientError as e:
            logger.exception('Failure getting secret!')
            if e.response['Error']['Code'] == 'DecryptionFailureException':
                # Secrets Manager can't decrypt the protected secret text using the provided KMS key.
                # Deal with the exception here, and/or rethrow at your discretion.
                raise e
            elif e.response['Error']['Code'] == 'InternalServiceErrorException':
                # An error occurred on the server side.
                # Deal with the exception here, and/or rethrow at your discretion.
                raise e
            elif e.response['Error']['Code'] == 'InvalidParameterException':
                # You provided an invalid value for a parameter.
                # Deal with the exception here, and/or rethrow at your discretion.
                raise e
            elif e.response['Error']['Code'] == 'InvalidRequestException':
                # You provided a parameter value that is not valid for the current state of the resource.
                # Deal with the exception here, and/or rethrow at your discretion.
                raise e
            elif e.response['Error']['Code'] == 'ResourceNotFoundException':
                # We can't find the resource that you asked for.
                # Deal with the exception here, and/or rethrow at your discretion.
                raise e
            else:
                raise e
        else:
            # Decrypts secret using the associated KMS key.
            # Depending on whether the secret is a string or binary, one of these fields will be populated.
            if 'SecretString' in get_secret_value_response:
                secret = get_secret_value_response['SecretString']
            else:
                decoded_binary_secret = base64.b64decode(get_secret_value_response['SecretBinary'])
            return cls(json.loads(secret), auto_commit)

