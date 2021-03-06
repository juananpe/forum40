from collections import defaultdict
from timeit import default_timer as timer

import datetime
import h5py
import logging
import math
import psycopg2
import sqlite3
from operator import itemgetter
from psycopg2.extras import execute_values
from tqdm import tqdm, trange

from forumdb.constants import OmpTables, OMP_DB_FILE, PG_USER, PG_DB, OMP_EMBEDDINGS_FILE
from forumdb.tools import dict_factory, insert, Inserter, omp_data
from forumdb.html_to_text import html_to_text

logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.DEBUG)

# TODO: External IDs


if __name__ == "__main__":
    sql_conn = sqlite3.connect(OMP_DB_FILE)
    sql_conn.row_factory = dict_factory
    logging.info(f'Connected to import source {OMP_DB_FILE}')

    conn = psycopg2.connect(dbname=PG_DB, user=PG_USER)
    logging.info(f'Connected to import target {PG_USER}@{PG_DB}')

    start = timer()

    # load omp data
    omp = omp_data(sql_conn)

    # sources
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO sources (name, domain) "
        "VALUES ('Der Standard', 'standard.at') "
        "RETURNING id"
    )
    source_id = cur.fetchone()[0]
    cur.close()
    logging.info(f'Importing to new source with ID {source_id}')

    # commentators
    omp_user_ids = set(post['ID_User'] for post in omp[OmpTables.POSTS])
    user_lookup = insert(
        conn,
        "INSERT INTO users (external_id, name) VALUES %s RETURNING id",
        {id_: (id_, id_) for id_ in omp_user_ids},
        unit='User',
    )

    # documents
    document_lookup = insert(
        conn,
        "INSERT INTO documents (external_id, category, url, title, text, markup, timestamp, source_id) VALUES %s RETURNING id",
        {art['ID_Article']: (
            str(art["ID_Article"]),
            art["Path"].split('/')[1] if '/' in art["Path"] else art["Path"],  # category
            art["Path"],  # url
            art["Title"],  # title
            html_to_text(art["Body"]),  # text
            art["Body"],  # markup
            art["publishingDate"],  # timestamp
            source_id,  # source_id
        ) for art in omp[OmpTables.ARTICLES]},
        unit='Document'
    )

    # labels
    label_lookup = insert(
        conn,
        "INSERT INTO labels (name, type, \"order\", source_id) VALUES %s RETURNING id",
        {cat["Name"]: (cat["Name"], "classification", cat["Ord"], source_id)
         for cat in omp[OmpTables.CATEGORIES]},
        unit='Label',
    )

    # comments
    # comment sorting required as parent posts always have to be inserted before replies
    # approach to minimize the number of session.flush() calls needed:
    # batch by reply structure "depth" i.e. first insert all root comments, then all replies to root
    # comments, then all replies to replies to root comments, then ???
    parent_id_by_id = {p['ID_Post']: p['ID_Parent_Post'] for p in omp[OmpTables.POSTS]}
    omp_posts_by_depth = defaultdict(list)
    for omp_post in omp[OmpTables.POSTS]:
        depth = 0
        parent_iterator_id = omp_post['ID_Parent_Post']
        while parent_iterator_id is not None:
            depth += 1
            parent_iterator_id = parent_id_by_id[parent_iterator_id]

        omp_posts_by_depth[depth].append(omp_post)

    comment_sql = (
        "INSERT INTO comments (external_id, doc_id, source_id, user_id, parent_comment_id, status, title, text, timestamp, year, month, day, embedding)"
        "VALUES %s RETURNING id"
    )

    # iterate batches by increasing depth

    with Inserter(conn, comment_sql, unit='Comment', total=len(omp[OmpTables.POSTS])) as inserter:
        for depth, omp_post_batch in sorted(omp_posts_by_depth.items(), key=itemgetter(0)):
            inserter.pbar.set_postfix(depth=depth)
            for omp_post in omp_post_batch:
                comment_date = datetime.datetime.strptime(omp_post["CreatedAt"], '%Y-%m-%d %H:%M:%S.%f')
                omp_parent_id = omp_post["ID_Parent_Post"]

                inserter.add(
                    source_id=omp_post["ID_Post"],
                    args=(
                        str(omp_post["ID_Post"]),  # external_id
                        document_lookup[omp_post["ID_Article"]],  # doc_id
                        source_id,  # source_id
                        user_lookup[omp_post["ID_User"]],  # user_id
                        inserter.id_lookup[omp_parent_id] if omp_parent_id is not None else None,  # parent_comment_id
                        omp_post["Status"],  # status
                        omp_post["Headline"],  # title
                        omp_post["Body"],  # text
                        omp_post["CreatedAt"],  # timestamp
                        comment_date.year,  # year
                        comment_date.month,  # month
                        comment_date.day,  # day
                        None,  # embedding
                    )
                )

            inserter.flush()
        comment_lookup = inserter.id_lookup

    # annotations
    with conn.cursor() as cur:
        execute_values(
            cur,
            "INSERT INTO annotations (label_id, comment_id, label) VALUES %s",
            tqdm([
                (label_lookup[ann["Category"]], comment_lookup[ann["ID_Post"]], bool(ann["Value"]))
                for ann in omp[OmpTables.ANNOTATIONS_CONSOLIDATED]
            ], unit='Annotation'),
        )

    with h5py.File(OMP_EMBEDDINGS_FILE, 'r') as f:
        ids = f['ids']
        embs = f['embeddings']
        n_embeddings = len(ids)

        batch_size = 5000
        n_batches = math.ceil(n_embeddings / batch_size)

        embedding_sql = (
            'UPDATE comments '
            'SET embedding = data.embedding '
            'FROM (VALUES %s) AS data (id, embedding) '
            f'WHERE comments.source_id = {source_id} '
            'AND comments.external_id = data.id'
        )

        with conn.cursor() as cur:
            for batch_start in trange(0, n_embeddings, batch_size, unit_scale=batch_size, unit='Embedding'):
                batch_end = batch_start + batch_size

                batch_data = list(zip(
                    [str(id_) for id_ in ids[batch_start:batch_end]],
                    embs[batch_start:batch_end].tolist(),
                ))

                execute_values(cur, embedding_sql, batch_data, page_size=100)

    conn.commit()
    conn.close()

    end = timer()
    logging.info(f"Import completed after {timer() - start:.01f} seconds.")
