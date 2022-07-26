create database db_with_abstractions;
use db_with_abstractions;
alter database db_with_abstractions set primary region "aws-us-west-2";
alter database db_with_abstractions add region "aws-ap-southeast-1";
alter database db_with_abstractions add region "aws-eu-central-1";
SET override_multi_region_zone_config = true;
alter database db_with_abstractions configure zone using num_replicas=3;

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

select  partition_name,
        parent_partition,
        column_names,
        index_name,
        partition_value,
        zone_config
from    [show partitions from table users];

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


CREATE TABLE public.organisation_users (
    id UUID NOT NULL DEFAULT gen_random_uuid(),
    org_id UUID NULL,
    user_id UUID NULL,
    "role" VARCHAR NOT NULL,
    metadata JSONB NULL,
    created_at TIMESTAMPTZ NULL DEFAULT now():::TIMESTAMPTZ,
    updated_at TIMESTAMPTZ NULL DEFAULT now():::TIMESTAMPTZ,
    CONSTRAINT organisation_users_pkey PRIMARY KEY (id ASC),
    CONSTRAINT organisation_users_org_id_fkey FOREIGN KEY (org_id) REFERENCES public.organisations(id),
    CONSTRAINT organisation_users_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE,
    UNIQUE INDEX organisation_users_org_id_user_id_role_key (org_id ASC, user_id ASC, "role" ASC),
    CONSTRAINT check_role CHECK ("role" IN ('MEMBER':::STRING, 'CREATOR':::STRING, 'ADMIN':::STRING))
);
alter table organisation_users configure zone using gc.ttlseconds=5;

