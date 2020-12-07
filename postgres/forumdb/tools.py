from typing import Dict, List, Tuple
import forumdb.Constants as Const
import logging
from bson.objectid import ObjectId
import pymongo
import datetime
from tqdm import tqdm


def clear_db(db):
    for collection in Const.MDB_COLLECTION_NAMES:
        db.drop_collection(db[collection])


def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d


def omp_data(sql_conn) -> Dict[str, List[Dict]]:
    """
    Read the whole sqlite db into a dict
    """
    omp: Dict = {}
    for table in Const.SQ_TABLE_NAMES:
        cur = sql_conn.cursor()
        cur.execute(f"SELECT * FROM {table}")
        omp[table] = cur.fetchall()

    return omp


def add_ids_after_input(items: List[Dict], insert_result: pymongo.results.InsertManyResult) -> List[Dict]:
    """
    Adds the _id field to each of the items that were inserted
    :param items: list of items that were inserted
    :param insert_result: insert_many pymongo result
    """
    for item, inserted_id in zip(items, insert_result.inserted_ids):
        item['_id'] = inserted_id
    return items


def write_sources_collection(db):
    """
    Writes the sources collection for OMP
    :param db: mongo db connection
    :returns: the inserted document
    """
    assert db, 'db is not set'

    source_to_insert = {
        "name": "der standard"
    }

    inserted_source = db[Const.SOURCES].insert_one(
        source_to_insert
    )
    source_to_insert['_id'] = inserted_source.inserted_id
    logging.debug(f'Wrote source document:{source_to_insert}')
    return source_to_insert


def write_users_collection(db, posts) -> Tuple[List[Dict], Dict]:
    """
    Writes the users collection for OMP
    :param db: mongo db connection
    :returns: the inserted users as a list
    """
    assert db, 'db is not set'

    # users for the annotations
    # users_to_insert = [
    #     {'external_UserId': 'omp_coder_1', 'username': '1', 'role': 'coder'},
    #     {'external_UserId': 'omp_coder_2', 'username': '2', 'role': 'coder'},
    #     {'external_UserId': 'omp_coder_3', 'username': '3', 'role': 'coder'}
    # ]

    user_ids = set()
    for post in posts:
        user_ids.add(post['ID_User'])

    users_to_insert = []
    for user_id in user_ids:
        users_to_insert.append(
            {
                'external_UserId': f'omp_user_{user_id}',
                'username': user_id,
                'role': 'commenter'
            }
        )

    result = db[Const.USERS].insert_many(users_to_insert)
    logging.debug(f'Wrote users documents:{len(result.inserted_ids)}')
    inserted_users = add_ids_after_input(users_to_insert, result)

    user_id_lookup = {user['username']: user['_id'] for user in inserted_users}

    return inserted_users, user_id_lookup


def write_documents_collection(db, documents: List[Dict]) -> Tuple[List[Dict], Dict]:
    """
    Write the posts to the documents collection
    :param db: mongo db connection
    :param documents: list of dicts with the articles
    :returns: list with the inserted documents
    """
    documents_to_insert = []

    for document in documents:
        document['title'] = document.pop('Title')
        document['markup'] = document.pop('Body')
        document['timestamp'] = datetime.datetime.strptime(
            document.pop('publishingDate'), '%Y-%m-%d %H:%M:%S.%f')
        # meta fields
        document['meta'] = {}
        document['meta']['path'] = document.pop('Path')
        documents_to_insert.append(document)

    result = db[Const.DOCUMENTS].insert_many(documents_to_insert)
    logging.debug(f'Wrote documents documents:{len(result.inserted_ids)}')
    inserted_documents = add_ids_after_input(documents_to_insert, result)

    # create a lookup dictionary for finding the foreign keys
    documents_lookup = {d['ID_Article']: d['_id'] for d in inserted_documents}
    db[Const.DOCUMENTS].update_many(
        {}, {'$unset': {'ID_Article': True}}, False)

    return inserted_documents, documents_lookup


