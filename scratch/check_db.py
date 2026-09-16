import psycopg2

conn = psycopg2.connect('postgresql://user:password@localhost:5432/majorcode')
cur = conn.cursor()
cur.execute('SELECT document_name, status, ingestion_timestamp FROM documents')
rows = cur.fetchall()
for r in rows:
    print(r)
