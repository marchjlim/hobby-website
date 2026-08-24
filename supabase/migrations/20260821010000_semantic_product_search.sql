create extension if not exists vector with schema extensions;

alter table public.products
add column if not exists embedding extensions.vector(768);

create or replace function public.match_products(
    query_embedding extensions.vector(768),
    match_threshold double precision,
    match_count integer
)
returns table (
    id bigint,
    canonical_name text,
    grade text,
    scale text,
    msrp numeric,
    msrp_currency text,
    original_release_date date,
    last_reproduction_date date
)
language sql
stable
security invoker
set search_path = ''
as $$
    select
        product.id,
        product.canonical_name,
        product.grade,
        product.scale,
        product.msrp,
        product.msrp_currency,
        product.original_release_date,
        product.last_reproduction_date
    from public.products as product
    where product.embedding is not null
      and 1 - (product.embedding <=> query_embedding) >= match_threshold
    order by product.embedding <=> query_embedding
    limit least(greatest(match_count, 0), 20);
$$;

revoke all on function public.match_products(
    extensions.vector,
    double precision,
    integer
) from public;

grant execute on function public.match_products(
    extensions.vector,
    double precision,
    integer
) to authenticated;
