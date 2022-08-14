from multiprocessing.connection import Client

conn = Client(("localhost", 6000), authkey=b"password")
conn.send("Updated")
conn.close()
