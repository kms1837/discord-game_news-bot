from discord.ext import commands
from bs4 import BeautifulSoup
import discord
import requests
import json

RULIWEB_NEWS_URL1 = "http://bbs.ruliweb.com/news/board/1003" # PC
RULIWEB_NEWS_URL2 = "http://bbs.ruliweb.com/news/board/1001" # 콘솔
INVEN_NEWS_URL1 = "http://feeds.feedburner.com/inven/sclass/24" #인벤 게임뉴스 - 칼럼
INVEN_NEWS_URL2 = "http://feeds.feedburner.com/inven/sclass/25" #인벤 게임뉴스 - 기획기사
THIS_NEWS_URL = "http://www.thisisgame.com/webzine/news/nboard/4/"
NAVER_NEWS_URL = "https://sports.news.naver.com/esports/news/index.nhn?isphoto=N&rc=N"
MAX_DISPLAY = 4

INVEN_TWITTER_URL = "https://twitter.com/inventeam"
THIS_TWITTER_URL = "https://twitter.com/thisisgamecom"
TWITTER_MAX_DISPLAY = 2

bot = commands.Bot(command_prefix='$', description='keyword')

@bot.command()
async def rank(ctx):
    print('asd')

@bot.command()
async def twitter(ctx):
    await invenTwitterScraping(ctx)
    await thisTwitterScraping(ctx)

@bot.command()
async def invenTwitter(ctx):
    await invenTwitterScraping(ctx)

@bot.command()
async def thisgmaeTwitter(ctx):
    await thisTwitterScraping(ctx)

@bot.command()
async def inven(ctx):
    await invenScraping(ctx)

@bot.command()
async def thisgame(ctx):
    await thisgameScraping(ctx)

@bot.command()
async def ruliweb(ctx):
    await ruliwebScraping(ctx)

@bot.command()
async def news(ctx):
    await invenScraping(ctx)
    await thisgameScraping(ctx)
    await ruliwebScraping(ctx)

async def thisgameScraping(ctx):
    print('thisgame')
    embed = discord.Embed(title="디스이즈 게임", description="디스이즈 게임의 최신 뉴스 {0}개를 보여줍니다.".format(MAX_DISPLAY), color=0x3c404c)
    newsBody = await newsTableBodyParsing(THIS_NEWS_URL, {"id" : "nboard"})
    newsRows = newsBody.select("li")
    fieldValue=""

    for index, row in enumerate(newsRows):
        if index >= MAX_DISPLAY:
            break
        
        rowContent = row.find("div", {"class": "subject"})
        rowTitle = rowContent.find("a")
        fieldValue += "[{0}](<{1}>)\n".format(rowTitle.text, "http://www.thisisgame.com" + rowTitle["href"])

    embed.add_field(name="전체 뉴스 게시판", value=fieldValue, inline=True)
    await ctx.send(embed=embed)

async def ruliwebScraping(ctx):
    print('ruliweb')
    embed = discord.Embed(title="루리웹 유저정보", description="루리웹의 최신 유저정보 {0}개를 보여줍니다.".format(MAX_DISPLAY), color=0x1A70DC)
    await ruliwebBoardParsing(RULIWEB_NEWS_URL1, embed, "PC")
    await ruliwebBoardParsing(RULIWEB_NEWS_URL2, embed, "콘솔")
    await ctx.send(embed=embed)

async def ruliwebBoardParsing(url, embed, title):
    fieldValue = ""

    newsBody = await newsTableBodyParsing(url, {"class" : "board_main"})
    newsRows = newsBody.select("tr")

    count = 0
    for row in newsRows:
        if count >= MAX_DISPLAY:
            break
        if len(row["class"]) > 1: #공지 걸러냄
            continue
        
        rowContent = row.find("td", {"class": "subject"})
        rowTitle = rowContent.find("a")
        fieldValue += "[{0}](<{1}>)\n".format(rowTitle.text, rowTitle["href"])
        count = count + 1
    
    embed.add_field(name=title, value=fieldValue, inline=True)

