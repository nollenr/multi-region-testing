# Using The Abstractions

- [Using The Abstractions](#using-the-abstractions)
  - [Create and Setup the Database](#create-and-setup-the-database)
  - [Create the Users Table](#create-the-users-table)
    - [Review the 'INSERT' Explain Plan](#review-the-insert-explain-plan)
    - [Execute the Insert](#execute-the-insert)
    - [Review Location of the Ranges for this Row](#review-location-of-the-ranges-for-this-row)
  - [Create the Organisations Table](#create-the-organisations-table)
    - [Review the 'INSERT' Explain Plan](#review-the-insert-explain-plan-1)
    - [Run the Insert](#run-the-insert)
    - [Review Location of the Ranges for this Row](#review-location-of-the-ranges-for-this-row-1)

## Create and Setup the Database
**ALL FROM US-WEST-2**

Create a multi-region database and keep all leaseholders and voting replicas in the same region (hence the 3 replicas, not 5).
```
create database db_with_abstractions;
use db_with_abstractions;
alter database db_with_abstractions set primary region "aws-us-west-2";
alter database db_with_abstractions add region "aws-ap-southeast-1";
alter database db_with_abstractions add region "aws-eu-central-1";
SET override_multi_region_zone_config = true;
alter database db_with_abstractions configure zone using num_replicas=3;
```

## Create the Users Table
```
CREATE TABLE public.users (
    id UUID NOT NULL DEFAULT gen_random_uuid(),
    auth_id VARCHAR(100) NOT NULL,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NULL,
    email VARCHAR NOT NULL,
    profile_picture_id VARCHAR NULL,
    default_picture VARCHAR NULL,
    preferences JSONB NULL,
    metadata JSONB NULL,
    created_at TIMESTAMPTZ NULL DEFAULT now():::TIMESTAMPTZ,
    updated_at TIMESTAMPTZ NULL DEFAULT now():::TIMESTAMPTZ,
    CONSTRAINT users_rbr_pkey PRIMARY KEY (id ASC)
    -- UNIQUE INDEX users_auth_id_key (auth_id ASC),
    -- UNIQUE INDEX users_email_key (email ASC),
    -- INDEX idx_users_auth_id (auth_id ASC)
) locality regional by row;
alter table users configure zone using gc.ttlseconds=5;
```

The partitions of the users table:
```
select  partition_name,
        parent_partition,
        column_names,
        index_name,
        partition_value,
        zone_config
from    [show partitions from table users];
```
|    partition_name   | parent_partition | column_names |      index_name      |    partition_value     |                     zone_config|
|---------------------|------------------|--------------|----------------------|------------------------|-------------------------------------------------------|
|  aws-ap-southeast-1 | NULL             | crdb_region  | users@users_rbr_pkey | ('aws-ap-southeast-1') | num_voters = 3,|
|                     |                  |              |                      |                        | voter_constraints = '[+region=aws-ap-southeast-1]',|
|                     |                  |              |                      |                        | lease_preferences = '[[+region=aws-ap-southeast-1]]'|
|  aws-eu-central-1   | NULL             | crdb_region  | users@users_rbr_pkey | ('aws-eu-central-1')   | num_voters = 3,|
|                     |                  |              |                      |                        | voter_constraints = '[+region=aws-eu-central-1]',|
|                     |                  |              |                      |                        | lease_preferences = '[[+region=aws-eu-central-1]]'|
|  aws-us-west-2      | NULL             | crdb_region  | users@users_rbr_pkey | ('aws-us-west-2')      | num_voters = 3,|
|                     |                  |              |                      |                        | voter_constraints = '[+region=aws-us-west-2]',|
|                     |                  |              |                      |                        | lease_preferences = '[[+region=aws-us-west-2]]'|


### Review the 'INSERT' Explain Plan
```
explain INSERT INTO public."users" (id,auth_id,first_name,last_name,email,profile_picture_id,default_picture,preferences,metadata,created_at,updated_at) VALUES ('2a231114-fd02-4e8c-bc9e-95fd5c132b96','adasdfadsf','adfa','poinc','asdfoij@gmail.com',NULL,NULL,NULL,NULL,'2022-06-07 11:21:11.618178-07','2022-06-07 11:21:11.618178-07');
```

```
                                                                                                                                        info
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
                    estimated row count: 1 (100% of the table; stats collected 3 hours ago)
                    table: users@users_rbr_pkey
                    spans: [/'aws-ap-southeast-1'/'2a231114-fd02-4e8c-bc9e-95fd5c132b96' - /'aws-ap-southeast-1'/'2a231114-fd02-4e8c-bc9e-95fd5c132b96'] [/'aws-eu-central-1'/'2a231114-fd02-4e8c-bc9e-95fd5c132b96' - /'aws-eu-central-1'/'2a231114-fd02-4e8c-bc9e-95fd5c132b96']
                    limit: 1

```

### Execute the Insert
```
INSERT INTO public."users" (id,auth_id,first_name,last_name,email,profile_picture_id,default_picture,preferences,metadata,created_at,updated_at) VALUES ('2a231114-fd02-4e8c-bc9e-95fd5c132b96','adasdfadsf','adfa','poinc','asdfoij@gmail.com',NULL,NULL,NULL,NULL,'2022-06-07 11:21:11.618178-07','2022-06-07 11:21:11.618178-07');

INSERT 1


Time: 311ms total (execution 310ms / network 1ms)
```

### Review Location of the Ranges for this Row
```
select range_id, lease_holder, replicas from [show range from table users for row('aws-us-west-2','2a231114-fd02-4e8c-bc9e-95fd5c132b96')];
```

|  range_id | lease_holder | replicas|
|-----------|--------------|-----------|
|       100 |            4 | {2,3,4}|
(nodes 2, 3 & 4 are all in us-west-2)

___


<br/><br/>

## Create the Organisations Table
```
CREATE TABLE public.organisations (
    id UUID NOT NULL DEFAULT gen_random_uuid(),
    name VARCHAR NOT NULL,
    subdomain VARCHAR(60) NOT NULL,
    creator UUID NULL,
    allowlisted_domains VARCHAR[] NULL,
    workspace_type VARCHAR NOT NULL,
    employee_count INT8 NULL DEFAULT (-1):::INT8,
    billing_email VARCHAR NULL,
    profile_image_id VARCHAR NULL,
    preferences JSONB NULL,
    pricing_plan VARCHAR NOT NULL DEFAULT 'FREE':::STRING,
    metadata JSONB NULL,
    created_at TIMESTAMPTZ NULL DEFAULT now():::TIMESTAMPTZ,
    updated_at TIMESTAMPTZ NULL DEFAULT now():::TIMESTAMPTZ,
    CONSTRAINT organisations_pkey PRIMARY KEY (id ASC),
    CONSTRAINT organisations_creator_fkey FOREIGN KEY (creator) REFERENCES public.users(id) ON DELETE CASCADE
    -- UNIQUE INDEX organisations_subdomain_key (subdomain ASC),
    -- CONSTRAINT check_min_subdomain_length CHECK (length(subdomain) >= 3:::INT8),
    -- CONSTRAINT check_workspace_type CHECK (workspace_type IN ('TEAM':::STRING, 'PERSONAL':::STRING)),
    -- CONSTRAINT check_pricing_plan CHECK (pricing_plan IN ('FREE':::STRING, 'PAID':::STRING))
) locality regional by row;
alter table organisations configure zone using gc.ttlseconds=5;
```

### Review the 'INSERT' Explain Plan
```
explain INSERT INTO public.organisations (id,"name",subdomain,creator,allowlisted_domains,workspace_type,employee_count,billing_email,profile_image_id,preferences,pricing_plan,metadata,created_at,updated_at) VALUES ('8636aaaa-f6e7-4e85-8a23-f8c8003bf805','adsfadf','fhapdfion','2a231114-fd02-4e8c-bc9e-95fd5c132b96',NULL,'TEAM',8,'asdfa3@gmail.com',NULL,NULL,'FREE',NULL,'2022-06-07 11:31:29.723805-07','2022-06-07 11:31:29.723805-07');

                                                                                                                                        info
------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
  distribution: local
  vectorized: true

  • root
  │
  ├── • insert
  │   │ into: organisations(id, name, subdomain, creator, allowlisted_domains, workspace_type, employee_count, billing_email, profile_image_id, preferences, pricing_plan, metadata, created_at, updated_at, crdb_region)
  │   │
  │   └── • buffer
  │       │ label: buffer 1
  │       │
  │       └── • values
  │             size: 16 columns, 1 row
  │
  ├── • constraint-check
  │   │
  │   └── • error if rows
  │       │
  │       └── • cross join
  │           │ estimated row count: 1
  │           │
  │           ├── • values
  │           │     size: 1 column, 1 row
  │           │
  │           └── • scan
  │                 estimated row count: 1 (100% of the table; stats collected 4 minutes ago)
  │                 table: organisations@organisations_pkey
  │                 spans: [/'aws-ap-southeast-1'/'8636aaaa-f6e7-4e85-8a23-f8c8003bf805' - /'aws-ap-southeast-1'/'8636aaaa-f6e7-4e85-8a23-f8c8003bf805'] [/'aws-eu-central-1'/'8636aaaa-f6e7-4e85-8a23-f8c8003bf805' - /'aws-eu-central-1'/'8636aaaa-f6e7-4e85-8a23-f8c8003bf805']
  │                 limit: 1
  │
  └── • constraint-check
      │
      └── • error if rows
          │
          └── • lookup join (anti)
              │ estimated row count: 0
              │ table: users@users_rbr_pkey
              │ equality cols are key
              │ lookup condition: (column4 = id) AND (crdb_region IN ('aws-ap-southeast-1', 'aws-eu-central-1'))
              │
              └── • lookup join (anti)
                  │ estimated row count: 0
                  │ table: users@users_rbr_pkey
                  │ equality cols are key
                  │ lookup condition: (column4 = id) AND (crdb_region = 'aws-us-west-2')
                  │
                  └── • scan buffer
                        label: buffer 1

```

### Run the Insert
```
INSERT INTO public.organisations (id,"name",subdomain,creator,allowlisted_domains,workspace_type,employee_count,billing_email,profile_image_id,preferences,pricing_plan,metadata,created_at,updated_at) VALUES ('8636aaaa-f6e7-4e85-8a23-f8c8003bf805','adsfadf','fhapdfion','2a231114-fd02-4e8c-bc9e-95fd5c132b96',NULL,'TEAM',8,'asdfa3@gmail.com',NULL,NULL,'FREE',NULL,'2022-06-07 11:31:29.723805-07','2022-06-07 11:31:29.723805-07');

INSERT 1


Time: 309ms total (execution 308ms / network 1ms)
```

### Review Location of the Ranges for this Row
```
select range_id, lease_holder, replicas from [show range from table organisations for row('aws-us-west-2','8636aaaa-f6e7-4e85-8a23-f8c8003bf805')];
```

 
|  range_id | lease_holder | replicas|
|-----------|--------------|-----------|
|       107 |            4 | {2,3,4}|

