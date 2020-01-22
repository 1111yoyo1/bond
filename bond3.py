# -*- coding: utf-8 -*-
import urllib2
import httplib
#import numpy as np
import traceback
import re
import sys
import json
import time
import socket
#import pprint
import logging
import datetime
import collections
import os

standard = -0.015
bondToStockUrl = "https://www.jisilu.cn/data/cbnew/cb_list/"


def ReadUrl(url):
    try:
        content = urllib2.urlopen(url).readline()
    except httplib.IncompleteRead as e:
        content = e.partial
        print content
    except socket.error, ex:
        print "Connection error"
        content = None
    except httplib.BadStatusLine as err:
        print "Bad Status Line"
        content = None
    except Exception, e:
        print "Common error, fail to access to %s" % url
        content = None
    return content


def Mail(subject, content):
    import base64
    import smtplib
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText
    mail_server = "smtp.partner.outlook.cn"
    mail_port = 587
    mail_user = "youyou.xu@memblaze.com"
    mail_pass = r'TWVtMjAxODAx'
    to_list = ['<youyou.xu@memblaze.com>']
    s = smtplib.SMTP(mail_server, mail_port)
    s.starttls()
    s.login(mail_user, base64.b64decode(mail_pass))
    msgRoot = MIMEMultipart('related')
    msgRoot['Subject'] = subject
    msg_alternative = MIMEMultipart('alternative')
    msg_alternative.attach(MIMEText(content, 'plain', 'utf-8'))
    msgRoot.attach(msg_alternative)
    s.sendmail(mail_user, to_list, msgRoot.as_string())
    s.close()


class LogBuilder(object):
    """ build  a logger"""

    _singleton = None

    def __new__(cls, *args,**kwargs):
        if not cls._singleton:
            cls._singleton = super(LogBuilder, cls).__new__(cls, *args, **kwargs)
        else:
            def initPass(self,*args,**kwargs):
                pass
            cls.__init__ = initPass
        return cls._singleton

    def __init__(self, filename):
        self.fileName = filename
        self.logLevel = logging.INFO
        self.logFormatter = '%(asctime)s %(levelname)s %(message)s'
        self.setup()

    def setup(self):
        logger = logging.getLogger(__name__)
        logger.setLevel(self.logLevel)
        formatter = logging.Formatter(self.logFormatter)
        hdlr = logging.FileHandler(self.fileName)
        hdlr.setFormatter(formatter)
        logger.addHandler(hdlr)

        hdlr2 = logging.StreamHandler(sys.stdout)
        hdlr2.setFormatter(formatter)
        logger.addHandler(hdlr2)
        self.mapLogger(logger)
        self.logger = logger
        return logger

    def mapLogger(self, logger):
        """map the logger to support legacy code"""
        logger.Debug = logger.debug
        logger.Info = logger.info
        logger.Warning = logger.warning
        logger.Error = logger.error
        logger.Critical = logger.critical