async def invenScraping(ctx):
    print('inven')
    embed = discord.Embed(title="인벤", description="인벤의 최신 뉴스 {0}개를 보여줍니다.".format(MAX_DISPLAY), color=0x7abe42)
    await invenFeedParsing(INVEN_NEWS_URL1, embed)
    await invenFeedParsing(INVEN_NEWS_URL2, embed)
    await ctx.send(embed=embed)

async def invenFeedParsing(url, embed):
    #xml feed
    result = ""
    request = requests.get(url)
    page = BeautifulSoup(request.text, "lxml-xml")
    title = page.find("title")
    items = page.findAll("item")
    for index, item in enumerate(items):
        if index >= MAX_DISPLAY:
            break
        result += "[{0}](<{1}>)\n".format(item.find("title").text, item.find("link").text)

    embed.add_field(name=title.text, value=result, inline=True)

async def naver():
    print("naver")
    #embed = discord.Embed(title="네이버", description="네이버의 최신 게임 포스트 {0}개를 보여줍니다.".format(MAX_DISPLAY), color=0x7abe42)
    fieldValue = ""

    # 네이버 뉴스는 ul li 방식으로 게시판이 구현됨 dom구조가 많이 꼬여있어서 코드도 좀 길어짐
    # 서버사이드에서 모두 렌더링하지 않고있어 다른 크롤링 방식이 필요함
    page = await getPage(NAVER_NEWS_URL)
    newsContent = page.find("div", {"id": "container"})
    newsCenter = newsContent.find("div", {"class": "newscenter"})
    newsList = newsCenter.find("div", {"class": "content"})
    print(newsList)

async def getPage(url):
    request = requests.get(url)
    page = BeautifulSoup(request.text, "html.parser")
    return page

async def newsTableBodyParsing(url, domInfo):
    page = await getPage(url)
    newsTable = page.find("div", domInfo)
    newsBody = newsTable.find("tbody")

    return newsBody

async def invenTwitterScraping(ctx):
    embed = discord.Embed(title="인벤", description="인벤의 최신 트위터 소식 {0}개를 보여줍니다.".format(TWITTER_MAX_DISPLAY), color=0x7abe42)
    await twitterScraping(THIS_TWITTER_URL, "인벤 트위터", embed)
    await ctx.send(embed=embed)

async def thisTwitterScraping(ctx):
    embed = discord.Embed(title="디스이즈 게임", description="디스이즈 게임의 최신 트위터 소식 {0}개를 보여줍니다.".format(TWITTER_MAX_DISPLAY), color=0x3c404c)
    await twitterScraping(INVEN_TWITTER_URL, "디스이즈 게임 트위터", embed)
    await ctx.send(embed=embed)

async def twitterScraping(url, title, embed):
    result = ""
    page = await getPage(url)
    timeLine = page.find("div", {"id": "timeline"})
    items = timeLine.findAll("li", {"class": "js-stream-item"})
    for index, item in enumerate(items):
        if index >= TWITTER_MAX_DISPLAY:
            break
        content = item.find("div", {"class": "content"})
        TextContainer = content.find("div", {"class": "js-tweet-text-container"})
        contentText = TextContainer.find("p")
        result += contentText.text + "\n\n"
    embed.add_field(name=title, value=result, inline=True)

@bot.event
async def on_ready():
    print('=====================')
    print('[게임뉴스 봇 가동]')
    print("이름:", bot.user.name)
    print("id:", bot.user.id)
    print('=====================')

try:
    jsonData = open("./manifest.json").read()
    setting = json.loads(jsonData)
    bot.run(setting["bot-token"])
except OSError:
    print("폴더에 manifest.json 파일이 없습니다.")
except KeyError as error:
    print("manifest에 bot-token항목이 있는지 확인해주세요")

# testing code
#import asyncio
#loop = asyncio.get_event_loop()
#loop.run_until_complete(invenTwitterScraping())
#loop.close()
