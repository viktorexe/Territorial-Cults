# 🏰 Territorial Cults Discord Bot

Yooo what's good my fellow gamers!! 👋 Welcome to **Territorial Cults** - literally the most INSANE Discord bot for Territorial.io that I've ever built! Like seriously, this isn't just some random bot you add and forget about... nah fam, this is about to turn your server into the most chaotic, fun, and addictive place on Discord! 🎮⚔️

*Built by me (viktorexe) during those crazy summer nights in July 2025 when I had way too much caffeine and not enough sleep* ☕😴

## 🌟 Okay But Like... What Actually IS This Thing??

So picture this right... You're just vibing in your Discord server, maybe playing some Territorial.io with the homies, and you're like "bruh wouldn't it be absolutely MENTAL if we could actually have real cults and start actual wars and stuff??" 

Well my friend... *dramatic pause* ...your wildest dreams just became reality! 🤯

I basically took your boring Discord server and said "nah we're not doing boring today" and turned it into this absolutely UNHINGED world where you can:
- Start your own cult (yes really)
- Declare war on your friends (sorry not sorry)
- Form alliances and then betray them (it's giving Survivor vibes)
- And just generally cause the most beautiful chaos you've ever seen

It's like if Game of Thrones had a baby with your favorite video game and that baby grew up to be a Discord bot. Wild, right? 🎭

## ✨ The Features That Made Me Stay Up Until 4AM Coding

### 🏛️ **Cult Life But Make It Digital**
Okay so like... you can literally start your own cult. I'm not even joking. Pick a name that goes hard, choose an emoji that represents your vibe, write a description that makes people go "damn I NEED to join this" - and boom, you're officially a cult leader! 

You can recruit your friends, be that mysterious loner who runs everything from the shadows, or just collect members like Pokemon cards. Whatever floats your boat! And the best part? You actually get REAL powers over your cult members. Finally, the respect you've always deserved! 😎

### ⚔️ **Starting Beef Has Never Been This Fun**
Remember when you were a kid and you'd have those epic playground wars? Yeah, this is that but for adults and way more sophisticated (kinda). 

You can literally declare war on other cults and I'll sit back with my popcorn watching the chaos unfold. The bot handles all the boring technical stuff while you focus on the important things - like talking trash and planning your victory speech. 

And don't worry, I made sure you get notifications for EVERYTHING because missing drama is basically a crime. 📱

### 🏆 **Rewards That Actually Matter**
You know how most bots give you rewards that are basically useless? Yeah, I hate that too. So I made a system where when you hit milestones, you get roles that people actually want and that look cool in the member list.

No more sliding into admin DMs like "hey I got 1000 points can I get that role please 🥺" - nah fam, the bot's got you covered automatically. It even removes your old roles so you don't look like a walking participation trophy. Growth mindset only! 📈

### 📊 **Stats That Feed Your Main Character Energy**
I built these leaderboards that are honestly more addictive than the actual game sometimes. You can see who's actually carrying their weight and who's just... there. 

Your profile page is basically your flex zone - it's got graphs, stats, achievements, the whole nine yards. It's like LinkedIn but for gamers and actually fun to look at. You can literally watch your glow-up happen in real time! ✨

## 🚀 Alright Let's Get This Thing Running!

### What You're Gonna Need (Don't Panic)
- A Discord server (obviously lol)
- MongoDB database (I know it sounds scary but trust me, it's just where I store all the cool data)
- Maybe like 10 minutes and definitely some snacks because setup makes me hungry

### The Setup Process (I Promise It's Not That Bad)

Okay so first things first, you gotta grab my code:

```bash
git clone https://github.com/viktorexe/Territorial-Cults.git
cd Territorial-Cults
```

Then you need to download all the Python stuff I used (don't worry, it's all the good stuff):

```bash
pip install -r requirements.txt
```

Now here's where you gotta do a tiny bit of work (I know, I know, but it's worth it):
- Find that `.env.example` file and copy it to `.env`
- Get your Discord bot token and paste it in there (it's like the VIP pass for your bot)
- Add your MongoDB connection string (this is where all the magic happens)

And finally, the moment of truth:

```bash
python main.py
```

If everything worked, you should see some messages pop up and then... congratulations! You just deployed something I spent way too many late nights building! 🎉

### Environment Variables
```env
DISCORD_TOKEN=your_super_secret_bot_token_here
MONGODB_URI=your_mongodb_connection_string_here
PORT=8000
```

## 🎯 The Commands That Took Forever to Perfect

Okay so I spent WEEKS making sure these commands were actually fun to use (not like those boring bots where everything feels like homework):

- `/cult_create` - This is where you become the leader you were born to be. Choose your cult name wisely because everyone's gonna see it!
- `/cult_list` - It's like Tinder but for cults. Swipe through and find your perfect match!
- `/cult_war` - The nuclear option. Use this when words just aren't enough anymore 🔥
- `/leaderboard` - Find out who's actually good at this game and who just talks a big game
- `/profile` - Your personal bragging rights page. I made the graphs extra pretty just for you
- `/set_multiplier` - Want to make an event extra spicy? This is your button
- `/rewardrole` - Set up rewards that people will actually fight for

And honestly there's like 20+ more commands but these are the ones that'll probably become your favorites!

## 🛠️ The Nerdy Stuff (For My Code Homies)

So if you're curious about what I used to build this masterpiece:

- **Python 3.9+** - Because Python is just *chef's kiss* perfect for this kind of stuff
- **discord.py** - The library that makes Discord bots not suck
- **MongoDB** - Where I store all your cult drama and war stories
- **matplotlib** - For making those graphs that make you feel like a data scientist
- **aiohttp** - Keeps everything running smooth and fast (no lag allowed!)
- **Docker** - Because I like my deployments clean and portable

Basically I picked all the tools that wouldn't make me want to throw my laptop out the window at 3AM 😅

## 🚢 Getting This Thing Online

### Railway (Seriously, It's So Easy)
I already set up all the Railway config files because I'm not about that complicated deployment life. Just connect your GitHub repo, hit deploy, and grab some coffee while it does its thing.

### Docker (If You're Into That)
For my container friends:
```bash
docker build -t territorial-cults .
docker run -d --env-file .env territorial-cults
```

### The Classic Way
Sometimes the old ways are the best ways:
```bash
python main.py
```
And you're done! See? I told you I'd keep it simple.

## 🙏 Big Love to Everyone Who Made This Possible

- The Territorial.io community - y'all are genuinely the coolest gamers I've ever met
- The discord.py developers who built the tools that let me turn my crazy ideas into reality
- Everyone who's gonna use this bot and create absolute chaos in their servers (you're the real MVPs)
- My coffee machine, my energy drinks, and that one playlist that got me through all those late night coding sessions
- My friends who had to listen to me ramble about cult systems and war mechanics for months

## 📞 Need Help? I Got You!

- Hit me up with a GitHub issue and I'll help you figure it out (I actually read these, promise!)
- Join our [Discord server](https://discord.gg/HvF5QnqtHN) where you can ask questions and see the bot in action
- Check out the [documentation](https://territorialcults.vercel.app) - I actually tried to make it not boring to read

Seriously though, don't be shy about asking for help. I'd rather spend time helping you get this working than have you give up because something was confusing!

---

**Okay real talk for a second:** I built this because I was tired of Discord servers that felt dead and boring. Like, we're gamers! We should be having FUN! So I spent my entire summer building something that would actually make people excited to open Discord again.

This isn't just about the code or the features - it's about creating those moments where you and your friends are laughing so hard you can't breathe, where you're planning strategies at 2AM, where you're making memories that you'll still be talking about years from now.

So yeah, use this bot, break it, fix it, make it yours. Start some wars, build some cults, cause some chaos. Just... have fun with it, you know? That's literally the whole point.

*Built with way too much caffeine, not enough sleep, and an unhealthy obsession with making Discord servers fun again*

*- viktorexe, somewhere in July 2025 at like 4AM probably* 🌙☕