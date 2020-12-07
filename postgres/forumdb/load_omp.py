import sqlite3
import logging
import datetime
import argparse

from timeit import default_timer as timer
from tqdm import tqdm

import forumdb.Constants as Const
import forumdb.pg_tools as tools

from sqlalchemy import create_engine
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session

logging.basicConfig(
    format='%(asctime)s : %(levelname)s : %(message)s', level=logging.DEBUG)

# Sqlite
sql_conn = sqlite3.connect(Const.OMP_DB_FILE)
sql_conn.row_factory = tools.dict_factory
logging.info(f'Sqlite3 connection to file: {Const.OMP_DB_FILE}')

# keine foreign keys
# keine unique constraints
# primary keys nach insert
# indexes nach insert
# labelgroup sentiment: pos neg and what else?


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Import OMP Database.')
    parser.add_argument('-d', '--drop-tables', dest='drop_tables', default=False, action='store_true',
                        help='Drop existing public schema and tables in OMP database')
    parser.add_argument('-e', '--with-embeddings', dest='with_embeddings', default=False, action='store_true',
                        help='Import OMP database (Der Standard) with pre-generated embeddings')
    args = parser.parse_args()

    db = create_engine(Const.PG_URL)
    connection = db.connect()
    logging.info(f'Connected to Postgres database {Const.PG_URL}')

    start = timer()

    # if args.drop_tables:
    #     tools.run_sql_file(connection, "pg_drop.sql")
    #     logging.info("Schema public and tables dropped")

    # init database schema
    # tools.run_sql_file(connection, "pg_schema.sql")
    Base = automap_base()
    Base.prepare(db, reflect=True)
    session = Session(db)
    logging.info("Schema public created")

    users_id = session.execute("SELECT MAX(id) from users").fetchone()[0]
    doc_id = session.execute("SELECT MAX(id) from documents").fetchone()[0]
    com_id = session.execute("SELECT MAX(id) from comments").fetchone()[0]
    label_id = session.execute("SELECT MAX(id) from labels").fetchone()[0]
    source_id = session.execute("SELECT MAX(id) from sources").fetchone()[0]
    users_id = 0 if users_id is None else users_id
    doc_id = 0 if doc_id is None else doc_id
    com_id = 0 if com_id is None else com_id
    label_id = 0 if label_id is None else label_id
    source_id = 1 if source_id is None else source_id + 1

    # connect to sqlite
    omp = tools.omp_data(sql_conn)

    # sources
    Sources = Base.classes.sources
    new_source = Sources(id = source_id, name = "Der Standard", domain = "derstandard.at")
    session.add(new_source)
    session.commit()
    logging.info("Inserted source %s with id %d" % (new_source.name, new_source.id))

    # commentators
    Commentators = Base.classes.users
    commentators = set()
    for post in omp[Const.POSTS]:
        commentators.add(post['ID_User'])
    commentator_lookup = {}
    commentator_id = users_id
    bulk = []
    for commentator in tqdm(commentators):
        commentator_id += 1
        commentator_lookup[commentator] = commentator_id
        bulk.append({"id" : commentator_id, "external_id" : commentator, "name" : commentator})
    session.execute(Commentators.__table__.insert(), bulk)
    logging.info("Inserted %d commentators" % (commentator_id - users_id))

    # documents
    Documents = Base.classes.documents
    document_lookup = {}
    i = doc_id
    for document in tqdm(omp[Const.ARTICLES]):
        i += 1
        cat = document["Path"].split('/')[1] if '/' in document["Path"] else document["Path"]
        new_document = Documents(id = i, category=cat, url = document["Path"], title = document["Title"], text = document["Body"], timestamp = document["publishingDate"], source_id = new_source.id)
        session.add(new_document)
        document_lookup[document["ID_Article"]] = i
    session.commit()
    logging.info("Inserted %d documents" % (i - doc_id))

    # labels
    Labels = Base.classes.labels
    label_lookup = {}
    i = label_id
    for label in omp[Const.CATEGORIES]:
        i += 1
        new_label = Labels(id = i, name = label["Name"], type = "classification", order = label["Ord"], source_id = new_source.id)
        session.add(new_label)
        label_lookup[label["Name"]] = i
    session.commit()
    logging.info("Inserted %d labels" % (i-label_id))

    # comments
    Comments = Base.classes.comments
    comment_lookup = {}
    i = 0
    bulk = []
    comment_id = com_id
    for comment in tqdm(omp[Const.POSTS]):
        comment_id += 1
        comment_lookup[comment["ID_Post"]] = comment_id
        comment_date = datetime.datetime.strptime(comment["CreatedAt"], '%Y-%m-%d %H:%M:%S.%f')
        new_comment = {
            "id" : comment_id,
            "doc_id" : document_lookup[comment["ID_Article"]],
            "source_id" : new_source.id,
            "user_id" : commentator_lookup[comment["ID_User"]],
            "parent_comment_id" : comment["ID_Parent_Post"],
            "status" : comment["Status"],
            "title" : comment["Headline"],
            "text" : comment["Body"],
            "timestamp" : comment["CreatedAt"],
            "year" : comment_date.year,
            "month" : comment_date.month,
            "day" : comment_date.day,
            "embedding" : None,
        }
        if args.with_embeddings:
            embed = []
            embed_comment = tools.embed_data(sql_conn, comment["ID_Post"])
            for embeddings in embed_comment[Const.POSTS]:
                embedding = embeddings["Embedding"]
                if embedding != '':
                    for e in embedding.strip('{}').split(','):
                        embed.append(float(e))
                    new_comment["embedding"] = embed

        bulk.append(new_comment)
        if comment_id % 1000 == 0:
            session.execute(Comments.__table__.insert(), bulk)
            bulk = []
            # break
    if bulk:
        session.execute(Comments.__table__.insert(), bulk)
    session.commit()
    logging.info("Inserted %d comments" % (comment_id - com_id))

    # annotations
    print(label_lookup)
    Annotations = Base.classes.annotations
    i = 0
    for annotation in omp[Const.ANNOTATIONS_CONSOLIDATED]:
        new_annotation = Annotations(
            label_id = label_lookup[annotation["Category"]],
            comment_id = comment_lookup[annotation["ID_Post"]],
            label = annotation["Value"]
        )
        session.add(new_annotation)
        i += 1
    session.commit()
    logging.info("Inserted %d annotations" % i)

logging.info("Run indexing ...")

end = timer()
logging.info("Import completed after " + str((end - start)) + " seconds.")

session.close()

# Query example

# select
# 	c.year,
# 	c."month",
# 	c."day",
# 	count(*)
# from
# 	comments c,
# 	facts f
# where
# 	c.id = f.comment_id
# 	and f.label_id = 7
# 	and f."label" = true
# group by
# 	cube (c."year",
# 	c."month",
# 	c."day")
# order by
# 	c."year",
# 	c."month"
#   c."day";
