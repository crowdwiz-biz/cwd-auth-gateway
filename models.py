import peewee, datetime
from playhouse.migrate import *
import config

if config.GENERAL['use_local_db']:
	database = peewee.SqliteDatabase(config.GENERAL['localdb_filename'])
else:
	database = peewee.PostgresqlDatabase(
	    config.GENERAL['pgsql_db'],  # Required by Peewee.
	    user=config.GENERAL['pgsql_db_user'],  # Will be passed directly to psycopg2.
	    password=config.GENERAL['pgsql_db_password'],
	    host=config.GENERAL['pgsql_db_host'],
		port = config.GENERAL['pgsql_db_port']
	)
class BOT(peewee.Model):
	# 
	# в этой таблице хранятся данные об аккаунте шлюза авторизации, первоначальное заполнение происходит из конфигурационного файла
	# 
	bc_login = peewee.TextField(default='', null=False)
	bc_id = peewee.TextField(default='', null=False)
	most_recent_op = peewee.IntegerField(default=0, null=False)
	statistics_id = peewee.TextField(default='', null=False)
	automatic_mode = BooleanField(default=True)

	class Meta:
		database = database

class USERS(peewee.Model):
	# 
	# в этой таблице хранятся данные об аккаунтах пользователей 
	# 
	bc_login = peewee.TextField(default='', null=False)
	bc_id = peewee.TextField(default='', null=False)
	statistics_id = peewee.TextField(default='', null=False)
	chat_id = peewee.TextField(default='', null=False)
	otp = peewee.TextField(default='', null=False)
	last_command = peewee.TextField(default='', null=False)
	wrong_auth = peewee.IntegerField(default=0, null=False)
	internal_balance = peewee.IntegerField(default=0, null=False)
	status =  peewee.IntegerField(default=0, null=False)

	class Meta:
		database = database

class DEPOSITS(peewee.Model):
	from_account= peewee.TextField(default='', null = False)
	amount = peewee.IntegerField(default=0, null = True)
	asset = peewee.TextField(default='', null = False)
	op_id = peewee.IntegerField(default=0, null = True)
	ts = peewee.DateTimeField(default=datetime.datetime.now, null = True)
	blocktime = peewee.DateTimeField(default=datetime.datetime.now, null = True)
	deposit_status = peewee.IntegerField(default=0, null = True) 

	class Meta:
		database = database

if __name__ == "__main__":
	try:
		BOT.create_table()
	except peewee.OperationalError:
		print("BOT table already exists!")
	try:
		USERS.create_table()
	except peewee.OperationalError:
		print("USERS table already exists!")
	try:
		DEPOSITS.create_table()
	except peewee.OperationalError:
		print("DEPOSITS table already exists!")