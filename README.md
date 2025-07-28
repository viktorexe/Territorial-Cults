# 🏰 Territorial Cults Discord Bot

hey! so i made this discord bot for territorial.io servers and it's pretty cool

basically you can make cults, start wars with other cults, and there's a whole point system that tracks your wins automatically. i built it because i was bored one summer and thought it would be fun to add some chaos to discord servers.

## what it does

- you can create/join cults with your friends
- declare wars on other cults (it's not that serious lol)
- automatic point tracking from your territorial.io games
- leaderboards and stats
- role rewards when you hit milestones

## setup

you'll need python, mongodb, and a discord bot token. pretty standard stuff.

```bash
git clone https://github.com/viktorexe/Territorial-Cults.git
cd Territorial-Cults
pip install -r requirements.txt
```

copy `.env.example` to `.env` and add your bot token + mongodb connection string

```bash
python main.py
```

## deployment

works on railway, docker, or just run it on any server. i included all the config files.

## help

if something breaks just open an issue or join the [discord](https://discord.gg/HvF5QnqtHN)

---

made this in july 2025 when i had too much free time. use it however you want, just don't claim you made it

*- viktorexe*