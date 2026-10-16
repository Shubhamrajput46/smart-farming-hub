try:
    import pymysql
    pymysql.install_as_MySQLdb()
except ImportError:  # sqlite par chalate waqt pymysql zaroori nahi
    pass
