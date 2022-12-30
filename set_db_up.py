from typing import Optional
import uuid
import psycopg2
from psycopg2.extras import DictCursor
from supabase import create_client, Client
from supabase.lib.client_options import ClientOptions
from get_supabase_credentials import get_supabase_credentials, stop_supabase

create_companies = """create table if not exists public.companies (
    id uuid not null primary key default uuid_generate_v4(),
    name varchar(255) not null,
    email varchar(255) not null,
    phone varchar(255),
    website varchar(255),
    logo varchar(255),
    size int,
    description text,
    data jsonb, -- address and other details
    created_at timestamp with time zone default timezone('utc' :: text, now()) not null,
    updated_at timestamp with time zone default timezone('utc' :: text, now()) not null,
    subscribed boolean default true
);"""
comment_on_companies = """comment on table public.companies is 'Companies data';"""
create_teams_table = """create table if not exists public.teams (
    id uuid not null primary key default uuid_generate_v4(),
    name varchar(255) not null,
    description text,
    logo text,
    data jsonb,
    parent_id uuid null,
    level int not null default 0,
    level_name text null,
    company_id uuid references public.companies not null,
    created_at timestamp with time zone default timezone('utc' :: text, now()) not null,
    updated_at timestamp with time zone default timezone('utc' :: text, now()) not null
);
"""
comment_on_teams = """comment on table public.teams is 'Teams data';"""
create_profile_completion_enum = (
    """create type profile_completion as enum ('invited', 'active', 'suspended');"""
)
create_users_table = """create table if not exists public.users (
    id uuid references auth.users on delete cascade not null primary key,
    first_name varchar(255),
    last_name varchar(255),
    email varchar(255) not null,
    phone varchar(255),
    data jsonb,
    job_title varchar(255),
    gender varchar(255),
    married bool, --maritial status could be [single, married, separated, divorced, other]
    ethnicity varchar(255),
    sexuality varchar(255),
    disability bool,
    date_of_birth timestamp,
    profile_status profile_completion not null default 'invited',
    is_parent boolean null,
    team_selected boolean not null default false,
    accepted_terms boolean not null default false,
    profile_type varchar(255) not null default 'full', -- minimal, partial, full
    company_id uuid references public.companies not null,
    created_at timestamp with time zone default timezone('utc' :: text, now()) not null,
    updated_at timestamp with time zone default timezone('utc' :: text, now()) not null,
    start_date timestamp with time zone default timezone('utc' :: text, now())
);
"""
comment_on_users = """comment on table public.users is 'Users data';"""
handle_new_user = """create or replace function handle_new_user() returns trigger as $$
    begin
        insert into public.users(id, email, company_id)
        values(
            new.id,
            new.email,
            (select id from public.companies where id = uuid(new.raw_user_meta_data->>'company_id')));
        update auth.users
        set raw_app_meta_data = raw_app_meta_data || new.raw_user_meta_data
        where email = new.email;
        update auth.users
        set raw_user_meta_data = '{}'
        where email = new.email;
        return new;
    end;
$$ language plpgsql security definer;
"""
on_auth_user_created = """drop trigger if exists on_auth_user_created on auth.user cascade;
create trigger on_auth_user_created
    after insert on auth.users
    for each row
    execute function handle_new_user();
"""
failed_invites = """create table if not exists public.failed_invites (
    id uuid not null primary key default uuid_generate_v4(),
    email text not null,
    payload jsonb,
    reason text not null,
    created_at timestamp with time zone default timezone('utc' :: text, now()) not null
);"""
comment_on_failed_invites = (
    """comment on table public.failed_invites is 'Failed invites data';"""
)
empylo_insert = """insert into
   public.companies ( name, email, phone, website, logo, size, description, data ) 
values
   (
      'Empylo', 'admin@empylo.com', '1234567890', 'https://empylo.com', 'https://empylo.com/logo.png', 10, 'Empylo is a company that helps you collect and analyse well being data.', '{"address": "10 Downing St, London"}' 
   )
;
"""
insert_empylo_teams = """insert into
   public.teams ( name, description, logo, data, parent_id, level, level_name, company_id ) 
values
   (
      'Finance', 'Finance team', 'https://empylo.com/logo.png', '{"moto": "We are what we are."}', null, 0, 'Finance', 
      (
         select
            id 
         from
            public.companies 
         where
            name = 'Empylo'
      )
   )
,
   (
      'Sales',
      'Sales team',
      'https://empylo.com/logo.png',
      '{"moto": "Keep on, keeping on"}',
      null,
      0,
      'Sales',
      (
         select
            id 
         from
            public.companies 
         where
            name = 'Empylo'
      )
   )
;
"""
sql_queries = [
    create_companies,
    comment_on_companies,
    create_teams_table,
    comment_on_teams,
    create_profile_completion_enum,
    create_users_table,
    comment_on_users,
    handle_new_user,
    on_auth_user_created,
    failed_invites,
    comment_on_failed_invites,
    empylo_insert,
    insert_empylo_teams,
]


def connect_to_db(db_credentials) -> psycopg2.extensions.connection:
    """
    Connect to the database.
    Args:
        db_credentials (dict): Supabase credentials
    Returns:
        psycopg2.extensions.connection
    """
    try:
        connection = psycopg2.connect(db_credentials["db_url"])
        cursor = connection.cursor(cursor_factory=DictCursor)
    except Exception as error:
        raise error
    return connection, cursor


def get_supabase_client(db_credentials) -> Client:
    """
    Get a supabase client.
    Returns:
        supabase.Client
    """
    try:
        supabase_client = create_client(
            db_credentials["supabase_url"], db_credentials["service_role_key"]
        )
    except Exception as error:
        raise error
    return supabase_client


def exacute_sql_queries(
    connection: psycopg2.extensions.connection,
    cursor: DictCursor,
    sql_queries: list,
) -> None:
    """
    Execute sql queries.
    Args:
        connection: psycopg2.extensions.connection
        cursor: psycopg2.extras.DictCursor
        sql_queries: list
    Returns:
        None
    """
    try:
        for query in sql_queries:
            cursor.execute(query)
            connection.commit()
    except Exception as error:
        raise error


def get_empylo_company_id(db_credentials) -> str:
    """
    Get the Empylo company id.
    Returns:
        str
    """
    try:
        supabase_client = get_supabase_client(db_credentials=db_credentials)
        response = (
            supabase_client.from_("companies")
            .select("*")
            .eq("name", "Empylo")
            .execute()
        )
        empylo_id = response.data[0]["id"]
        print(f"Empylo company id: {empylo_id}")
        return empylo_id
    except Exception as error:
        raise error


def spin_db_up() -> Optional[dict]:
    """Spins up the database and returns the credentials.
    Create tables, comments, policies and functions.
    Returns:
        Optional[dict]  -- Supabase credentials
    """
    try:
        db_credentials = get_supabase_credentials()
        connection, cursor = connect_to_db(db_credentials=db_credentials)
        exacute_sql_queries(connection, cursor, sql_queries)
        empylo_id = get_empylo_company_id(db_credentials=db_credentials)
        db_credentials["company_id"] = empylo_id
        return db_credentials
    except Exception as error:
        raise error


def main() -> None:
    """
    Main.
    Returns:
        None
    """
    try:
        db_credentials = get_supabase_credentials()
        connection, cursor = connect_to_db(db_credentials=db_credentials)
        exacute_sql_queries(connection, cursor, sql_queries)
        supabase_client = get_supabase_client(db_credentials=db_credentials)
        stop_supabase()
    except Exception as error:
        raise error


if __name__ == "__main__":
    main()