class BondObj(object):
    def __init__(self, bondId, market=None, stockId=None, conStockRate=None):
        self.bondId = bondId
        self.market = market
        self.stockId = stockId
        self.conStockRate = conStockRate
        self.bondFivePriceUrl = "http://sqt.gtimg.cn/utf8/q=%s%s" % (self.market, self.bondId)
        self.bondJsonWebContent = urllib2.urlopen(self.bondFivePriceUrl).readline()

        self.stockFivePriceUrl = "http://sqt.gtimg.cn/utf8/q=%s" % (self.stockId)
        self.stockJsonWebContent = urllib2.urlopen(self.stockFivePriceUrl).readline()

    def ToString(self):
        self.output = "Bond Id: %s\n" % self.bondId
        self.output += "Market: %s\n" % self.market
        self.output += "Stock Id: %s\n" % self.stockId
        self.output += "stock Converting Rate: %s\n" % self.conStockRate
        self.output += "Bond Sell Prices: "
        self.output += " ".join(self.bondPricesSell)
        self.output += "\n"
        self.output += "Bond Buy Prices: "
        self.output += " ".join(self.bondPricesBuy)
        self.output += "\n"
        self.output += "Stock Sell prices: "
        self.output += " ".join(self.stockPricesSell)
        self.output += "\n"
        self.output += "Stock Buy prices: "
        self.output += " ".join(self.stockPricesBuy)
        self.output += "\n"
        self.output += "Convert Price Rate: %f\n" % self.overPriceRate
        return self.output

    def SimpleInfoToString(self):
        self.output = "Bond Id: %s, " % self.bondId
        self.output += "Convert Price Rate: %f" % self.overPriceRate
        return self.output

    def Display(self, logger=None):
        if logger is None:
            print self.ToString()
        else:
            logger.Info(self.ToString())

    def DisplaySimple(self, logger=None):
        if logger is None:
            print self.SimpleInfoToString()
        else:
            logger.Info(self.SimpleInfoToString())

    @property
    def bondPricesSell(self):
        bondPricesSell = []
        # bond first 5 price to sell
        base = 9
        # print self.bondId
        # print self.bondJsonWebContent.split("~")
        for i in xrange(0, 9, 2):
            bondPricesSell.append(self.bondJsonWebContent.split("~")[base + i])
        return bondPricesSell

    @property
    def bondPricesBuy(self):
        bondPricesBuy = []
        # bond first 5 price to buy
        base = 19
        for i in xrange(0, 9, 2):
            bondPricesBuy.append(self.bondJsonWebContent.split("~")[base + i])
        return bondPricesBuy

    @property
    def stockPricesSell(self):
        stockPricesSell = []
        # stock first 5 price to buy
        base = 9
        for i in xrange(0, 9, 2):
            stockPricesSell.append(self.stockJsonWebContent.split("~")[base + i])
        return stockPricesSell

    @property
    def stockPricesBuy(self):
        stockPricesBuy = []
        # stock first 5 price to sell
        base = 19
        for i in xrange(0, 9, 2):
            stockPricesBuy.append(self.stockJsonWebContent.split("~")[base + i])
        return stockPricesBuy

    @property
    def overPriceRate(self):
        try:
            overPriceRate = float(self.bondPricesBuy[0]) / float(float(self.stockPricesSell[0]) * 100 / float(self.conStockRate)) - 1
        except ZeroDivisionError:
            print "hit ZeroDivisionError"
            overPriceRate = -1
        return overPriceRate

    def IsMatch(self):
        if self.overPriceRate < standard and self.overPriceRate > -1:
            return True
        else:
            return False

    def IsValid(self):
        try:
            return True
        except:
            print "%s not valid" % self.bondId
            return False


