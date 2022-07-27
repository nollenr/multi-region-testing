## Create and Setup the Database
**ALL FROM US-WEST-2**

```
create database db_with_primitives;
SET override_multi_region_zone_config = true;
alter database db_with_abstractions configure zone using num_replicas=3;
use db_with_primitives;
```

## Create the Users Table
```
CREATE TABLE public.users (
    region STRING NOT NULL DEFAULT gateway_region(),
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
    CONSTRAINT users_rbr_pkey PRIMARY KEY (region, id ASC)
    -- UNIQUE INDEX users_auth_id_key (auth_id ASC),
    -- UNIQUE INDEX users_email_key (email ASC),
    -- INDEX idx_users_auth_id (auth_id ASC)
) 
    PARTITION BY LIST (region) (
       PARTITION "aws-us-west-2" VALUES IN ('aws-us-west-2'),
       PARTITION "aws-ap-southeast-1" VALUES IN ('aws-ap-southeast-1'),
       PARTITION "aws-eu-central-1" VALUES IN ('aws-eu-central-1')
    );
ALTER PARTITION "aws-us-west-2" OF INDEX users@users_rbr_pkey CONFIGURE ZONE USING
    constraints = '[+region=aws-us-west-2]';
ALTER PARTITION "aws-ap-southeast-1" OF INDEX users@users_rbr_pkey CONFIGURE ZONE USING
    constraints = '[+region=aws-ap-southeast-1]';
ALTER PARTITION "aws-eu-central-1" OF INDEX users@users_rbr_pkey CONFIGURE ZONE USING
    constraints = '[+region=aws-eu-central-1]';
alter table users configure zone using gc.ttlseconds=5;

CREATE UNIQUE INDEX users_pk_aps1 ON users(region, id) ;
ALTER index users@users_pk_aps1 configure zone using num_replicas=3,           
    constraints='{"+region=aws-ap-southeast-1":3}', lease_preferences='[[+region=aws-ap-southeast-1]]';

CREATE UNIQUE INDEX users_pk_euc1 ON users(region, id) ;
ALTER index users@users_pk_euc1 configure zone using num_replicas=3, 
    constraints='{"+region=aws-eu-central-1":3}', lease_preferences='[[+region=aws-eu-central-1]]';
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

|    partition_name   | parent_partition | column_names |      index_name      |    partition_value     |                 zone_config|
|---------------------|------------------|--------------|----------------------|------------------------|-----------------------------------------------|
|  aws-us-west-2      | NULL             | region       | users@users_rbr_pkey | ('aws-us-west-2')      | constraints = '[+region=aws-us-west-2]'|
|  aws-ap-southeast-1 | NULL             | region       | users@users_rbr_pkey | ('aws-ap-southeast-1') | constraints = '[+region=aws-ap-southeast-1]'|
|  aws-eu-central-1   | NULL             | region       | users@users_rbr_pkey | ('aws-eu-central-1')   | constraints = '[+region=aws-eu-central-1]'|

### Review the 'INSERT' Explain Plan
```
explain INSERT INTO public."users" (id,auth_id,first_name,last_name,email,profile_picture_id,default_picture,preferences,metadata,created_at,updated_at) VALUES ('2a231114-fd02-4e8c-bc9e-95fd5c132b96','adasdfadsf','adfa','poinc','asdfoij@gmail.com',NULL,NULL,NULL,NULL,'2022-06-07 11:21:11.618178-07','2022-06-07 11:21:11.618178-07');

                                                                          info
--------------------------------------------------------------------------------------------------------------------------------------------------------
  distribution: local
  vectorized: true

  • insert fast path
    into: users(region, id, auth_id, first_name, last_name, email, profile_picture_id, default_picture, preferences, metadata, created_at, updated_at)
    auto commit
    size: 12 columns, 1 row
(7 rows)

```

### Execute the Insert
```
INSERT INTO public."users" (id,auth_id,first_name,last_name,email,profile_picture_id,default_picture,preferences,metadata,created_at,updated_at) VALUES ('2a231114-fd02-4e8c-bc9e-95fd5c132b96','adasdfadsf','adfa','poinc','asdfoij@gmail.com',NULL,NULL,NULL,NULL,'2022-06-07 11:21:11.618178-07','2022-06-07 11:21:11.618178-07');

INSERT 1


