import json, re
from msilib.schema import Error
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

def partitionString(string, openChar, closeChar, index=0):
    CHAR_IDs = {"{": {"close": "}", "type": "object"}, "[": {"close":"]", "type": "array"}, "\"": {"type": "string", "close":"\""}}
    arr = []
    string = string[index:]
    for i, signifier in enumerate(string):
        startingIndex = i + index
        nextSign = string[i+1]
        if signifier==openChar:
            arr.append([signifier, i+index, len(string)])
            nextIndex = i + 1
            while nextSign != closeChar:
                print(nextIndex, len(string)-1)
                nextSign = string[nextIndex]
                if nextSign in CHAR_IDs.keys():
                    return partitionString(string, nextSign, CHAR_IDs[nextSign]['close'], index=nextIndex)
                nextIndex+=1
        else:
            next
                
    print(arr)

            



def forceClose(dataFile):
    # identifys loose objects involuntarily inserted into streams via early pulls
    with open(dataFile, 'r', encoding="utf-8") as file:
        myString = file.read()
        asciiString = myString.encode('ascii', 'ignore')
        asciiString = asciiString.replace(b'\x19', b'')
        myString = asciiString.decode('utf-8', 'ignore')
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
    regURL = re.compile(r'(\|[^\|:]+:)+')
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
        h= 0
        for gm in groupMatches:
            if (gm!=':\"') and (gm!='\"'):
                toAdd.append(re.sub('\"', "", gm).strip())
            

        newString = newString + myString[lastStart:start+1] + "\"" +"".join(toAdd) + "\","
        lastStart = stop
    
    urlMatcher = (r"\{\"url\":\"(.+)\"(?=,)")
    newString = newString + myString[lastStart:]
    urlsAndObjects = re.split(regURL, newString)
    urls = list(filter(lambda x: re.match(regURL, x), urlsAndObjects))
    objects = filter(lambda x: ((x!='')and(re.match(regURL, x))==None), urlsAndObjects)
    filteredObjects = []
    for i, o in enumerate(objects):
        # Stream writes in 3 ways:
            # writing of object attributes are cut off by a repeat call
            # An Object's stream exhausts mid-parameter, causing parms to be cut off.
            # the intercepting object can also be cut off mid paramter by the starting streams return.   
        try:
            # 1st: see if the stream was written in one buffer 
            json.loads(o)
            print('did not happen')
        except json.decoder.JSONDecodeError as error:
            msg = error.args[0]
            charAt = int(re.findall(r'char (\d+)', msg)[0])
            looseObjs = []
            looseObjs.append(o[:charAt])
            if msg.startswith("Extra"):
                try:
                    firstData = json.loads(o[:charAt])
                    secondData = json.loads(o[charAt+2:])
                    if firstData==secondData:
                        firstData['url'] = urls[i]
                        filteredObjects.append(firstData)
                except json.decoder.JSONDecodeError as error2:
                    msg = error2.args[0]
                    charAt = int(re.findall(r'char (\d+)', msg)[0])
                    print(firstData)
            else:
                # expecting ',' delimiter: line 1 column n+1 (char n)
                # case: stream interupts object with url indicator with the entire combined string from the api
                # solution: get the object with the greater length and check to see if it has the call url parameter inside, if not pop it from interupted object and place in full object
                while o[charAt]!="{":
                    charAt-=1

                try:
                    stringObj = o[charAt:]
                    fullObject = json.loads(stringObj)
                except json.decoder.JSONDecodeError as er:
                    msg = er.args[0]
                    charStreamReturn = int(re.findall(r'char (\d+)', msg)[0])
                    try:
                        filteredObjects.append(json.loads(stringObj[:charStreamReturn]))

                    except json.decoder.JSONDecodeError as er2:
                        msg = er2.args[0]
                        offendingString = int(re.findall(r'char (\d+)', msg)[0])
                        endOfObject = o[-100:]
                        # stringObj, looseObjs[-1], offendingString
                        closer = stringObj[offendingString:].index(endOfObject)
                        secondHalf = stringObj[offendingString-2:][:closer+len(endOfObject)+2]
                        fullObject = looseObjs[-1] + secondHalf
                        finalForm = json.loads(fullObject)
                        finalForm['url'] = urls[i]
                        filteredObjects.append(finalForm)

    with open(dataFile.replace("txt", "json"), "w") as jfile:
        jfile.write(json.dumps(filteredObjects))
    
    return None

forceClose("./requests/server/collections/toFix/cbk2.txt")

#partitionString('{"type": "boose", "cost": 129.99, "tax": 23.22, "devices": ["soundbar", "voice remote", "smart alexa"], "customerInfo": {"address": "4501 Brekley Ridge", "zipCode": "75921", "repeat": true, "_id": {"oid": 2391312084123, "REF": 129031923}}}',
#openChar="{", closeChar="}")
