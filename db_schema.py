import aiosqlite
import asyncio

async def createbotdb():

    conn = await aiosqlite.connect("bot.db")

    cursor = await conn.execute("""CREATE TABLE cases (
                    name text,
                    tier integer
                    )""")

    cursor = await conn.execute("""CREATE TABLE subscriptions (
                    guildid text,
                    newsid text,
                    salesid integer
                    )""")

    cursor = await conn.execute("""CREATE TABLE builds (
                    userid integer,
                    buildcontent text,
                    pcpp text
                    )""")

    await conn.commit()
    await conn.close()


loop = asyncio.get_event_loop()
loop.run_until_complete(createbotdb())

print('bot.db database created.')



async def createbotdatadb():

    conn = await aiosqlite.connect("botdata.db")

    cursor = await conn.execute("""CREATE TABLE botstats (
                    membercount text,
                    servercount text
                    )""")

    await conn.commit()
    await conn.close()


loop = asyncio.get_event_loop()
loop.run_until_complete(createbotdatadb())

print('botstats.db database created.')


credentials = open("credentials.json", "x")
credentials.close()
credentials = open("credentials.json", "w")
credentials.write('''{
  "token": "discord bot token",
  "client_id": "reddit application client id",
  "client_secret": "reddit application client secret",
  "username": "reddit username",
  "password": "reddit password",
  "TRN-Api-Key": "apex tracker api key: https://apex.tracker.gg/site-api"
}''')
credentials.close()

print('credentials.json created - you\'ll have to fill in these credentials yourself.')



scrapedata = open("scrapedata.txt", "x")
scrapedata.close()
scrapedata = open("scrapedata.txt", "w")
scrapedata.write("1")

print('scrapedata.txt created')

print('all files formatted and ready - contact QuaKe#5943 on discord if you need extra help')