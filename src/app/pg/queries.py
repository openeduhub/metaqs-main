from pprint import pformat
from typing import Dict, List
from uuid import UUID

from asyncpg import Connection

from src.app.core.config import DEBUG
from src.app.core.logging import logger
from src.app.models.stats import StatType


async def stats_latest(
    conn: Connection, stat_type: StatType, noderef_id: UUID
) -> List[Dict]:
    results = []

    if stat_type is StatType.SEARCH:

        results = await conn.fetch(
            """
            with collections as (

                select id
                from staging.collections
                where portal_id = $1

            )

            select stats.resource_id collection_id
                 , stats.stats
            from store.search_stats stats
                join collections c on c.id = stats.resource_id
            where resource_type = 'COLLECTION'
                and resource_field = 'TITLE'
            """,
            noderef_id,
        )

    elif stat_type is StatType.MATERIAL_TYPES:

        results = await conn.fetch(
            """
            with collections as (

                select id
                from staging.collections
                where portal_id = $1

            ), counts as (

                select counts.*
                from staging.material_counts_by_learning_resource_type counts
                         join collections c on c.id =  counts.collection_id

            ), agg as (

                select counts.collection_id
                     , jsonb_object_agg(counts.learning_resource_type::text, counts.count) counts
                from counts
                group by counts.collection_id

            )

            select c.id collection_id
                 , case
                        when agg.counts is not null
                            then jsonb_set(agg.counts, '{total}', to_jsonb(mc.total))
                        else jsonb_build_object('total', mc.total)
                   end counts
            from collections c
                join staging.material_counts mc on mc.collection_id = c.id
                left join agg on agg.collection_id = c.id
            """,
            noderef_id,
        )

    elif stat_type is StatType.VALIDATION_COLLECTIONS:

        results = await conn.fetch(
            """
            with agg as (

                select resource_id                    collection_id
                     , array_agg(missing_field::text) missing_fields
                from staging.missing_fields
                where resource_type = 'COLLECTION'
                group by resource_id

            )

            select c.id collection_id
                 , coalesce(agg.missing_fields, '{}'::text[]) missing_fields
            from staging.collections c
                    left join agg on agg.collection_id = c.id
            where c.portal_id = $1
            order by c.portal_depth, c.id
            """,
            noderef_id,
        )

    elif stat_type is StatType.VALIDATION_MATERIALS:

        results = await conn.fetch(
            """
            with agg as (
                select mm.collection_id
                     , jsonb_object_agg(mm.missing_field, mm.material_ids) missing_fields
                from staging.materials_by_missing_field mm
                group by mm.collection_id
            )
            select c.id as collection_id
                 , coalesce(agg.missing_fields, '{}'::jsonb) missing_fields
            from staging.collections c
                     left join agg on agg.collection_id = c.id
            where c.portal_id = $1
            order by c.portal_depth, c.id
            """,
            noderef_id,
        )

    elif stat_type is StatType.PORTAL_TREE:

        results = await conn.fetch(
            """
            select c.id                                                        noderef_id
                 , c.title
                 , replace(ltree2text(subpath(c.path, -2, 1)), '_', '-')::uuid parent_id
            from staging.collections c
            where c.portal_id = $1
            order by c.portal_depth, parent_id
            """,
            noderef_id,
        )

    results = [dict(record) for record in results]

    if DEBUG:
        logger.debug(f"Read from postgres:\n{pformat(results)}")

    return results
