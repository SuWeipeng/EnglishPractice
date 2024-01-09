import sqlite3
import os

def update_db_include_word_and_set_id_as_primary_key(source_db_path):
    conn = sqlite3.connect(source_db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()

    for table in tables:
        table_name = table[0]

        # 获取所有列的名称和数据类型，包括原主键 'word'
        cursor.execute(f"PRAGMA table_info({table_name});")
        column_definitions = [(col[1], col[2]) for col in cursor.fetchall()]

        # 排除已存在的 'id' 列，因为我们将重新创建它
        column_definitions = [(name, type) for name, type in column_definitions if name != 'id']

        # 创建临时表，'id' 作为第一列
        column_definitions_string = ', '.join([f"{name} {type}" for name, type in column_definitions])
        cursor.execute(f"CREATE TABLE temp_{table_name} (id INTEGER PRIMARY KEY AUTOINCREMENT, {column_definitions_string});")

        # 将原始表中的数据复制到临时表中
        column_names_string = ', '.join([name for name, type in column_definitions])
        cursor.execute(f"INSERT INTO temp_{table_name} ({column_names_string}) SELECT {column_names_string} FROM {table_name};")

        # 删除原始表
        cursor.execute(f"DROP TABLE {table_name};")

        # 将临时表重命名为原始表名
        cursor.execute(f"ALTER TABLE temp_{table_name} RENAME TO {table_name};")

    conn.commit()
    conn.close()

    print(f"Database '{source_db_path}' has been updated: 'id' columns are now the first column and primary keys, including 'word' content.")

# 示例用法
db_path = 'Ebbinghaus.db'
update_db_include_word_and_set_id_as_primary_key(db_path)