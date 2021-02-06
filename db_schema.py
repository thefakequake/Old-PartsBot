import aiosqlite
import asyncio

async def createbotdb():

    conn = await aiosqlite.connect("bot.db")

    cursor = await conn.execute("""CREATE TABLE cases (
                    name text,
                    tier integer
                    )""")


    await conn.commit()
    await conn.close()


loop = asyncio.get_event_loop()
loop.run_until_complete(createbotdb())

print('bot.db database created.')


credentials = open("credentials.json", "x")
credentials.close()
credentials = open("credentials.json", "w")
credentials.write('''{
  "token": "discord bot token",
  "client_id": "reddit application client id",
  "client_secret": "reddit application client secret",
  "username": "reddit username",
  "password": "reddit password",
  "TRN-Api-Key": "apex tracker api key: https://apex.tracker.gg/site-api",
  "command_prefix": ","
}''')
credentials.close()

print('credentials.json created - you\'ll have to fill in these credentials yourself.')


print('all files formatted and ready - contact QuaKe#9535 on discord if you need extra help')