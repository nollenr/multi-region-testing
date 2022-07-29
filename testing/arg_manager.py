import argparse
import logging
logger = logging.getLogger(__name__)

# https://stackoverflow.com/questions/15753701/how-can-i-pass-a-list-as-a-command-line-argument-with-argparse

class ArgManager():
  """Class to manage arguments, environment variables, etc.

    self.args is a dictionary with the following:

  """
  def __init__(self):

    # ARGUMENT PROCESSING
    parser = argparse.ArgumentParser(description='''Test Cockroach Manager (Connection Helper)''',
    epilog='''
      See the "README.md" in the repository for a full description of 
      the tool.''')

    connect_method = parser.add_mutually_exclusive_group()
    connect_method.add_argument('-s', '--Secrets',    dest='SECRETS', default=True,    help='Connect to Cockroach using AWS Secrets', action='store_true')
    connect_method.add_argument('-d', '--Dictionary', dest='DICT',    default = False, help='Connect to Cockroach using a Dictionary of values', action='store_true')

    parser.add_argument('-n', '--Name', dest='SECRET_NAME', help='When using AWS Secrets to connect to the cockroachDB, this is the name of the secret.')
    parser.add_argument('-g', '--RegionName', dest='REGION_NAME', default='us-west-2', help='When using AWS Secrets to connect to the CockroachDB, this is the name of the AWS region.')
    parser.add_argument('-u', '--User', dest='USER', default='ron', help='Database user')
    parser.add_argument('-o', '--Host', dest='HOST', default='internal-nollen-mr-hackathon-6x8.aws-us-west-2.cockroachlabs.cloud', help='Database host')
    parser.add_argument('-p', '--Port', dest='PORT', type=str, default='26257', help='Database port')
    parser.add_argument('-r', '--sslrootcert', dest='SSLROOTCERT', default='/home/ec2-user/Library/CockroachCloud/certs/nollen-mr-hackathon-ca.crt', help='SSL Root Cert')
    parser.add_argument('-b', '--DBname', dest='DBNAME', help='Database name')

    args = parser.parse_args()
    self.args = vars(args)
    
    if self.args['DICT']:
        self.args['SECRETS'] = False

