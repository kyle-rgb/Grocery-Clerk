import json, re
from pprint import pprint

from multiprocessing import Pool
from tracemalloc import start

def fixData():

    with open('./requests/server/collections/toFix/aprilTrips.txt', 'r', encoding="utf-8") as file:
        myString = file.read()


    for j in range(100_000):
        try:
            json.loads(myString)
            break
        except json.decoder.JSONDecodeError as jError:
            print(jError.colno)
            newString = myString[:jError.colno-2] + myString[jError.colno-1:]
            myString = newString


    with open("./requests/server/collections/toFix/aprilTrips.json", "w", encoding="utf-8") as z:
        z.write(json.dumps(myString))


def destroyIDs(dataFile):
    with open(dataFile, 'r', encoding="utf-8") as file:
        myString = file.read()
        j = json.loads(myString)
        jj = json.loads(j)


        for entry in jj:
            if 'data' in entry:
                data = entry['data']
                if isinstance(data, list):
                    data = data[-1]
                    if 'tenders' in data:
                        data['tenders'][0]['emv'] = {}
                        data['tenders'][0]['referenceCode'] = ""
                    if 'purchaseHistoryID' in data:
                        data['purchaseHistoryID'] = ''
                    if 'loyaltyId' in data:
                        data['loyaltyId'] = ''

    with open('parsed'+dataFile, 'w', encoding="utf-8") as file:
        file.write(json.dumps(jj))
        

    return None

def forceClose(dataFile):
    # identifys loose objects involuntarily inserted into streams via early pulls
    with open(dataFile, 'r', encoding="utf-8") as file:
        myString = file.read()
        myString.encode('ascii', 'replace')

    # def mp_worker():
    #     pass

    # def mp_handler():
    #     pool = Pool(16)
    #     pool.map(mp_worker, )
    #     pass


    queue = []#deque(maxlen=10_000)
    reg = r"(\"|\{|\[|\}|\])"
    parsed = {'{': "OO", "}": "OE", "[": "AO", "]": "AE", "\"": "SS"}
    closers  = {"OO": "OE", "AO": "AE", "SS":"SS"}
    #matches = [(x.span()[0], parsed[x.group()]) for x in re.finditer(reg, myString)]
    # re.compile(r'\:(?=\")\"([^\"]+)\"(?=[\}\],])') # pulls out all strings
    # re.compile(r'\:(?=\[)([^\]]+)(?=\])') # pulls out all arrays
    # re.compile(r'(?=\{)\{([^\}])+(?=\})') // OPEN CLOSE DO NOT CONTAIN OBJECTS  (?=\{)\{([^\}\[\{])+(?=\})\}
    # GETS EVERY ARRAY = (?=\[)\[([^\[\]])+(?=\])\]
    # GETS STRINGS = re.compile("(?=\:\")(\:\")([^\"])+(\".{1})(?=[\}\]\"\s\,])")
    regxFour = re.compile(r"(?=\:\")(\:\")([^\"]+)(\")(?!\"[\}\]\s\,])([^\:\}\]]+\,)")
    regTwo = re.compile(r"((\{\s*|\"success\"\s*:\s*true,)\s*\"data\")")
    regURL = re.compile(r'(\|([A-z0-9\/?\.=&]+):){2}([\[\{])')
    regThree = re.compile(r"(\"\w+\":)")
    #myString = re.sub(regThree, r'   \1   ', myString)
    # newResponse = [x.span() for x in re.finditer(regTwo, myString)]
    # urls = [x.span() for x in re.finditer(regURL, myString)]
    # [print(myString[x[0]-12:x[1]+50]) for x in newResponse]
    newString = ''
    lastStart = 0
    for group in re.finditer(regxFour, myString):
        start, stop = group.span()
        groupMatches = group.groups()
        toAdd =[]

        for gm in groupMatches:
            if (gm!=':\"') and (gm!='\"'):
                toAdd.append(re.sub('\"', "", gm))
            

        newString = newString + myString[lastStart:start-1] + "".join(toAdd) + "\","
        lastStart = stop
    
    print(newString[63088-500:63088+200])
    # newString = re.sub(regURL,r',\3"url":"www.kroger.com/\2",', newString)
    # newString = "[" + newString[1:] + "]"
    # for i in range(50):
    #     try:
    #         json.loads(newString)
    #     except json.decoder.JSONDecodeError as Error:
    #         start_number = (Error.colno)-1
    #         err = Error.args
    #         print("ERROR:")
    #         print(Error)
    #         print("\n")
    #         errorFigure = newString[start_number]
    #         print(newString[start_number-20:start_number]+f"<{newString[start_number]}>"+newString[start_number+1:start_number+20])
    #         if "delimiter" in Error.args[0]:
    #             while errorFigure != "\"":
    #                 start_number-=1
    #                 errorFigure = newString[start_number]        
    #             newString = newString[:start_number] + newString[start_number+1:]
    #         elif "control character" in Error.args[0]:
    #             newString = newString[:start_number] + newString[start_number+1:]
    #         else:
    #             raise ValueError('newError')
            
    #         print(newString[start_number-20:start_number+20])
    #         print("\n")
            
    # for i in range(0, len(matches), 2):
    #     index = matches[i][0]
    #     parsedCode = matches[i][1]
    #     if parsedCode in ["OE", "AE"]:
    #         next
    #     elif parsedCode == "SS":
    #         if matches[i+1][1]=='SS':
    #             finished = matches[i+1][0]+1
    #     else:
    #         wantedSignifier = closers[parsedCode]
    #         finished = 0
    #         j = i
    #         while matches[j][1]!=wantedSignifier:
    #             j+=1
    #         finished = matches[j][0]+1
    #     print(f'parsedCODE : {parsedCode} starts @ {index} and ends @ {finished}')
    #     #print(matches[:i])
    #     print(myString[index:finished])
        

    # print(len(queue))
    return None

forceClose("./requests/server/collections/toFix/cbk2.txt")