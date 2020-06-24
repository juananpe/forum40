from enum import Enum

## USERS
COUNT_USERS = "SELECT COUNT(*) FROM users;"
SELECT_USER_BY_ID = lambda x: f"SELECT * FROM users WHERE id = {x} fetch first 1 rows only;"
SELECT_USER_ID_BY_USER_NAME = "SELECT id FROM users WHERE name = %s fetch first 1 rows only;"
## Sources
COUNT_SOURCES = "SELECT COUNT(*) FROM sources;"

## Documents
COUNT_DOCUMENTS = "SELECT COUNT(*) FROM documents;"

## Annotations
COUNT_ANNOTATIONS = "SELECT COUNT(*) FROM annotations;"
SELECT_ANNOTATION_BY_COMMENTID = lambda x : f"SELECT label_id, user_id, label FROM annotations WHERE comment_id = {x}"
SELECT_LABEL_FROM_ANNOTATIONS_BY_IDS = lambda label_id, comment_id, user_id: f"SELECT label FROM annotations WHERE label_id = {label_id} AND comment_id = {comment_id} AND user_id = '{user_id}';"
INSERT_ANNOTATION = lambda label_id, comment_id, user_id, label: f"INSERT INTO annotations (label_id, comment_id, user_id, label) VALUES ({label_id}, {comment_id}, {user_id}, {label})"
UPDATE_ANNOTATION = lambda label_id, comment_id, user_id, label: f"UPDATE annotations SET label = {label} WHERE label_id = {label_id} AND comment_id = {comment_id} AND user_id = '{user_id}'"
SELECT_USERS_ANNOTATION = "SELECT a.label, a.label_id, a.comment_id FROM annotations a WHERE user_id='%s' and label_id in %s and comment_id in %s"


## Labels
COUNT_LABELS = "SELECT COUNT(*) FROM labels"
COUNT_LABELS_BY_NAME = lambda x: f"SELECT COUNT(*) FROM labels WHERE name = '{x}';"

SELECT_LABEL_BY_ID = lambda x: f"SELECT id FROM labels WHERE id = {x} fetch first 1 rows only;"
SELECT_NAMES_FROM_LABES = lambda source_id: f"SELECT name FROM labels where labels.source_id = {source_id}"
SELECT_IDS_FROM_LABES = lambda source_id: f"SELECT id FROM labels where labels.source_id = {source_id}"
SELECT_ID_FROM_LABELS_BY_NAME = lambda x : f"SELECT id FROM labels WHERE name = '{x}';"
SELECT_MAX_ID = lambda table: f"SELECT MAX(id) FROM {table}"

INSERT_LABEL = lambda id_, type_, name, source_id : f"INSERT INTO labels (id, type, name, source_id) VALUES({id_}, '{type_}', '{name}', {source_id})" 

## Auth
SELECT_PASSWORD_BY_NAME = lambda x: (f"SELECT password, id FROM users WHERE name = %s;", (x,))

## Comments
SELECT_COMMENTS_BY_ID = lambda x: f"select * from comments where id = {x}"
SELECT_COMMENT_BY_ID =  lambda x: f"SELECT * FROM comments WHERE id = {x} fetch first 1 rows only"
GET_PARENT_BY_CHILD = lambda id: f'SELECT id, text, title, user_id, year, month, day FROM comments p, (SELECT parent_comment_id FROM comments c WHERE id = {id}) as c WHERE p.id = c.parent_comment_id;'

GROUP_COMMENTS_BY_DAY = lambda label, keywords, source_id: f"""
            SELECT day, month, year, Count(*) FROM 
                (SELECT DISTINCT comment_id FROM facts {opt_where(label)} {opt_label_selection_single(label)} {opt_and_label_eq_true(label)}) AS a, 
                (SELECT id AS comment_id, year, month, day FROM comments {opt_where(keywords or source_id)} 
                    {opt_keyword_section(keywords)} {opt_and(keywords and source_id)} {opt_source_id_section(source_id)}) AS c 
            WHERE a.comment_id = c.comment_id
            GROUP BY year, month, day
            ORDER BY year
            """
GROUP_COMMENTS_BY_MONTH = lambda label, keywords, source_id: f"""
            SELECT month, year, Count(*) FROM 
                (SELECT DISTINCT comment_id FROM facts {opt_where(label)} {opt_label_selection_single(label)} {opt_and_label_eq_true(label)}) AS a, 
                (SELECT id AS comment_id, year, month FROM comments {opt_where(keywords or source_id)} 
                    {opt_keyword_section(keywords)} {opt_and(keywords and source_id)} {opt_source_id_section(source_id)}) AS c 
            WHERE a.comment_id = c.comment_id
            GROUP BY year, month
            ORDER BY year
            """
