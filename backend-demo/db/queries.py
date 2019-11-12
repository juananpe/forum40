## USERS
COUNT_USERS = "SELECT COUNT(*) FROM users;"
SELECT_USER_BY_ID = lambda x: f"SELECT * FROM users WHERE id = {x} fetch first 1 rows only;"

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

## Labels
COUNT_LABELS = "SELECT COUNT(*) FROM labels"
COUNT_LABELS_BY_NAME = lambda x: f"SELECT COUNT(*) FROM labels WHERE name = '{x}';"

SELECT_LABEL_BY_ID = lambda x: f"SELECT id FROM labels WHERE id = {x} fetch first 1 rows only;"
SELECT_NAMES_FROM_LABES = lambda source_id: f"SELECT name FROM labels where labels.source_id = {source_id}"
SELECT_IDS_FROM_LABES = lambda source_id: f"SELECT id FROM labels where labels.source_id = {source_id}"
SELECT_ID_FROM_LABELS_BY_NAME = lambda x : f"SELECT id FROM labels WHERE name = '{x}';"
SELECT_MAX_LABELID = "SELECT MAX(id) FROM labels"

INSERT_LABEL = lambda id_, type_, name, source_id : f"INSERT INTO labels (id, type, name, source_id) VALUES({id_}, '{type_}', '{name}', {source_id})" 

## Auth
SELECT_PASSWORD_BY_NAME = lambda x: (f"SELECT password FROM users WHERE name = %s;", (x,))

## Comments
SELECT_COMMENTS_BY_ID = lambda x: f"select * from comments where id = {x}"
SELECT_COMMENT_BY_ID =  lambda x: f"SELECT * FROM comments WHERE id = {x} fetch first 1 rows only"
GET_PARENT_BY_CHILD = lambda id: f'SELECT id, text, title, user_id, year, month, day FROM comments p, (SELECT parent_comment_id FROM comments c WHERE id = {id}) as c WHERE p.id = c.parent_comment_id;'
GROUP_COMMENTS_BY_DAY = lambda label, keywords: f"""
            SELECT day, month, year, Count(*) FROM 
                (SELECT DISTINCT comment_id FROM annotations {opt_label_selection_single(label)} {opt_and_label_eq_true(label)}) AS a, 
                (SELECT id AS comment_id, year, month, day FROM comments {opt_keyword_section(keywords)}) AS c 
            WHERE a.comment_id = c.comment_id
            GROUP BY year, month, day
            ORDER BY year
            """
GROUP_COMMENTS_BY_MONTH = lambda label, keywords: f"""
            SELECT month, year, Count(*) FROM 
                (SELECT DISTINCT comment_id FROM annotations {opt_label_selection_single(label)} {opt_and_label_eq_true(label)}) AS a, 
                (SELECT id AS comment_id, year, month FROM comments {opt_keyword_section(keywords)}) AS c 
            WHERE a.comment_id = c.comment_id
            GROUP BY year, month
            ORDER BY year
            """
GROUP_COMMENTS_BY_YEAR = lambda label, keywords: f"""
            SELECT year, Count(*) FROM 
                (SELECT DISTINCT comment_id FROM annotations {opt_label_selection_single(label)} {opt_and_label_eq_true(label)}) AS a, 
                (SELECT id AS comment_id, year FROM comments {opt_keyword_section(keywords)}) AS c 
            WHERE a.comment_id = c.comment_id
            GROUP BY year
            ORDER BY year
            """

GET_COMMENTS_BY_FILTER = lambda labels, keywords,  skip, limit: f"""
            select c.id, c.title, c.text, c.timestamp from
                (
                    select distinct coalesce(a.comment_id, f.comment_id) as id from 
                        (select distinct comment_id, label_id from facts {opt_label_selection(labels)} ) as a
                        full outer join
                        (select distinct comment_id, label_id from annotations {opt_label_selection(labels)}  ) as f
                        on a.comment_id = f.comment_id and a.label_id = f.label_id
                        order by id
                        limit {limit} offset {skip}
                ) a,
                (select * from comments {opt_keyword_section(keywords)}) as c
                where a.id = c.id
            """

GET_ANNOTATIONS_BY_FILTER = lambda ids, labels, user_id: f"""
            select coalesce(a.comment_id, f.comment_id) as comment_id, coalesce(a.label_id, f.label_id) as label_id, a.count_true as group_count_true, 
            a.count_false as group_count_false, f.label as ai, f.confidence as ai_pred {opt_user_sec_head(user_id)} from 
            (
                select comment_id, label_id, count(label or null) as count_true, count(not label or null) as count_false
                from annotations {opt_label_selection(labels)} {opt_and(ids)} {opt_comments_section(ids)} 
                group by comment_id, label_id
            ) a
            full outer join 
            (
                select * from facts {opt_label_selection(labels)} {opt_and(ids)} {opt_comments_section(ids)} 
            ) f
            ON a.comment_id = f.comment_id and a.label_id = f.label_id
            {opt_user_sec_body(user_id)}
            order by a.comment_id, a.label_id
            """

COUNT_COMMENTS_BY_FILTER = lambda labels, keywords: f"""
            select count(*) from
            (
                select * from comments {opt_keyword_section(keywords)}
            ) as c
            inner join 
            (
                select coalesce(l.cid_a, l.cid_f) as comment_id from 
                (
                    (
                        select distinct comment_id as cid_a from annotations {opt_label_selection(labels)}
                    ) as a
                    full outer join
                    (
                        select distinct comment_id as cid_f from facts {opt_label_selection(labels)}
                    ) as f on a.cid_a = f.cid_f
                ) as l
                order by comment_id
            ) _ 
            on c.id = _.comment_id
            """

### utility

def _opt_keyword(cond, keyword):
    return keyword if cond else ''

def opt_where(cond):
    return _opt_keyword(cond, 'where')

def opt_and(cond):
    return _opt_keyword(cond, 'and')

def opt_comments_section(ids):
    return f"comment_id in ({', '.join(ids) })" if ids else ''

def opt_label_selection(labels):
    return f'where label_id IN ({", ".join(i for i in labels)})' if labels else ''

def opt_label_selection_single(label):
    return f'where label_id = {label}' if label else ''

def opt_and_label_eq_true(labels):
    return 'and label = True' if labels else ''

def opt_keyword_section(keywords):
    return ' where ' + ' OR '.join(f"text LIKE '%{x}%'" for x in keywords) if keywords else ''

def opt_user_sec_head(user_id):
    return ', a2.label as user' if user_id else ''

def opt_user_sec_body(user_id):
    return f"""
        left join annotations a2
        on a.comment_id = a2.comment_id and a.label_id = a2.label_id and user_id = '{user_id}'
        """ if user_id else ''