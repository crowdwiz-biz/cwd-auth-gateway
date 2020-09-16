from websocket import create_connection
import datetime
import json, requests, random

from crowdwiz import CrowdWiz
from crowdwiz.account import Account
from crowdwizbase.memo import decode_memo
from crowdwizbase.account import PublicKey, PrivateKey

from models import BOT, USERS, DEPOSITS

import config

from telegram_common import *
from textwrap import dedent

def config_init():
	try:
		bot_acc = BOT.get(BOT.bc_login == config.GENERAL['bc_login'])
	except:
		ws = create_connection(config.GENERAL['ws'])
		cwd = CrowdWiz(node=config.GENERAL['ws'])
		bc_acc = Account(config.GENERAL['bc_login'], blockchain_instance = cwd)
		ws.send('{"jsonrpc": "2.0", "method": "get_objects" "params": [["%s"]], "id": 1}' % bc_acc['statistics'])
		result = ws.recv()
		ws.send('{"jsonrpc": "2.0", "method": "get_objects" "params": [["%s"]], "id": 1}' % json.loads(result).get('result')[0]['most_recent_op'])
		result = ws.recv()
		most_recent_op = int(json.loads(result).get('result')[0]['operation_id'].split('.')[2])
		bot_acc = BOT.create()
		bot_acc.bc_login = config.GENERAL['bc_login']
		bot_acc.bc_id = bc_acc['id']
		bot_acc.statistics_id = bc_acc['statistics']
		bot_acc.most_recent_op = most_recent_op
		bot_acc.save()

def get_block_date(block_num):
	ws = create_connection(config.GENERAL['ws'])
	ws.send('{"jsonrpc": "2.0", "method": "get_block_header" "params": ["%s"], "id": 1}' % str(block_num))
	result = ws.recv()
	block =json.loads(result)
	return datetime.datetime.strptime(block['result']['timestamp'], '%Y-%m-%dT%H:%M:%S')

def handle_updates(updates):
	for update in updates["result"]:
		text = update["message"]["text"]
		chat_id = update["message"]["chat"]["id"]
		keyboard=[]
		textmessage = ""

		try:
			internal_account = USERS.get(USERS.chat_id == chat_id)
		except:
			internal_account = USERS.create()
			internal_account.bc_login=''
			internal_account.bc_id=''
			internal_account.statistics_id=''
			internal_account.chat_id=chat_id
			internal_account.otp=str(random.randint(10000, 99999))
			internal_account.last_command=''
			internal_account.wrong_auth=0
			internal_account.internal_balance=0
			internal_account.save()

		if internal_account.last_command=='withdraw' and text !='withdraw':
			try:
				if internal_account.status == 1 and int(text)<=internal_account.internal_balance:
					withdraw_cwd=float(int(int(text)/float(config.GENERAL['withdraw_rate'])*100000)/100000)
					print(withdraw_cwd)
					cwd = CrowdWiz(node=config.GENERAL['ws'], keys=[config.GENERAL['wif'], config.GENERAL['memo_wif'] ])
					cwd.transfer(internal_account.bc_login, withdraw_cwd,"CWD","Вывод %s DEMO по крусу %s за 1 CWD" % (str(text), str(config.GENERAL['withdraw_rate'])),account=config.GENERAL['bc_login'])
					textmessage = "Осуществлён вывод %s DEMO по крусу %s за 1 CWD. На аккаунт %s отправлено %s CWD." % (str(text), str(config.GENERAL['withdraw_rate']),internal_account.bc_login, str(withdraw_cwd) )
					internal_account.last_command=''
					internal_account.internal_balance=internal_account.internal_balance-int(text)
					internal_account.save()
				else:
					internal_account.last_command=''
					internal_account.save()
					textmessage ="Недостаточный баланс!"
			except:
				internal_account.last_command=''
				internal_account.save()
				textmessage ="Недостаточный баланс!"

		if internal_account.last_command=='Ввести код' and text !='Ввести код':
			if internal_account.otp == text:
				internal_account.status = 1
				internal_account.last_command=''
				internal_account.save()
				text = "Информация"
			else:
				textmessage = "Введён неверный код, повторите попытку"
				internal_account.wrong_auth=internal_account.wrong_auth+1
				internal_account.save()

		if internal_account.last_command=='Привязать аккаунт' and text !='Привязать аккаунт':
			try:
				cwd = CrowdWiz(node=config.GENERAL['ws'], keys=[config.GENERAL['wif'],config.GENERAL['memo_wif'] ])
				bc_acc = Account(text, blockchain_instance = cwd)
				internal_account.bc_id=bc_acc['id']
				internal_account.bc_login=bc_acc['name']
				internal_account.statistics_id=bc_acc['statistics']
				internal_account.save()
				cwd.send_message(bc_acc['name'],"Код для привязки вашего аккаунта к демо-боту %s" % str(internal_account.otp),account=config.GENERAL['bc_login'])
				textmessage = "На ваш аккаунт в Crowdwiz отправлен код подтверждения для привязки, введите полученный код"
				internal_account.last_command='Ввести код'
				internal_account.save()
			except:
				textmessage = "Такой аккунт не зарегистрирован! Повторите попытку."


		if text == "/start":
			textmessage = "/start pressed"
		if text == "Информация":
			textmessage=dedent("""\
								======================
								Информация о вашем Аккаунте
								Ваш баланс: %s DEMO
								Ваш логин в Crowdwiz: %s
								Ваш статус: %s
								""" % ( str(internal_account.internal_balance), 
										internal_account.bc_login if internal_account.bc_login != "" else "Не привязан",
										"Аккаунт подтверждён и активен" if internal_account.status == 1 else "Аккаунт неактивен",
									) 
								)
		if text == 'Привязать аккаунт':
			internal_account.last_command='Привязать аккаунт'
			internal_account.save()
			textmessage = "Введите свой аккаунт в Crowdwiz"

		if text == 'Пополнить счёт':
			if internal_account.status == 1:
				textmessage = "Сделайте перевод с аккаунта %s на аккаунт %s. Курс поплнения %s DEMO за 1 CWD" % (internal_account.bc_login, config.GENERAL['bc_login'], str(config.GENERAL['deposit_rate']))
			else:
				textmessage = "Аккаунт не привязан"

		if text == 'Вывести в CWD':
			if internal_account.status == 1:
				textmessage = "Ваш баланс составлет %s DEMO. Курс на вывод составляет %s DEMO за 1 CWD. Введите количество DEMO которое хотите вывести:" % (str(internal_account.internal_balance), str(config.GENERAL['withdraw_rate']))
				internal_account.last_command='withdraw'
				internal_account.save()
		if keyboard == []:
			if internal_account.bc_id !='' and internal_account.status ==0:
				keyboard = build_keyboard(['Информация','Ввести код'])
			elif internal_account.bc_id !='' and internal_account.status ==1:
				keyboard = build_keyboard(['Информация', 'Пополнить счёт', 'Вывести в CWD'])
			else:
				keyboard = build_keyboard(['Информация','Привязать аккаунт'])
		send_message(textmessage, chat_id, keyboard)