def SavePic(xdata, ydata, title="", xlabel="", ylabel="", units=""):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt

    if len(ydata) == 0:
        raise Exception("y value is empty")

    size = 14

    ratio = 100
    # "2019/05/16_1457"
    X_Parameter = map(lambda x: time.mktime(time.strptime(x, '%Y/%m/%d_%H%M')), xdata)
    Y_Parameter = map(lambda x: x * ratio, ydata)

    YMatchedIndexList = [index for index in xrange(len(Y_Parameter)) if Y_Parameter[index] < (standard * 100)]
    pointMatchList = [[X_Parameter[index], Y_Parameter[index]] for index in YMatchedIndexList]

    text = ""
    footTitle = "The following points are matched:\n%20s%20s" % ("date", "value")
    contentList = []
    for pointList in pointMatchList:
        xpoint = time.strftime('%Y/%m/%d_%H%M', time.localtime(pointList[0]))
        ypoint = pointList[1]
        # plt.annotate("%s" % (round(float(ypoint), 0)), (xpoint, ypoint))
        contentList.append("%20s%20s" % (xpoint, ypoint))
    text = "\n".join([footTitle, "\n".join(contentList)])
    #print text

    if 1:
        plt.figure(figsize=(20, 18))
        f, axarr = plt.subplots(nrows=1, ncols=2, figsize=(10, 9), sharex="none", sharey="none")
        subplots = axarr[0]
        subplots.set_title(title)
        subplots.set_xlabel(xlabel, size=size)
        subplots.set_ylabel(ylabel, size=size)
        subplots.plot(X_Parameter, Y_Parameter, '-')

        maxYValue = max(Y_Parameter)
        minYValue = min(Y_Parameter)

        yPointValues = []
        rangefromMintoMax = maxYValue - minYValue
        valueIncrement = rangefromMintoMax / 5
        for x in xrange(6):
            yPointValues.append((minYValue + x * valueIncrement))
        subplots.set_yticks(yPointValues)
        yPointStr = map(lambda x: "%f" % x, yPointValues)
        subplots.set_yticklabels(yPointStr)

        maxXValue = max(X_Parameter)
        minXValue = min(X_Parameter)

        xPointValues = []
        rangefromMintoMax = maxXValue - minXValue
        valueIncrement = rangefromMintoMax / 5
        for x in xrange(6):
            xPointValues.append((minXValue + x * valueIncrement))
        subplots.set_xticks([xPointValues[0], xPointValues[2], xPointValues[-1]])

        xPointStr = map(lambda x: time.strftime('%Y/%m/%d_%H%M', time.localtime(x)), xPointValues)
        subplots.set_xticklabels([xPointStr[0], xPointStr[2], xPointStr[-1]])

        subplots.set_ylim((minYValue * 1.5, maxYValue * 1.5))
        subplots.grid(True)

        subplots2 = axarr[1]
        subplots2.set_axis_off()
        subplots2.set_axis_off()
        plt.figtext(0.50, 0.2, text, fontsize=size)

        picFile = os.path.join("%s.png" % (title))
        print "Save image to %s" % picFile
        plt.savefig(picFile, format='png')
        plt.close()
    if 0:

        plt.figure(1, figsize=(16, 12))

        plt.title(title, size=size)
        plt.xlabel(xlabel, size=size)
        plt.ylabel(ylabel, size=size)
        plt.plot(X_Parameter, Y_Parameter, '-')

        # minYIndex = Y_Parameter.index(min(Y_Parameter))
        # plt.annotate("%s %s" % (Y_Parameter[minYIndex], units), (X_Parameter[minYIndex], Y_Parameter[minYIndex]))
        # plt.annotate("%s %s" % (Y_Parameter[0], units), (X_Parameter[0], Y_Parameter[0]))
        # plt.annotate("%s %s" % (Y_Parameter[-1], units), (X_Parameter[-1], Y_Parameter[-1]))

        YMatchedIndexList = [index for index in xrange(len(Y_Parameter)) if Y_Parameter[index] < (standard * 100)]
        pointMatchList = [[X_Parameter[index], Y_Parameter[index]] for index in YMatchedIndexList]

        for pointList in pointMatchList:
            xpoint = pointList[0]
            ypoint = pointList[1]
            plt.annotate("%s" % (round(float(ypoint), 0)), (xpoint, ypoint))

        ax = plt.gca()

        maxYValue = max(Y_Parameter)
        minYValue = min(Y_Parameter)

        yPointValues = []
        rangefromMintoMax = maxYValue - minYValue
        valueIncrement = rangefromMintoMax / 5
        for x in xrange(6):
            yPointValues.append((minYValue + x * valueIncrement))
        ax.set_yticks(yPointValues)
        yPointStr = map(lambda x: "%f" % x, yPointValues)
        ax.set_yticklabels(yPointStr)

        maxXValue = max(X_Parameter)
        minXValue = min(X_Parameter)

        xPointValues = []
        rangefromMintoMax = maxXValue - minXValue
        valueIncrement = rangefromMintoMax / 5
        for x in xrange(6):
            xPointValues.append((minXValue + x * valueIncrement))
        ax.set_xticks(xPointValues)

        xPointStr = map(lambda x: time.strftime('%Y/%m/%d_%H%M', time.localtime(x)), xPointValues)
        ax.set_xticklabels(xPointStr)

        ax.set_ylim((minYValue * 1.5, maxYValue * 1.5))
        ax.grid(True)

        text = ""
        footTitle = "The following points are matched:\n%4sdate%4svalue    "
        contentList = []
        for pointList in pointMatchList:
            xpoint = time.strftime('%Y/%m/%d_%H%M', time.localtime(pointList[0]))
            ypoint = pointList[1]
            # plt.annotate("%s" % (round(float(ypoint), 0)), (xpoint, ypoint))
            contentList.append("%4s%4s" % (xpoint, ypoint))
        text = "\n".join([footTitle, "\n".join(contentList)])
        #print text
        plt.figtext(0.01, 0.01, text, fontsize=size)
        #picFile = os.path.join("%s_%s.png" % (title, time.strftime('%Y-%m-%d_%H-%M-%S')))
        picFile = os.path.join("%s.png" % (title))

        print "Save image to %s" % picFile
        plt.savefig(picFile, format='png')
        plt.close()


