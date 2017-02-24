import pymssql
from os import getenv

SQL_SERVER = getenv("HP_SQL_SERVER")
SQL_USER = getenv("HP_SQL_USER")
SQL_PASSWORD = getenv("HP_SQL_PASSWORD")

SQL_DB = "POCCLoud"
SQL_TABLE = "Production"


def main(test_mode=False):
    if (not SQL_SERVER or not SQL_USER or not SQL_PASSWORD) and not test_mode:
        print("Be sure to set the SQL Server, username, and password as enviroment variables HP_SQL_SERVER, HP_SQL_USER, and HP_SQL_PASSWORD")
        exit()

    conn = pymssql.connect(SQL_SERVER, SQL_USER, SQL_PASSWORD, SQL_DB)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM Production WHERE id > 0")
    conn.commit()

    cursor.execute("SELECT * FROM Production")
    row = cursor.fetchone()
    while row:
        print(row)
        row = cursor.fetchone()

    conn.close()


if __name__ == '__main__':
    main()
