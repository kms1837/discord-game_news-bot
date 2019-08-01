from discord.ext import commands
from bs4 import BeautifulSoup
from selenium import webdriver
import discord
import requests
import json

RULIWEB_NEWS_URL1 = "http://bbs.ruliweb.com/news/board/1003" # PC
RULIWEB_NEWS_URL2 = "http://bbs.ruliweb.com/news/board/1001" # 콘솔
INVEN_NEWS_URL1 = "http://feeds.feedburner.com/inven/sclass/24" #인벤 게임뉴스 - 칼럼
INVEN_NEWS_URL2 = "http://feeds.feedburner.com/inven/sclass/25" #인벤 게임뉴스 - 기획기사
THIS_NEWS_URL = "http://www.thisisgame.com/webzine/news/nboard/4/"
NAVER_NEWS_URL = "https://sports.news.naver.com/esports/news/index.nhn?isphoto=N&rc=N"

INVEN_TWITTER_URL = "https://twitter.com/inventeam"
THIS_TWITTER_URL = "https://twitter.com/thisisgamecom"

STEAM_RANK_URL = "https://store.steampowered.com/stats/"
GANETRICS_RANK_URL = "http://www.gametrics.com/Rank/Rank02.aspx"

bot = commands.Bot(command_prefix='$', description="")

@bot.command()
async def steamRank(ctx):
    """스팀 현재 접속자 순위"""
    await steamRankScraping(ctx)

@bot.command()
async def gametricsRank(ctx):
    """게임트릭스 PC방 게임사용량 순위"""
    await gametricsRankScraping(ctx)

@bot.command()
async def twitter(ctx):
    """모든 트위터 정보조회"""
    await invenTwitterScraping(ctx)
    await thisTwitterScraping(ctx)

@bot.command()
async def invenTwitter(ctx):
    """인벤 트위터 정보조회"""
    await invenTwitterScraping(ctx)

@bot.command()
async def thisgmaeTwitter(ctx):
    """디스이즈게임 트위터 정보조회"""
    await thisTwitterScraping(ctx)

@bot.command()
async def inven(ctx):
    """인벤 게임뉴스"""
    await invenScraping(ctx)

@bot.command()
async def thisgame(ctx):
    """디스이즈 게임뉴스"""
    await thisgameScraping(ctx)

@bot.command()
async def ruliweb(ctx):
    """루리웹 유저정보"""
    await ruliwebScraping(ctx)

@bot.command()
async def news(ctx):
    """모든 뉴스 정보조회(네이버는 속도가 느려 제외됨)"""
    await invenScraping(ctx)
    await thisgameScraping(ctx)
    await ruliwebScraping(ctx)

@bot.command()
async def naver(ctx):
    """네이버 게임뉴스"""
    await naverScraping(ctx)

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

async def naverScraping(ctx):
    print("naver")
    embed = discord.Embed(title="네이버", description="네이버의 최신 뉴스 {0}개를 보여줍니다.".format(MAX_DISPLAY), color=0x03cf5d)
    result = ""

    # 네이버 뉴스는 ul li 방식으로 게시판이 구현됨 dom구조가 많이 꼬여있어서 코드도 좀 길어짐
    # 서버사이드에서 모두 렌더링하지 않고있어 다른 크롤링 방식이 사용됨
    page = await getPhantomPage(NAVER_NEWS_URL)
    newsContent = page.find("div", {"id": "container"})
    newsCenter = newsContent.find("div", {"class": "newscenter"})
    newsList = newsCenter.find("div", {"class": "news_list"})
    items = newsList.select("li")
    for index, item in enumerate(items):
        if index >= MAX_DISPLAY:
            break
        title = item.select(".text a")[0]
        result += "[{0}](<{1}>)\n".format(title.text, "https://sports.news.naver.com" + title["href"])
    
    embed.add_field(name=title.text, value=result, inline=True)
    await ctx.send(embed=embed)

async def getPage(url):
    request = requests.get(url)
    page = BeautifulSoup(request.text, "html.parser")
    return page

