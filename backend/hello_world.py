from sqlalchemy  import create_engine

engine = create_engine('mysql+pymysql://root:root@mysql:3307/db')
print("connected")