def write_labels_collection(db, labels):
    """
    Write the labels to the labels collection
    :param db: mongo db connection
    :param labels: list of dicts with the labels
    :returns: list with the inserted documents
    """

    new_labels = []
    for label in labels:
        new_label = {}
        new_label['type'] = 'binary'
        category_name = label.get('Name').lower()
        new_label['classname'] = [category_name, 'non-' + category_name]
        new_label['description'] = category_name
        new_label['scale'] = 'ordinal'
        new_label['last_trained'] = None
        new_label['staffId'] = ''
        new_labels.append(new_label)

    result = db[Const.LABELS].insert_many(new_labels)
    logging.debug(f'Wrote labels documents:{len(result.inserted_ids)}')
    inserted_labels = add_ids_after_input(new_labels, result)
    return inserted_labels


def write_comments_collection(db, posts, documents_lookup, annotations, labels, source, user_id_lookup):
    """
    Write the posts to the comments collection
    :param db: mongo db connection
    :param posts: list of dicts with the posts
    :param documents: the documents for the foreign key
    :param annotations: the annotations that need to be added
    :param labels: the labels that exist
    :param source: the source that the dataset belongs to
    :param user_id_lookup: dict for looking up the objectIds for a ID_User
    :returns: list with the inserted documents
    """

    def add_parent_comment_keys(inserted_comments, posts_lookup):
        logging.debug('Looking up parent comment ids...')
        for inserted_comment, post in tqdm(list(zip(inserted_comments, posts))):
            parent_post_id = post.get('ID_Parent_Post', False)
            if parent_post_id:
                inserted_comment['parentCommentId'] = posts_lookup[parent_post_id]

    def add_annotations(posts_lookup, annotations):
        nonlocal labels
        label_id_lookup = {label['description']: label['_id'] for label in labels}
        logging.debug('Adding annotations to comments...')
        for annotation in tqdm(annotations):
            post_id = annotation.get('ID_Post')
            _id = posts_lookup[post_id]
            comment = db[Const.COMMENTS].find_one({'_id': _id})
            labels = comment.get('labels', [])
            label = {
                "labelId": label_id_lookup[annotation['Category'].lower()],
                "classified": 0,
                "confidence": [],
                "manualLabels": [
                    {
                        "annotatorId": '',
                        "label": 1 if int(annotation['Value']) == 1 else 0,
                        "timestamp": ""
                    }
                ]
            }

            labels.append(label)
            db[Const.COMMENTS].update_one(
                {'_id': _id}, {'$set': {'labels': labels}})

    comments = []
    logging.debug('Converting comments...')
    for post in tqdm(posts):
        comment = {}
        # 2015-09-22 22:25:46.360
        comment['timestamp'] = datetime.datetime.strptime(
            post['CreatedAt'], '%Y-%m-%d %H:%M:%S.%f')
        comment['title'] = post['Headline']
        comment['text'] = post['Body']
        comment['parentDocumentId'] = documents_lookup[post['ID_Article']]
        comment['sourceId'] = source['_id']
        comment['userId'] = user_id_lookup[post['ID_User']]

        comment['meta'] = {}
        comment['meta']['positiveVotes'] = post['PositiveVotes']
        comment['meta']['negativeVotes'] = post['NegativeVotes']
        comment['meta']['status'] = post['Status']

        comments.append(comment)

    logging.debug(f'Writing comments initially without parentCommentId...')
    result = db[Const.COMMENTS].insert_many(comments)
    inserted_comments = add_ids_after_input(comments, result)

    # create post id lookup dictionary
    posts_lookup = {post['ID_Post']: inserted_comment['_id']
                    for inserted_comment, post in zip(inserted_comments,  posts)}

    add_parent_comment_keys(inserted_comments, posts_lookup)
    db.drop_collection(db[Const.COMMENTS])
    logging.debug(f'Writing comments with parentCommentId...')
    result = db[Const.COMMENTS].insert_many(comments)
    logging.debug(f'Wrote comments documents:{len(result.inserted_ids)}')

    add_annotations(posts_lookup, annotations)

    return inserted_comments
