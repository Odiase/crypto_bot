import psycopg2
from urllib.parse import urlparse, parse_qs, unquote
import time




class TokenDatabase:
    def __init__(self, max_retries=5, retry_delay=5):
        '''Initialize Database Connection with Retry Mechanism'''
        # Parse the connection URL
        self.config = self.parse_db_url("postgresql://elontrustsdb3_user:V2GclU6nnhoYFM9Mn1w9qHiXv6z1iQze@dpg-csvl53l6l47c73do62dg-a.oregon-postgres.render.com/elontrustsdb3", ssl_require=True)
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.conn = self.connect_with_retry()

    def parse_db_url(self, url, ssl_require=False):
        parsed_config = {}

        spliturl = urlparse(url)

        path = spliturl.path[1:]
        query = parse_qs(spliturl.query)

        hostname = spliturl.hostname or ""
        if "%" in hostname:
            hostname = spliturl.netloc
            if "@" in hostname:
                hostname = hostname.rsplit("@", 1)[1]
            hostname = unquote(hostname)

        port = spliturl.port

        parsed_config.update(
            {
                "NAME": unquote(path or ""),
                "USER": unquote(spliturl.username or ""),
                "PASSWORD": unquote(spliturl.password or ""),
                "HOST": hostname,
                "PORT": port or 5432,
            }
        )

        if ssl_require:
            parsed_config["sslmode"] = "require"

        return parsed_config

    def connect_with_retry(self):
        '''Attempt to establish a database connection with retries'''
        attempt = 0
        while attempt < self.max_retries:
            try:
                conn = psycopg2.connect(
                    database=self.config["NAME"],
                    user=self.config["USER"],
                    password=self.config["PASSWORD"],
                    host=self.config["HOST"],
                    port=self.config["PORT"],
                    sslmode=self.config.get("sslmode", "")
                )
                return conn
            except psycopg2.OperationalError as e:
                print(f"Attempt {attempt + 1} failed: {e}")
                attempt += 1
                time.sleep(self.retry_delay)
        raise Exception("Max retries exceeded, failed to connect to the database")

    def create_token_record_table(self):
        '''Drop and recreate the table to ensure constraints'''
        cur = self.conn.cursor()
        # Drop the table if it already exists
        cur.execute("DROP TABLE IF EXISTS token_records;")
        # Recreate the table with the correct UNIQUE constraint
        cur.execute("""
            CREATE TABLE token_records (
                id SERIAL PRIMARY KEY,
                contract_address VARCHAR(200) NOT NULL UNIQUE,  -- Add UNIQUE constraint
                buy_status VARCHAR(10) DEFAULT 'UNBOUGHT',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        self.conn.commit()
        cur.close()



    def check_buy_status(self, contract_address):
        '''Check the buy status of a token by its contract address'''
        cur = self.conn.cursor()
        cur.execute("""
            SELECT buy_status FROM token_records WHERE contract_address = %s;
        """, (contract_address,))
        result = cur.fetchone()
        cur.close()
        if result:
            return result[0] == 'BOUGHT'
        return False

    def register_token_record(self, contract_address):
        '''Register a new token record'''
        cur = self.conn.cursor()
        cur.execute("""
            INSERT INTO token_records (contract_address) VALUES (%s)
            ON CONFLICT (contract_address) DO NOTHING;
        """, (contract_address,))
        self.conn.commit()
        cur.close()

    def set_token_as_bought(self, contract_address):
        '''Set the buy status of a token to "BOUGHT" by its contract address'''
        cur = self.conn.cursor()
        cur.execute("""
            UPDATE token_records
            SET buy_status = 'BOUGHT'
            WHERE contract_address = %s;
        """, (contract_address,))
        self.conn.commit()
        cur.close()

    def get_unbought_tokens(self):
        '''Retrieve tokens with buy_status UNBOUGHT'''
        cur = self.conn.cursor()
        cur.execute("""
            SELECT contract_address FROM token_records WHERE buy_status = 'UNBOUGHT';
        """)
        tokens = cur.fetchall()
        cur.close()
        return [token[0] for token in tokens]

    def close(self):
        '''Close the database connection'''
        self.conn.close()




try:
    # Initialize the database object
    db = TokenDatabase()
    # Create the token_records table if it doesn't exist
    # db.create_token_record_table()
    print("Table `token_records` checked/created successfully.")
    # Dummy contract address for testing
    dummy_contract_address = "9ZAwYLDrP2goDowrEzgM2RHtv9754N6aRUNzG4xda42C"
    # Register the dummy token
    db.register_token_record(dummy_contract_address)
    print(f"Dummy token with contract address {dummy_contract_address} has been registered.")
    # Fetch and display all unbought tokens
    unbought_tokens = db.get_unbought_tokens()
    print("Unbought tokens in the database:")
    print(unbought_tokens)
except Exception as e:
    print(f"Error occurred: {e}")
finally:
    # Close the database connection
    db.close()
    print("Database connection closed.")