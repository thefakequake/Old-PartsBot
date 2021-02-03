![PartsBot Logo](https://images-ext-2.discordapp.net/external/6UmCMcasGIE3Re778AWhhiu9-bBYH9oJk6Css0sRb0g/%3Ftoken-time%3D1612396800%26token-hash%3D9oUuzM-M5AMRgqCPjngzkuMQSHvY9p6kcmIzh-XHcAg%253D/https/c10.patreonusercontent.com/3/eyJ3Ijo5NjB9/patreon-media/p/campaign/4864117/1cca5404da9a41a4af5bc81fda411782/4.png)

### PartsBot is a Discord bot that can automatically format PCPartPicker links, check pricing and specs for parts, save your build and allow you to update it on the fly, and much, much more.
#### You can invite the bot [here](https://discord.com/api/oauth2/authorize?client_id=769886576321888256&permissions=0&scope=bot). Consider supporting this project on the [PartsBot Patreon](https://www.patreon.com/partsbot). Join the [Discord Server](https://discord.gg/WM9pHp8) if you need to get any help regarding this bot.

![A demonstration](https://media.discordapp.net/attachments/525286309376426014/805931963734032394/ezgif.com-gif-maker.gif)

## Reporting bugs
Please report bugs in the [PartsBot Discord](https://discord.gg/WM9pHp8). The bot automatically reports errors if it encounters them, but please do report them if you see them often.

## Bot information
PartsBot is written in Python using the Discord.py library. The prefix is `,` and it cannot be unfortunately cannot be changed unless you run your own instance (see below).

## Contributing
Contributions to PartsBot are welcome. Send a pull request and I (QuaKe) will review it.

## Running your own instance
Make sure you have at least Python 3.7 installed (that's the most recent version it has been tested on).
```
>>> git clone https://github.com/QuaKe8782/PartsBot.git
>>> pip install -r requirements.txt
>>> python db_schema.py
```
Now fill in `credentials.json`. You will need to provide a discord bot token, an apex tracker API key (https://apex.tracker.gg/site-api), a reddit account username and password, a reddit application client ID, a reddit application client secret and a bot command prefix unless you wish to keep it as `,`.
```
>>> python3 main.py
```
Then, invite your bot to your server and you should be good to go!

## Credits
Bogdan for his member converter

CorpNewt for his [URL regex](https://github.com/corpnewt/CorpBot.py/blob/rewrite/Cogs/Server.py#L20).