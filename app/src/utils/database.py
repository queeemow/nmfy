import psycopg2
import uuid
class DataBase:
    connection = None
    cursor = None
    add_data_query = None

    def __init__(self) -> None:
        try:
            self.connect()
            print('all good')
            print("Информация о сервере PostgreSQL")
            print(self.connection.get_dsn_parameters(), "\n")
            self.cursor.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp";')
            self.create_table()
        except Exception as e:
            print(e)
        pass
    
    def create_table(self):
        print("create table")
        try:
            user_table_query = '''CREATE TABLE IF NOT EXISTS users (
                                id uuid PRIMARY key NOT NULL,
                                telegram_user_id VARCHAR NOT NULL unique,
                                telegram_username VARCHAR
                            ); '''
            chat_table_query = '''CREATE TABLE IF NOT EXISTS chat (
                                id uuid PRIMARY key NOT NULL,
                                date_time_of_request TIMESTAMP NOT NULL, 
                                telegram_chat_id VARCHAR NOT NULL,
                                user_id uuid,
                                foreign key (user_id) references users(id)
                            ); '''
            files_table_query = '''CREATE TABLE IF NOT EXISTS files (
                                id uuid PRIMARY key NOT NULL,
                                request_url VARCHAR NOT NULL,
                                video_or_audio VARCHAR NOT NULL,
                                file_size VARCHAR NOT NULL, 
                                status VARCHAR NOT NULL, 
                                time_elapsed VARCHAR NOT NULL,
                                chat_id uuid,
                                foreign key (chat_id) references chat(id)
                            ); '''
            create_enum = """DO $$
                                BEGIN
                                    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'provider_enum') THEN
                                        CREATE TYPE provider_enum AS ENUM
                                        (
                                           'youtube', 'instagram'
                                        );
                                END IF;
                            END$$;
                            """
            provider_table_query = '''CREATE TABLE IF NOT EXISTS provider (
                                        id uuid PRIMARY key NOT NULL,
                                        provider provider_enum,
                                        file_id uuid,
                                        foreign key (file_id) references files(id)
                                    ); '''
            self.cursor.execute(user_table_query)
            self.cursor.execute(chat_table_query)
            self.cursor.execute(files_table_query)
            self.cursor.execute(create_enum)
            self.cursor.execute(provider_table_query)
            self.connection.commit()
        except Exception as e:
            self.cursor.execute(user_table_query)
            self.cursor.execute(chat_table_query)
            self.cursor.execute(files_table_query)
            self.cursor.execute(provider_table_query)
            self.connection.commit()
            print(e)

    def add_data(self, user_data):
        user_uuid = uuid.uuid4()
        chat_uuid = uuid.uuid4()
        file_uuid = uuid.uuid4()
        provider_uuid = uuid.uuid4()
        try:
            self.add_user_and_chat_query = f"""
            WITH new_user AS (
                INSERT INTO users (id, telegram_user_id, telegram_username)
                VALUES ('{user_uuid}', '{user_data['user_id']}', '{user_data['username']}') 
                ON CONFLICT (telegram_user_id) DO UPDATE
                SET id = users.id
                RETURNING id
            ) 
            INSERT INTO chat (id, date_time_of_request, 
                telegram_chat_id,
                user_id)
                SELECT '{chat_uuid}', '{user_data['date_time_of_request']}', '{user_data['chat_id']}', id
                FROM new_user;
                """
        
            self.add_files_query = f"""INSERT INTO files(
                id,
                video_or_audio,
                request_url,
                file_size, 
                status, 
                time_elapsed,
                chat_id
                )
                VALUES('{file_uuid}',
                '{user_data['video_or_audio']}',
                '{user_data['request_url']}',
                '{user_data['file_size']}',
                '{user_data['status']}',
                '{user_data['time_elapsed']}',
                '{chat_uuid}'
                );
                """
            self.add_provider_query = f"""INSERT INTO provider(
                id,
                provider,
                file_id
                )
                VALUES('{provider_uuid}',
                '{user_data['provider']}',
                '{file_uuid}'
                );
                """
            self.cursor.execute(self.add_user_and_chat_query)
            self.cursor.execute(self.add_files_query)
            self.cursor.execute(self.add_provider_query)
            self.connection.commit()
            print("user has been added to the tables successfully")
        except Exception as e:
            print(e)

    def connect(self):
        try:
            self.connection = psycopg2.connect(dbname='nmfy', user='postgres', 
                                password='1405', host='localhost')
            self.cursor = self.connection.cursor()
            print("Information on PostgreSQL server")
            print(self.connection.get_dsn_parameters(), "\n")
        except Exception as e:
            print(e)

    def select_all(self):
        try:
            select_all_qeury = "SELECT * FROM userdata;"
            self.cursor.execute(select_all_qeury)
            self.connection.commit()
        except Exception as e:
            print(e)
        self.close_conection()

    def close_conection(self):
        if self.cursor:
            self.cursor.close()
            self.connection.close()
            print("Connection with PostgreSQL was closed")

    def drop_table(self):
        try:
            droptable_users_query = "DROP TABLE users;"
            droptable_files_query = "DROP TABLE files;"
            droptable_provider_query = "DROP TABLE provider;"
            droptable_chat_query = "DROP TABLE chat;"

            self.cursor.execute(droptable_chat_query)
            self.cursor.execute(droptable_files_query)
            self.cursor.execute(droptable_users_query)
            self.cursor.execute(droptable_provider_query)
            self.connection.commit()
        except Exception as e:
            print(e)

# db = DataBase()
# db.create_table()
# db.add_data({})