GROUP_COMMENTS_BY_YEAR = lambda label, keywords, source_id: f"""
            SELECT year, Count(*) FROM 
                (SELECT DISTINCT comment_id FROM facts {opt_where(label)} {opt_label_selection_single(label)} {opt_and_label_eq_true(label)}) AS a, 
                (SELECT id AS comment_id, year FROM comments{opt_where(keywords or source_id)} 
                    {opt_keyword_section(keywords)} {opt_and(keywords and source_id)} {opt_source_id_section(source_id)}) AS c 
            WHERE a.comment_id = c.comment_id
            GROUP BY year
            ORDER BY year
            """

GROUP_ALL_COMMENTS_BY_DAY = lambda keywords, source_id: f'''
        SELECT day, month, year, Count(*) FROM comments
            {opt_where(keywords or source_id)}  {opt_keyword_section(keywords)}
                    {opt_and(keywords and source_id)} {opt_source_id_section(source_id)}
            GROUP BY year, month, day
            ORDER BY year
'''

GROUP_ALL_COMMENTS_BY_MONTH = lambda keywords, source_id: f'''
        SELECT month, year, Count(*) FROM comments
            {opt_where(keywords or source_id)}  {opt_keyword_section(keywords)}
                    {opt_and(keywords and source_id)} {opt_source_id_section(source_id)}
            GROUP BY year, month
            ORDER BY year
'''
GROUP_ALL_COMMENTS_BY_YEAR = lambda keywords, source_id: f'''
        SELECT year, Count(*) FROM comments
            {opt_where(keywords or source_id)}  {opt_keyword_section(keywords)}
                    {opt_and(keywords and source_id)} {opt_source_id_section(source_id)}
            GROUP BY year
            ORDER BY year
'''

GET_COMMENTS_BY_FILTER_draft = lambda labels, keywords, source_ids, skip, limit: f"""
            select c.id, c.title, c.text, c.timestamp from
                (
                    select distinct coalesce(a.comment_id, f.comment_id) as id from 
                        (select distinct comment_id, label_id from facts {opt_where(labels)} {opt_label_selection(labels)} {opt_and_label_eq_true(labels)} ) as a
                        full outer join
                        (select distinct comment_id, label_id from annotations {opt_where(labels)} {opt_label_selection(labels)} {opt_and_label_eq_true(labels)} ) as f
                        on a.comment_id = f.comment_id and a.label_id = f.label_id
                        order by id
                        limit {limit} offset {skip}
                ) a,
                (select * from comments {opt_where(keywords or source_ids)} {opt_keyword_section(keywords)} {opt_and(keywords and source_ids)} {opt_source_section(source_ids)}) as c
                where a.id = c.id
            """

GET_UNLABELED_COMMENTS_BY_FILTER = lambda labels, keywords, source_ids, skip, limit: f"""
            select c.id, c.title, c.text, c.timestamp from comments c 
            where 
                {opt_keyword_section(keywords)} {opt_and(keywords and source_ids)} {opt_source_section(source_ids, "c.")}
                {opt_and(keywords or source_ids)}
            	not exists ( select * from annotations a where c.id = a.comment_id {opt_and(labels)} {opt_label_selection(labels)} )
            	and 
            	not exists ( select * from facts f where c.id = f.comment_id {opt_and(labels)} {opt_label_selection(labels)} )
            limit {limit} offset {skip}
            """

GET_ANNOTATIONS_BY_FILTER = lambda ids, labels, user_id: f"""
            select coalesce(a.comment_id, f.comment_id) as comment_id, coalesce(a.label_id, f.label_id) as label_id, a.count_true as group_count_true, 
            a.count_false as group_count_false, f.label as ai, f.confidence as ai_pred {opt_user_sec_head(user_id)} from 
            (
                select comment_id, label_id, count(label or null) as count_true, count(not label or null) as count_false
                from annotations {opt_where(labels)} {opt_label_selection(labels)} {opt_and(ids)} {opt_comments_section(ids)} 
                group by comment_id, label_id
            ) a
            full outer join 
            (
                select * from facts {opt_where(labels)} {opt_label_selection(labels)} {opt_and(ids)} {opt_comments_section(ids)} 
            ) f
            ON a.comment_id = f.comment_id and a.label_id = f.label_id
            {opt_user_sec_body(user_id)}
            order by a.comment_id, a.label_id
            """

COUNT_COMMENTS_BY_FILTER = lambda labels, keywords, source_ids: f"""
            select count(*) from
            (
                select * from comments {opt_where(keywords or source_ids)} {opt_keyword_section(keywords)} {opt_and(keywords and source_ids)} {opt_source_section(source_ids)}
            ) as c
            inner join 
            (
                select coalesce(l.cid_a, l.cid_f) as comment_id from 
                (
                    (
                        select distinct comment_id as cid_a from annotations {opt_where(labels)} {opt_label_selection(labels)} {opt_and_label_eq_true(labels)} 
                    ) as a
                    full outer join
                    (
                        select distinct comment_id as cid_f from facts {opt_where(labels)} {opt_label_selection(labels)} {opt_and_label_eq_true(labels)} 
                    ) as f on a.cid_a = f.cid_f
                ) as l
                order by comment_id
            ) _ 
            on c.id = _.comment_id
            """

