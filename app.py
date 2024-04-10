import mysql.connector

def connect_to_database():
    cnx = mysql.connector.connect(
        host='sql6.freemysqlhosting.net',
        user='sql6697893',
        password='5MWWGiNNhA',
        database='sql6697893'
    )
    return cnx

db_conn = connect_to_database()
cursor = db_conn.cursor()

def db_init():
    cursor.execute("SHOW TABLES LIKE 'users'")
    result = cursor.fetchone()

    if not result:
        cursor.execute("""
            CREATE TABLE users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(255),
                email VARCHAR(255),
                password VARCHAR(255)
            )
        """)
    
    cursor.execute("SHOW TABLES LIKE 'url_map'")
    result = cursor.fetchone()

    if not result:
        cursor.execute("""
            CREATE TABLE url_map (
                id INT AUTO_INCREMENT PRIMARY KEY,
                short_url VARCHAR(255),
                long_url VARCHAR(255),
                counter INT,
                user_id INT,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)

def insert_into_users(name, email, password):
    query = "INSERT INTO users (name, email, password) VALUES (%s, %s, %s)"
    values = (name, email, password)
    cursor.execute(query, values)
    db_conn.commit()

def insert_into_url_map(short_url, long_url, counter, user_id):
    query = "INSERT INTO url_map (short_url, long_url, counter, user_id) VALUES (%s, %s, %s, %s)"
    values = (short_url, long_url, counter, user_id)
    cursor.execute(query, values)
    db_conn.commit()
    
def search_short_url(short_url):
    query = "SELECT * FROM url_map WHERE short_url = %s"
    values = (short_url, )
    cursor.execute(query, values)
    result = cursor.fetchone()
    return result is not None

db_init()
insert_into_users('John Doe', 'john@example.com', 'password123')
insert_into_url_map('shortUrl', 'http://example.com/longUrl', 0, 1)

if search_short_url('shortUrl'):
    print('The short_url exists.')
else:
    print('The short_url does not exist.')