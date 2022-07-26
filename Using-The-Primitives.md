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
















```
CREATE TABLE userinfo ( 
    region STRING       NOT NULL DEFAULT gateway_region(),
    ku string UNIQUE,
    data jsonb NOT NULL,
    email string AS (Data->>'Email') STORED, 
    PRIMARY KEY (region, ku),
    INDEX emailindex (email) WHERE (email) IS NOT NULL,
    FOREIGN KEY (region, KU) REFERENCES klei.userid (region, ku) MATCH FULL ON DELETE CASCADE ON UPDATE CASCADE);
    PARTITION BY LIST (region) (
       PARTITION "aws-us-west-2" VALUES IN ('aws-us-west-2'),
       PARTITION "aws-ap-southeast-1" VALUES IN ('aws-ap-southeast-1'),
       PARTITION "aws-eu-central-1" VALUES IN ('aws-eu-central-1')
    );

ALTER PARTITION "aws-us-west-2" OF INDEX userinfo@userinfo_pkey CONFIGURE ZONE USING
    constraints = '[+region=aws-us-west-2]';
ALTER PARTITION "aws-ap-southeast-1" OF INDEX userinfo@userinfo_pkey CONFIGURE ZONE USING
    constraints = '[+region=aws-ap-southeast-1]';
ALTER PARTITION "aws-eu-central-1" OF INDEX userinfo@userinfo_pkey CONFIGURE ZONE USING
    constraints = '[+region=aws-eu-central-1]'
```

```
CREATE TABLE UserID (
    KU string,
    Region string NOT NULL,
    SteamID decimal,
    PSNID string,
    RailCommonID string,
    GoogleLogin string,
    XboxID string,
    EpicID string,
    NintendoAccountID string,
    NintendoSAID string,
    DouyuID string,
    BilibiliID string,
    PRIMARY KEY (KU ASC),
    UNIQUE INDEX (Region, KU),
    UNIQUE INDEX SteamIDIndex (SteamID ASC) WHERE SteamID IS NOT NULL,
    UNIQUE INDEX PSNIDIndex (PSNID ASC) WHERE PSNID IS NOT NULL,
    UNIQUE INDEX RailCommonIDIndex (RailCommonID ASC) WHERE RailCommonID IS NOT NULL,
    UNIQUE INDEX GoogleLoginIndex (GoogleLogin ASC) WHERE GoogleLogin IS NOT NULL,
    UNIQUE INDEX XboxIDIndex (XboxID ASC) WHERE XboxID IS NOT NULL,
    UNIQUE INDEX EpicIDIndex (EpicID ASC) WHERE EpicID IS NOT NULL,
    UNIQUE INDEX NintendoAccountIDIndex (NintendoAccountID ASC) WHERE NintendoAccountID IS NOT NULL,
    UNIQUE INDEX NintendoSAIDIndex (NintendoSAID ASC) WHERE NintendoSAID IS NOT NULL,
    UNIQUE INDEX DouyuIDIndex (DouyuID ASC) WHERE DouyuID IS NOT NULL,
    UNIQUE INDEX BilibiliIDIndex (BilibiliID ASC) WHERE BilibiliID IS NOT NULL
);

CREATE UNIQUE INDEX ku_east1 ON userid(region, ku) ;
CREATE UNIQUE INDEX ku_eu2 ON userid(region, ku) ;
And then I alter these indexes so that their lease holder replicas are located in us-east-1 and eu-west-2.
ALTER index userid@ku_east1 configure zone using num_replicas=3, constraints=‘{“+region=us-east-1”:1}‘, lease_preferences=‘[[+region=us-east-1]]‘;
ALTER index userid@ku_eu2 configure zone using num_replicas=3, constraints=‘{“+region=eu-west-2":1}‘, lease_preferences=‘[[+region=eu-west-2]]’;

```
