# Multi-Region Testing
Originally built for a West SEssion Hackathon on Multi-Region

- [Multi-Region Testing](#multi-region-testing)
  - [Problem Statement](#problem-statement)
    - [Setup](#setup)
    - [Problem](#problem)
  - [Topology](#topology)
    - [High Level Topology](#high-level-topology)
    - [Detail Topology](#detail-topology)
  - [ERD](#erd)
- [The Details](#the-details)
  - [VPCs](#vpcs)
  - [EC2 Instances](#ec2-instances)
  - [Cockroach Cluster](#cockroach-cluster)
- [Using The Abstractions](#using-the-abstractions)

## Problem Statement
### Setup
A prospect has a set of tables that include
- parent-child tables
- many-to-many resolution tables

The prospect would like to have all of these tables be Region-By-Row (RBR) since the application and customers live in 3 distinct geographical regions.  

### Problem
When rows are inserted to the parent or child tables, all regions must be checked for uniqueness and membership.  We would like to keep data and queries local to one region to reduce latencies.



## Topology
### High Level Topology
![Topology](topology.drawio.png)
### Detail Topology
![Topology Detail](topology-detail.drawio.png)

## ERD
The starting Entity-Relationship-Diagram (ERD) is below.  
![Entity Relationship Diagram](erd.drawio.png)
The 3 tables I'm going to focus on are in red and initially they are all Regional-By-Row Tables.   The starting DDL for the tables is avilable [here](schema_starting.sql).  


# The Details

## VPCs
|Cloud Formation Stack Name|VPC Name|VPC Address Space|
|-------|---------|----------|
|nollen-multi-region-hackathon-vpc02|hackathon-vpc02|192.168.2.0/24|
|nollen-multi-region-hackathon-vpc03|hackathon-vpc03|192.168.3.0/24|
|nollen-multi-region-hackathon-vpc04|hackathon-vpc04|192.168.4.0/24|


## EC2 Instances
|Region|Name|Private IP|Public IP|PuTTY|
|-----|----|----|-----|----|
|eu-central-1 (Frankfurt)|nollen-hackathon-app-frankfurt|192.168.3.145|3.74.228.34|aws-euc1-app|
|ap-southeast-1 (Singapore)|nollen-hackathon-app-singapore|192.168.4.151|13.212.122.220|aws-aps1-app|
|us-west-2 (Oregon)|nollen-hackathon-app-oregon|192.168.2.135|35.91.33.160|aws-usw2-app|

## Cockroach Cluster
nollen-mr-hackathon

User: ron

US-WEST-2
```
cockroach sql --url "postgresql://ron:${mypass}@internal-nollen-mr-hackathon-6x8.aws-us-west-2.cockroachlabs.cloud:26257/defaultdb?sslmode=verify-full&sslrootcert=$HOME/Library/CockroachCloud/certs/nollen-mr-hackathon-ca.crt"
```

AP-SOUTHEAST-2
```
cockroach sql --url "postgresql://ron:${mypass}@internal-nollen-mr-hackathon-6x8.aws-ap-southeast-1.cockroachlabs.cloud:26257/defaultdb?sslmode=verify-full&sslrootcert=$HOME/Library/CockroachCloud/certs/nollen-mr-hackathon-ca.crt"
```

EU-CENTRAL-1
```
cockroach sql --url "postgresql://ron:${mypass}@internal-nollen-mr-hackathon-6x8.aws-eu-central-1.cockroachlabs.cloud:26257/defaultdb?sslmode=verify-full&sslrootcert=$HOME/Library/CockroachCloud/certs/nollen-mr-hackathon-ca.crt"
```

```
select  node_id, 
        locality,
        ranges,
        leases
from    crdb_internal.gossip_nodes
order by locality;
```

|  node_id |                                                    locality                                                     | ranges | leases|
|----------|-----------------------------------------------------------------------------------------------------------------|--------|---------|
|        1 | region=aws-ap-southeast-1,az=aws-ap-southeast-1a,dns=cockroachdb-0.cockroachdb.ap-southeast-1.svc.cluster.local |     29 |      7|
|        8 | region=aws-ap-southeast-1,az=aws-ap-southeast-1b,dns=cockroachdb-1.cockroachdb.ap-southeast-1.svc.cluster.local |     30 |      5|
|        9 | region=aws-ap-southeast-1,az=aws-ap-southeast-1c,dns=cockroachdb-2.cockroachdb.ap-southeast-1.svc.cluster.local |     27 |      6|
|        6 | region=aws-eu-central-1,az=aws-eu-central-1a,dns=cockroachdb-0.cockroachdb.eu-central-1.svc.cluster.local       |     28 |      6|
|        7 | region=aws-eu-central-1,az=aws-eu-central-1b,dns=cockroachdb-1.cockroachdb.eu-central-1.svc.cluster.local       |     28 |      7|
|        5 | region=aws-eu-central-1,az=aws-eu-central-1c,dns=cockroachdb-2.cockroachdb.eu-central-1.svc.cluster.local       |     28 |      5|
|        3 | region=aws-us-west-2,az=aws-us-west-2a,dns=cockroachdb-0.cockroachdb.us-west-2.svc.cluster.local                |     28 |      8|
|        2 | region=aws-us-west-2,az=aws-us-west-2b,dns=cockroachdb-1.cockroachdb.us-west-2.svc.cluster.local                |     29 |      7|
|        4 | region=aws-us-west-2,az=aws-us-west-2c,dns=cockroachdb-2.cockroachdb.us-west-2.svc.cluster.local                |     27 |      7|



# Using The Abstractions

```
explain INSERT INTO public."users" (id,auth_id,first_name,last_name,email,profile_picture_id,default_picture,preferences,metadata,created_at,updated_at) VALUES ('2a231114-fd02-4e8c-bc9e-95fd5c132b96','adasdfadsf','adfa','poinc','asdfoij@gmail.com',NULL,NULL,NULL,NULL,'2022-06-07 11:21:11.618178-07','2022-06-07 11:21:11.618178-07');
```

```
------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
  distribution: local
  vectorized: true

  • root
  │
  ├── • insert
  │   │ into: users(id, auth_id, first_name, last_name, email, profile_picture_id, default_picture, preferences, metadata, created_at, updated_at, crdb_region)
  │   │
  │   └── • values
  │         size: 13 columns, 1 row
  │
  └── • constraint-check
      │
      └── • error if rows
          │
          └── • cross join
              │ estimated row count: 1
              │
              ├── • values
              │     size: 1 column, 1 row
              │
              └── • scan
                    estimated row count: 1 (100% of the table; stats collected 52 minutes ago)
                    table: users@users_rbr_pkey
                    spans: [/'aws-ap-southeast-1'/'2a231114-fd02-4e8c-bc9e-95fd5c132b96' - /'aws-ap-southeast-1'/'2a231114-fd02-4e8c-bc9e-95fd5c132b96'] [/'aws-eu-central-1'/'2a231114-fd02-4e8c-bc9e-95fd5c132b96' - /'aws-eu-central-1'/'2a231114-fd02-4e8c-bc9e-95fd5c132b96']
                    limit: 1
(26 rows)
```
