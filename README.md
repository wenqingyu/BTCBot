BTC China Bot
===========

This bot runs on [BTC China](https://vip.btcchina.com), aka the heaven of trading bots, where transaction fee is 0%.
Currently it only follows simple heuristics (buy low and sell high), and acts as a scalper. Indicators will be added.

Usage
---

``` bash
git clone https://github.com/zfei/BtcChinaBot
```
after it's downloaded, cd into BtcChinaBot:
``` bash
cd ./BtcChinaBot
```
rename sample_settings.py to settings.py:
``` bash
mv sample_settings.py settings.py
```
and make changes to it (set API access & secret and parameters).

Finally, run the bot:
``` bash
python bot.py
```
This program is provided AS IS. Do not enter API information if you do not know what you are doing. Use it at your own risk.

License
---

The use of this program is subject to MIT LICENSE, please refer to LICENSE for additional information.
Donation
---

The official API methods provided by BTC China is inconsistent with their documentation and actual scenarios. I've made more than 5 changes to it to actually make it work, plus numerous wrappers in bot.py to make sure the ridiculous API doesn't mess things up.

If this project helps you in anyway, please kindly consider a donation to the following bitcoin address:

``` bash
1BjEJBytssDg6WpCnYDc9ini5ecZevJ3Q
```

It's much appreciated.
