import pymysql.cursors

class MySQLConnection:
    def __init__(self, db):
        self.connection = pymysql.connect(
            host = 'localhost',
            user = 'root',
            password = 'root', 
            db = db,
            charset = 'utf8mb4',
            cursorclass = pymysql.cursors.DictCursor,
            autocommit = True
        )

    def query_db(self, query, data=None):
        with self.connection.cursor() as cursor:
            try:
                query = cursor.mogrify(query, data)
                print("Running Query:", query)
                cursor.execute(query)
                if query.lower().startswith("select"):
                    return cursor.fetchall()
                self.connection.commit()
                if query.lower().startswith("insert"):
                    return cursor.lastrowid
            except Exception as e:
                print("Something went wrong", e)
                return False
            finally:
                self.connection.close()

def connectToMySQL(db):
    return MySQLConnection(db)