#GET_COMMENTS_BY_FILTER = lambda labels, keywords, source_ids, skip, limit: f"""
#            select distinct c.id, c.title, c.text, c.timestamp
#            from 
#            (select * from comments {opt_where(keywords or source_ids)} {opt_keyword_section(keywords)} {opt_and(keywords and source_ids)} {opt_source_section(source_ids)} ) c
#            right join 
#                (
#                    select coalesce(a.comment_id, f.comment_id) as id
#                    from annotations a 
#                    full join facts f on
#                    a.comment_id = f.comment_id and a.label_id = f.label_id
#                    where ( a."label" or f."label") {opt_label_coalesce_AF_in(labels)}
#                
#                    limit {limit} offset {skip}
#                ) l
#            on c.id = l.id
#            order by c.id
#            """
    
class Order(Enum):
    ASC = 1
    DESC = 2
    UNCERTAIN = 0

def GET_ALL_COMMENTS(num_keywords):
    query = f"""select c.id, c.title, c.text, c.timestamp
    from comments c
    where c.source_id = %s
    """
    for _ in range(num_keywords):
        query+= " and text like %s "

    query += f"""
    order by c.timestamp DESC
    limit %s offset %s
    """
    return query

def GET_COMMENT_IDS_BY_FILTER(label_sort_id, order, label_ids, num_keywords):
    """
    Returns the query for getting comment ids
    :param label_sort_id: label_id to sort or None, if none sort for date
    :param order: ordering
    :param num_keywords: number of keywords
    """
    query = f"""
    select c.id, c.title, c.text, c.timestamp, f.confidence, f.label_id from comments c, facts f
    where c.id = f.comment_id
    and source_id = %s"""

    if label_ids:
        query+=" and f.label_id = %s"
    
    for _ in range(num_keywords):
        query+= " and text like %s"

    if label_sort_id:
        if Order(order) == Order.ASC:
            query+= " order by f.confidence ASC"
        elif Order(order) == Order.DESC:
            query+= " order by f.confidence DESC"
        else:
            query+= " order by uncertaintyorder DESC"
    else:
        query+= " order by c.timestamp DESC"

    query+=f" limit %s offset %s"
    return query

def GET_RUNNING_TRAINING():
    return """
    select COUNT(*) from model where label_id = %s and pid IS NOT NULL;
    """

def GET_MODEL_INFO():
    return """
    select * from model where label_id = %s;
    """

def GET_FACTS():
    return """select f.comment_id, f.label_id, f.confidence
    from facts f
    where f.comment_id in %s
    and f.label_id in %s"""

def GET_ANNOTATIONS():
    return """
    select a.comment_id, a.label_id, count(a.label or null) as count_true, count(not a.label or null) as count_false 
    from annotations a
    where a.comment_id in %s
    and a.label_id in %s
    group by a.comment_id, a.label_id
    """

def GET_ANNOTATED_COMMENTS():
    return """
    SELECT 
    count(case when label=true then 1 end) pos,
    count(case when label=false then 1 end) neg
    FROM comments c JOIN annotations a ON c.id=a.comment_id
    WHERE a.label_id=%s and c.embedding is not NULL
    """

def GET_PREVIOUS_NUMBER_TRAINING_SAMPLES():
    return """
    select number_training_samples from model where label_id = %s;
    """

def GET_LABEL_INFO():
    return "SELECT name, source_id FROM labels WHERE id=%s"

### utility

def _opt_keyword(cond, keyword):
    return keyword if cond else ''

def opt_where(cond):
    return _opt_keyword(cond, 'where')

def opt_and(cond):
    return _opt_keyword(cond, 'and')

def opt_comments_section(ids):
    return f"comment_id in ({', '.join(ids) })" if ids else ''

def opt_source_id_section(source_id):
    return f' source_id = {source_id} '

def opt_source_section(ids, prefix = ''):
    return f"{prefix}source_id in ({', '.join(ids) })" if ids else ''

def opt_label_selection(labels):
    return f'label_id IN ({", ".join(i for i in labels)})' if labels else ''

def opt_label_coalesce_AF_in(labels):
    return f'and coalesce(a.label_id, f.label_id) iN ({", ".join(i for i in labels)})' if labels else ''

def opt_label_selection_single(label):
    return f'label_id = {label}' if label else ''

def opt_and_label_eq_true(labels):
    return 'and label = True' if labels else ''

def opt_keyword_section(keywords):
    return ' OR '.join(f"text LIKE '%{x}%'" for x in keywords) if keywords else ''

def opt_user_sec_head(user_id):
    return ', a2.label as user' if user_id else ''

def opt_user_sec_body(user_id):
    return f"""
        left join annotations a2
        on a.comment_id = a2.comment_id and a.label_id = a2.label_id and user_id = '{user_id}'
        """ if user_id else ''