Time: 173ms total (execution 172ms / network 1ms)
```

### Review Location of the Ranges for this Row
```
select range_id, lease_holder, replicas from [show range from table users for row('aws-us-west-2','2a231114-fd02-4e8c-bc9e-95fd5c132b96')];
```

|  range_id | lease_holder | replicas|
|-----------|--------------|-----------|
|       136 |            3 | {2,3,4}|
(nodes 2, 3 & 4 are all in us-west-2)

___


<br/><br/>

## Create the Organisations Table
```
CREATE TABLE public.organisations (
    region STRING NOT NULL DEFAULT gateway_region(),
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
    CONSTRAINT organisations_pkey PRIMARY KEY (region, id ASC),
    CONSTRAINT organisations_creator_fkey FOREIGN KEY (region, creator) REFERENCES public.users(region, id) ON DELETE CASCADE
    -- UNIQUE INDEX organisations_subdomain_key (subdomain ASC),
    -- CONSTRAINT check_min_subdomain_length CHECK (length(subdomain) >= 3:::INT8),
    -- CONSTRAINT check_workspace_type CHECK (workspace_type IN ('TEAM':::STRING, 'PERSONAL':::STRING)),
    -- CONSTRAINT check_pricing_plan CHECK (pricing_plan IN ('FREE':::STRING, 'PAID':::STRING))
) 
    PARTITION BY LIST (region) (
       PARTITION "aws-us-west-2" VALUES IN ('aws-us-west-2'),
       PARTITION "aws-ap-southeast-1" VALUES IN ('aws-ap-southeast-1'),
       PARTITION "aws-eu-central-1" VALUES IN ('aws-eu-central-1')
    );
ALTER PARTITION "aws-us-west-2" OF INDEX organisations@organisations_pkey CONFIGURE ZONE USING
    constraints = '[+region=aws-us-west-2]';
ALTER PARTITION "aws-ap-southeast-1" OF INDEX organisations@organisations_pkey CONFIGURE ZONE USING
    constraints = '[+region=aws-ap-southeast-1]';
ALTER PARTITION "aws-eu-central-1" OF INDEX organisations@organisations_pkey CONFIGURE ZONE USING
    constraints = '[+region=aws-eu-central-1]';
alter table organisations configure zone using gc.ttlseconds=5;
```

The partitions of the organisations table:
```
select  partition_name,
        parent_partition,
        column_names,
        index_name,
        partition_value,
        zone_config
from    [show partitions from table organisations];
```

|    partition_name   | parent_partition | column_names |            index_name            |    partition_value     |                 zone_config|
|---------------------|------------------|--------------|----------------------------------|------------------------|-----------------------------------------------|
|  aws-us-west-2      | NULL             | region       | organisations@organisations_pkey | ('aws-us-west-2')      | constraints = '[+region=aws-us-west-2]'|
|  aws-ap-southeast-1 | NULL             | region       | organisations@organisations_pkey | ('aws-ap-southeast-1') | constraints = '[+region=aws-ap-southeast-1]'|
|  aws-eu-central-1   | NULL             | region       | organisations@organisations_pkey | ('aws-eu-central-1')   | constraints = '[+region=aws-eu-central-1]'|

### Review the 'INSERT' Explain Plan
```
explain INSERT INTO public.organisations (id,"name",subdomain,creator,allowlisted_domains,workspace_type,employee_count,billing_email,profile_image_id,preferences,pricing_plan,metadata,created_at,updated_at) VALUES ('8636aaaa-f6e7-4e85-8a23-f8c8003bf805','adsfadf','fhapdfion','2a231114-fd02-4e8c-bc9e-95fd5c132b96',NULL,'TEAM',8,'asdfa3@gmail.com',NULL,NULL,'FREE',NULL,'2022-06-07 11:31:29.723805-07','2022-06-07 11:31:29.723805-07');

                                                                                                       info
------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
  distribution: local
  vectorized: true

  • insert fast path
    into: organisations(region, id, name, subdomain, creator, allowlisted_domains, workspace_type, employee_count, billing_email, profile_image_id, preferences, pricing_plan, metadata, created_at, updated_at)
    auto commit
    FK check: users@users_pk_aps1
    size: 15 columns, 1 row

```

### Run the Insert
```
INSERT INTO public.organisations (id,"name",subdomain,creator,allowlisted_domains,workspace_type,employee_count,billing_email,profile_image_id,preferences,pricing_plan,metadata,created_at,updated_at) VALUES ('8636aaaa-f6e7-4e85-8a23-f8c8003bf805','adsfadf','fhapdfion','2a231114-fd02-4e8c-bc9e-95fd5c132b96',NULL,'TEAM',8,'asdfa3@gmail.com',NULL,NULL,'FREE',NULL,'2022-06-07 11:31:29.723805-07','2022-06-07 11:31:29.723805-07');

INSERT 1

Time: 171ms total (execution 170ms / network 1ms)
```

### Review Location of the Ranges for this Row
```
select range_id, lease_holder, replicas from [show range from table organisations for row('aws-us-west-2','8636aaaa-f6e7-4e85-8a23-f8c8003bf805')];
```


|  range_id | lease_holder | replicas|
|-----------|--------------|-----------|
|       166 |            2 | {2,3,4}|