def main():

    # targetbondId = "123001"
    # targetStockId = "300058"
    # targetMarket = "sz".upper()

    targetbondId = "110044"
    targetStockId = "600831"
    targetMarket = "sh".upper()

    with open("%s#%s.txt" % (targetMarket, targetbondId), "r") as f:
        bondPriceList = f.readlines()[2:-1]

    with open("%s#%s.txt" % (targetMarket, targetStockId), "r") as f:
        stockPriceList = f.readlines()[2:-1]

    def ConvertToDict(priceList):
        retMap = {}
        for priceLine in priceList:
            tempList = priceLine.split("\t")
            retMap["_".join((tempList[0],tempList[1]))] = tempList[5]
        return retMap

    bondPriceMap = ConvertToDict(bondPriceList)
    stockPriceMap = ConvertToDict(stockPriceList)

    allPriceKey = collections.OrderedDict()
    sortedData = sorted(set(bondPriceMap.keys()) & set(stockPriceMap.keys()))
    for shareKey in sortedData:
        allPriceKey[shareKey] = [bondPriceMap[shareKey], stockPriceMap[shareKey]]

    ignoreList = ["127009", "113020", "110050"]

    while True:
        targetBond = sys.argv[1] if len(sys.argv) == 2 else ""
        localtime = time.strftime('%Y-%m-%d', time.localtime(time.time()))
        filename = "bondOuput%s_%s_2.txt" % (targetBond, localtime)
        log = LogBuilder(filename)
        logger = log.logger

        monitorList = []
        with open("bondwatchList.txt", "r") as f:
            monitorList = map(lambda x: x.strip(), f.readlines())

        originJsonWebContent = ReadUrl(bondToStockUrl)
        if originJsonWebContent is None:
            continue

        originalDict = json.loads(originJsonWebContent)
        pageList = originalDict.get("rows", [])

        bondObjList = []
        for page in pageList:
            bond_idContentList = page.get("cell", [])
            bondId = bond_idContentList.get("bond_id", [])
            market = bond_idContentList.get("market", [])
            stockId = bond_idContentList.get("stock_id", [])
            if len(market) == 0:
                market = stockId[0:2]
            conStockRate = bond_idContentList.get("convert_price", [])
            bondObj = BondObj(bondId, market=market, stockId=stockId, conStockRate=conStockRate)
            if len(sys.argv) == 2:
                if targetBond == bondId:
                    bondObjList.append(bondObj)
            else:
                #if targetBond in monitorList:
                if bondObj.IsValid():
                    bondObjList.append(bondObj)

        bondIdconStockRateMap = {}
        for x in bondObjList:
            bondIdconStockRateMap[x.bondId] = x.conStockRate

        targetList = map(lambda x: str(x), bondIdconStockRateMap.keys())

        targetBondconStockRate = None
        if targetbondId in targetList:
            targetBondconStockRate = bondIdconStockRateMap[targetbondId]
        else:
            print "no found bond id %s" % targetbondId
            raise
        #overPriceRate = float(self.bondPricesBuy[0]) / float(float(self.stockPricesSell[0]) * 100 / float(self.conStockRate)) - 1

        overPriceRateTimeStampOverPriceMap = collections.OrderedDict()
        for key, value in allPriceKey.items():
            timeStamp = key
            bondPricesBuy = value[0]
            stockPricesSell = value[1]
            overPriceRate = float(bondPricesBuy) / float(float(stockPricesSell) * 100 / float(targetBondconStockRate)) - 1
            overPriceRateTimeStampOverPriceMap[timeStamp] = overPriceRate

        #print overPriceRateTimeStampOverPriceMap

        SavePic(overPriceRateTimeStampOverPriceMap.keys(),
                overPriceRateTimeStampOverPriceMap.values(),
                title="%s_%s_%s" % (targetMarket, targetbondId, targetStockId), xlabel="Date",
                ylabel="Over Price Rate %", units="")
        return
        matched = []
        with open(filename, "a") as f:
            if len(sys.argv) == 2:
                for bondObj in bondObjList:
                    bondObj.DisplaySimple(logger)
            else:
                logger.Info("total bond: %s " % len(bondObjList))
                for bondObj in bondObjList:
                    print "processing bond %s" % bondObj.bondId
                    if bondObj.IsMatch():
                        if bondObj.bondId in monitorList:
                            matched.append(bondObj)
                            logger.Info(bondObj.ToString())
                            if bondObj.bondId not in ignoreList:
                                logger.Info("get exchangable bond %s\n" % bondObj.bondId)
                                Mail("get exchangable bond %s\n" % bondObj.bondId, bondObj.output)
                logger.Info("matched bond: %s" % len(matched))
        time.sleep(1)
        break

if __name__ == "__main__":
    main()