async def getPhantomPage(url):
    driver = webdriver.PhantomJS('./phantomjs-2.1.1-windows/bin/phantomjs.exe')
    driver.get(url)
    page = BeautifulSoup(driver.page_source, "html.parser")
    driver.close()
    return page

async def newsTableBodyParsing(url, domInfo):
    page = await getPage(url)
    newsTable = page.find("div", domInfo)
    newsBody = newsTable.find("tbody")

    return newsBody

async def invenTwitterScraping(ctx):
    print('invenTwitter')
    embed = discord.Embed(title="인벤", description="인벤의 최신 트위터 소식 {0}개를 보여줍니다.".format(TWITTER_MAX_DISPLAY), color=0x7abe42)
    await twitterScraping(THIS_TWITTER_URL, "인벤 트위터", embed)
    await ctx.send(embed=embed)

async def thisTwitterScraping(ctx):
    print('thisTwitter')
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

async def steamRankScraping(ctx):
    embed = discord.Embed(title="스팀 접속자 랭크", description="현재 접속자 순위를 {0}위까지 보여줍니다.".format(RANK_LIMIT), color=0x3c404c)
    page = await getPage(STEAM_RANK_URL)
    detailStats = page.find("div", {"id": "detailStats"})
    items = detailStats.findAll("tr", {"class": "player_count_row"})

    for index, item in enumerate(items):
        if index >= RANK_LIMIT:
            break
        tds = item.findAll("td")
        gameName = item.find("a", {"class": "gameLink"})
        title = "{0}등 {1}".format(index+1, gameName.text)
        info = "현재 플레이어: {0} 오늘 최고기록: {1}".format(tds[0].find("span").text, tds[1].find("span").text)
        embed.add_field(name=title, value=info, inline=True)
    await ctx.send(embed=embed)

async def gametricsRankScraping(ctx):
    #사이트가 오래되서 div에 class나 id가 거의 안되있다.
    embed = discord.Embed(title="게임트릭스 PC방 게임사용량 순위", description="게임사용량 순위를 {0}위까지 보여줍니다.".format(RANK_LIMIT), color=0x3c404c)
    page = await getPhantomPage(GANETRICS_RANK_URL)
    panel = page.find("div", {"id": "UpdatePanel"})
    rankContainer = panel.select("tbody > tr > td")[2]
    rankTable = rankContainer.select("tbody > tr")[8]
    rankContent = rankTable.select("tbody > tr")[1]
    items = rankContent.select("table")

    for index, item in enumerate(items):
        if index >= RANK_LIMIT:
            break
        row = item.select("tbody > tr")[0]
        infoItems = row.select("td")
        title = "{0}등 {1}".format(index+1, infoItems[3].find("a").text)
        percent = infoItems[5].text.replace(" ", "").replace("\t", "").replace("\n", "")
        info = "사용시간 점유율: {0}".format(percent)
        embed.add_field(name=title, value=info, inline=True)

    await ctx.send(embed=embed)

@bot.event
async def on_ready():
    print('=====================')
    print('[게임뉴스 봇 가동]')
    print("이름:", bot.user.name)
    print("id:", bot.user.id)
    print('=====================')


def runApp():
    try:
        jsonData = open("./manifest.json", 'r', encoding='UTF-8').read()
        setting = json.loads(jsonData)

        global MAX_DISPLAY
        MAX_DISPLAY = setting["news-display"]
        global TWITTER_MAX_DISPLAY
        TWITTER_MAX_DISPLAY = setting["twitter-display"]
        global RANK_LIMIT
        RANK_LIMIT = setting["rank-display"]

        bot.description = setting["description"]
        bot.run(setting["bot-token"])
    except OSError:
        print("폴더에 manifest.json 파일이 없습니다.")
    except KeyError as error:
        print("manifest오류! 다시 설정해주세요")

if __name__ == "__main__":
    runApp()



# testing code

#import asyncio
#loop = asyncio.get_event_loop()
#loop.run_until_complete(naver())
#loop.close()
