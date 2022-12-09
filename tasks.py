import time
import sqlite3


def make_safe(text):
    return text.replace("'", '"')


def ensure_db_exists():
    with sqlite3.connect('tasks.db') as con:
        cur = con.cursor()
        cur.execute('''SELECT name FROM sqlite_master WHERE name == 'tasks';''')
        if len(cur.fetchall()):
            return
        else:
            cur.execute('''
                CREATE TABLE tasks(
                    USER_ID TEXT,
                    TASK_ID_FOR_USER INT,
                    TITLE TEXT,
                    DESCRIPTION TEXT,
                    REMIND_TS INT,
                    REMINDED BOOL,
                    STATUS TEXT
                );
            ''')
            con.commit()
            return


def create_task(user_id, title):
    with sqlite3.connect('tasks.db') as con:
        cur = con.cursor()
        previous_users_task_id = cur.execute(f'''SELECT MAX(TASK_ID_FOR_USER) FROM tasks WHERE USER_ID == '{user_id}';''').fetchone()[0]
        cur_task_id = (previous_users_task_id + 1) if previous_users_task_id else 1
        safe_title = make_safe(title)
        cur.execute(f'''INSERT INTO tasks (USER_ID, TASK_ID_FOR_USER, TITLE, STATUS) VALUES ('{user_id}', {cur_task_id}, '{safe_title}', 'OPENED');''')
        con.commit()
        return cur_task_id


def get_task_list(user_id, mode='active'):
    with sqlite3.connect('tasks.db') as con:
        cur = con.cursor()
        where_clause = ''
        if mode == 'active':
            where_clause = '''AND STATUS == 'OPENED' '''
        if mode == 'closed':
            where_clause = '''AND STATUS == 'CLOSED' '''
        
        task_list = cur.execute(f'''
            SELECT TASK_ID_FOR_USER, 
                TITLE 
            FROM tasks 
            WHERE USER_ID == '{user_id}'
                {where_clause};
        ''').fetchall()
        return '\n'.join(f'{task_id}. {title}' for task_id, title in task_list)


def update_field(user_id, task_id, field_name, field_value):
    with sqlite3.connect('tasks.db') as con:
        cur = con.cursor()
        safe_field = make_safe(field_value)
        task = cur.execute(f'''SELECT TASK_ID_FOR_USER FROM tasks WHERE USER_ID == '{user_id}' AND TASK_ID_FOR_USER == {task_id}''').fetchone()[0]
        if task:
            cur.execute(f'''UPDATE tasks SET {field_name} == '{safe_field}' WHERE USER_ID == '{user_id}' AND TASK_ID_FOR_USER == {task_id}''')
            con.commit()
            return 1
        return 0


def get_actual_reminds():
    with sqlite3.connect('tasks.db') as con:
        cur = con.cursor()
        now = int(time.time())
        for row in cur.execute(f'''SELECT USER_ID, TITLE, DESCRIPTION, TASK_ID_FOR_USER FROM tasks WHERE REMIND_TS <= {now} AND (NOT REMINDED OR REMINDED IS NULL);''').fetchall():
            cur.execute(f'''UPDATE tasks SET REMINDED=TRUE WHERE USER_ID == '{row[0]}' AND TASK_ID_FOR_USER == {row[3]};''')
            yield {'user_id': row[0], 'title': row[1], 'description': row[2]}