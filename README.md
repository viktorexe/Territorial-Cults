# 🏰 Territorial Cults Discord Bot

Hey there! Welcome to the **Territorial Cults** Discord bot - your ultimate companion for managing Territorial.io gaming communities! 🎮

*Made with ❤️ by [viktorexe](https://github.com/viktorexe)*

## 🌟 What's This All About?

Ever wanted to turn your Discord server into an epic Territorial.io battleground? This bot transforms your community into a thriving ecosystem of cults, wars, alliances, and friendly competition! Think of it as your server's personal game master that never sleeps.

## ✨ Cool Features That'll Blow Your Mind

### 🏛️ **Cult System**
- Create your own cults with custom names, icons, and descriptions
- Join forces with friends or go solo - your choice!
- Leaders and officers get special powers (because hierarchy matters!)
- Watch your cult grow and dominate the leaderboards

### ⚔️ **Epic Wars & Alliances**
- Declare war on rival cults and settle scores once and for all
- Form strategic alliances (or betray them later - we don't judge!)
- Automatic war resolution when time runs out
- Real-time battle tracking and notifications

### 💰 **Smart Economy System**
- Earn points from your Territorial.io victories
- Automatic win log processing (no more manual tracking!)
- Server-wide multipliers for special events
- Beautiful profile graphs to show off your progress

### 🏆 **Reward System That Actually Works**
- Set up milestone rewards that give roles automatically
- No more "hey admin, I reached 1000 points" messages
- Smart role management that removes lower tiers
- Real-time monitoring every 3 seconds (yeah, we're that fast!)

### 📊 **Leaderboards & Stats**
- Interactive leaderboards with time filters
- Cult rankings and war histories
- Personal profiles with achievement tracking
- Monthly and weekly breakdowns

## 🚀 Getting Started

### What You'll Need
- A Discord server (obviously!)
- MongoDB database (for storing all the cool data)
- A bit of patience while setting things up

### Quick Setup
1. **Clone this bad boy:**
   ```bash
   git clone https://github.com/viktorexe/Territorial-Cults.git
   cd Territorial-Cults
   ```

2. **Install the magic:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up your secrets:**
   - Copy `.env.example` to `.env`
   - Add your Discord bot token
   - Add your MongoDB connection string

4. **Launch it:**
   ```bash
   python main.py
   ```

### Environment Variables
```env
DISCORD_TOKEN=your_super_secret_bot_token_here
MONGODB_URI=your_mongodb_connection_string_here
PORT=8000
```

## 🎯 Key Commands You'll Love

- `/cult_create` - Birth a new cult into existence
- `/cult_list` - See all the cults and join one with a click
- `/cult_war` - Time to settle some scores!
- `/leaderboard` - Who's dominating right now?
- `/profile` - Check out your epic stats
- `/set_multiplier` - Boost those points for events
- `/rewardrole` - Set up those sweet milestone rewards

## 🛠️ Tech Stack (For the Nerds)

- **Python 3.9+** - Because it's awesome
- **discord.py** - The Discord magic happens here
- **MongoDB** - Where all your data lives happily
- **matplotlib** - For those beautiful graphs
- **aiohttp** - Keeping things async and fast
- **Docker** - Deploy anywhere, anytime

## 🚢 Deployment Options

### Railway (Recommended)
This bot is Railway-ready! Just connect your repo and deploy. The `railway.json` and health check endpoints are already configured.

### Docker
```bash
docker build -t territorial-cults .
docker run -d --env-file .env territorial-cults
```

### Traditional Hosting
Just run `python main.py` on any server with Python 3.9+

## 🤝 Contributing

Found a bug? Have a cool idea? Want to make this bot even more awesome? 

1. Fork it
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is open source and available under the [MIT License](LICENSE).

## 🙏 Special Thanks

- The Territorial.io community for being awesome
- Discord.py developers for the amazing library
- Everyone who uses this bot and makes their servers more fun!

## 📞 Need Help?

- Open an issue on GitHub
- Check out the [documentation](https://territorialcults.vercel.app)
- Join our support community (coming soon!)

---

**Remember:** This bot is made by gamers, for gamers. It's designed to bring communities together through friendly competition and epic battles. Use it responsibly and have fun! 🎉

*Made with passion and way too much coffee by [viktorexe](https://github.com/viktorexe)* ☕