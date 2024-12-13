import psycopg2
conn = psycopg2.connect(dbname="postgres", host="localhost", user="postgres", password="postgres", port="5432")
cursor = conn.cursor()


class usersAndChannels():
    async def show_users_table(self):
            cursor.execute("SELECT * FROM users")
            lst = cursor.fetchall()
            return sorted(lst)
        
    async def add_users_table(self,uid):
        try:
            cursor.execute("INSERT INTO users (uid) VALUES (%s)", (uid,))
            conn.commit()
        except (psycopg2.errors.UniqueViolation):
            conn.commit()
            return "repeat"
        
    async def get_channels_by_uid(self,uid):
        cursor.execute("SELECT channel FROM channels WHERE uid = %s", (uid,))
        lst = cursor.fetchall()
        return sorted(lst)
    
    async def add_channels_by_uid(self, uid, channel):
        try:
         
            cursor.execute("INSERT INTO channels (uid, channel) VALUES (%s, %s)", (uid,channel))
            conn.commit()
        except:
       
            conn.commit()
            return "repeat"