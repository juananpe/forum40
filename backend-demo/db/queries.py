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
SELECT_LABEL_FROM_ANNOTATIONS_BY_IDS = lambda label_id, comment_id, user_id: "SELECT label FROM annotations WHERE label_id = {label_id} AND comment_id = {comment_id} AND user_id = '{user_id}';"
INSERT_ANNOTATION = lambda label_id, comment_id, user_id, label: f"INSERT INTO annotations (label_id, comment_id, user_id, label) VALUES ({label_id}, {comment_id}, {user_id}, {label})"
UPDATE_ANNOTATION = lambda label_id, comment_id, user_id, label: f"UPDATE annotations SET label = {label} WHERE label_id = {label_id} AND comment_id = {comment_id} AND user_id = '{user_id}'"

## Labels
COUNT_LABELS = "SELECT COUNT(*) FROM labels"
COUNT_LABELS_BY_NAME = lambda x: f"SELECT COUNT(*) FROM labels WHERE name = '{x}';"

SELECT_LABEL_BY_ID = lambda x: f"SELECT id FROM labels WHERE id = {x} fetch first 1 rows only;"
SELECT_NAMES_FROM_LABES = "SELECT name FROM labels"
SELECT_IDS_FROM_LABES = "SELECT id FROM labels"
SELECT_ID_FROM_LABELS_BY_NAME = lambda x : f"SELECT id FROM labels WHERE name = '{x}';"
SELECT_MAX_LABELID = "SELECT MAX(id) FROM labels"

INSERT_LABEL = lambda id_, type_, name : f"INSERT INTO labels (id, type, name) VALUES({id_}, '{type_}', '{name}')" 

## Auth
SELECT_PASSWORD_BY_NAME = lambda x: f"SELECT password FROM users WHERE name = '{x}';"

## Comments
SELECT_COMMENT_BY_ID =  lambda x: f"SELECT * FROM comments WHERE id = {x} fetch first 1 rows only"
GROUP_COMMENTS_BY_DAY = lambda sub_a, sub_c: f"""
            SELECT day, month, year, Count(*) FROM 
                (SELECT DISTINCT comment_id FROM annotations {sub_a}) AS a, 
                (SELECT id AS comment_id, year, month, day FROM comments {sub_c}) AS c 
            WHERE a.comment_id = c.comment_id
            GROUP BY year, month, day
            ORDER BY year
            """
GROUP_COMMENTS_BY_MONTH = lambda sub_a, sub_c: f"""
            SELECT month, year, Count(*) FROM 
                (SELECT DISTINCT comment_id FROM annotations {sub_a}) AS a, 
                (SELECT id AS comment_id, year, month FROM comments {sub_c}) AS c 
            WHERE a.comment_id = c.comment_id
            GROUP BY year, month
            ORDER BY year
            """
GROUP_COMMENTS_BY_YEAR = lambda sub_a, sub_c: f"""
            SELECT year, Count(*) FROM 
                (SELECT DISTINCT comment_id FROM annotations {sub_a}) AS a, 
                (SELECT id AS comment_id, year FROM comments {sub_c}) AS c 
            WHERE a.comment_id = c.comment_id
            GROUP BY year
            ORDER BY year
            """