def handle_deposits(bot):
	print("handle_deposits called")
	cwd = CrowdWiz(node=config.GENERAL['ws'], keys=[config.GENERAL['wif'],config.GENERAL['memo_wif'] ])
	account=Account(bot.bc_login, blockchain_instance = cwd)
	max_op_id = bot.most_recent_op
	for h in account.history():
		op_id=h['id']
		int_op_id = int(op_id.split('.')[2])
		if int_op_id > max_op_id:
			max_op_id = int_op_id
		if int_op_id<=bot.most_recent_op:
			bot.most_recent_op = max_op_id
			bot.save()
			break

		if h['op'][0] == 0 and h['op'][1]['to'] == bot.bc_id and int_op_id > bot.most_recent_op:
			try:
				op_in_base=DEPOSITS.get(DEPOSITS.op_id == int_op_id)
			except:
				if (h['op'][1]['amount']['asset_id'] == "1.3.0"):
					blocktime = get_block_date(h['block_num'])
					acc = Account(h['op'][1]['from'], blockchain_instance = cwd)
					try:
						internal_account = USERS.get(USERS.bc_login == acc.name)
						internal_account.internal_balance=internal_account.internal_balance+int(h['op'][1]['amount']['amount'])/100000*config.GENERAL['deposit_rate']
						internal_account.save()
						new_deposit = DEPOSITS.create(
							from_account = acc.name,
							amount = int(h['op'][1]['amount']['amount'])/100000,
							asset = "CWD",
							op_id = int_op_id,
							deposit_status = 1,
							blocktime = blocktime
						)
						new_deposit.save()
						chat_id=internal_account.chat_id
						textmessage = "Вы пополнили баланс на сумму %s DEMO по курсу %s DEMO за 1 CWD" % (str(int(h['op'][1]['amount']['amount'])/100000*config.GENERAL['deposit_rate']),str(config.GENERAL['deposit_rate']))
						keyboard = build_keyboard(['Информация', 'Пополнить счёт', 'Вывести в CWD'])
						send_message(textmessage, chat_id, keyboard)
					except:
						print("Account not linked")



def main():
	config_init()
	last_update_id = None
	while True:
		try:
			for bot in BOT.select():
				handle_deposits(bot)
			updates = get_updates(last_update_id)
			if len(updates["result"]) > 0:
				last_update_id = get_last_update_id(updates) + 1
				handle_updates(updates)

		except Exception as e:
			print("Error", str(e))
			break
		time.sleep(60)

if __name__ == '__main__':
	main()