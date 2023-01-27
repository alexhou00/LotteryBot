map_nums ={u'零':0, u'一':1, u'二':2, u'三':3, u'四':4, 
           u'五':5, u'六':6, u'七':7, u'八':8, u'九':9, 
           u'十':10, u'百':100, u'千':1000, u'万':10000,
           u'０':0, u'１':1, u'２':2, u'３':3, u'４':4, u'５':5, u'６':6, u'７':7, u'８':8, u'９':9,
           u'壹':1, u'贰':2, u'叁':3, u'肆':4, u'伍':5, 
           u'陆':6, u'柒':7, u'捌':8, u'玖':9, u'拾':10, 
           u'佰':100, u'仟':1000, u'萬':10000, u'亿':100000000,
           u'貳':2, u'參':3, u'陸':6, u'億':100000000, u'兩':2}

def getResultForDigit(a, encoding="utf-8"):
    if isinstance(a, str):
        # a = a.decode(encoding)
        pass

    count = 0 
    result = 0
    tmp = 0
    Billion = 0  
    while count < len(a):
        tmpChr = a[count]
        tmpNum = map_nums.get(tmpChr, None)
        if type(tmpNum) == type(None):
            count += 1
            continue
        if tmpNum == 100000000:
            result = result + tmp
            result = result * tmpNum

            Billion = Billion * 100000000 + result 
            result = 0
            tmp = 0
        elif tmpNum == 10000:
            result = result + tmp
            result = result * tmpNum
            tmp = 0

        elif tmpNum >= 10:
            if tmp == 0:
                tmp = 1
            result = result + tmpNum * tmp
            tmp = 0
        elif tmpNum is not None:
            tmp = tmp * 10 + tmpNum
        count += 1
    result = result + tmp
    result = result + Billion
    return result