import json, re, os, unicodedata
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
        myString = myString.replace("\x18", "")
        myString = myString.replace("\x19", "")
        myString = myString.replace("\x13", "")
        myString = myString.replace("\x14", "")
        myString = myString.replace("\x02", "")
        myString = myString.replace("\x10", "")
        myString = myString.replace("\x11", "")
        myString = myString.replace("\x1c", "")
        myString = myString.replace("\x1e", "")
        myString = myString.replace("\x1d", "")
        myString = myString.replace("\x0b", "")
        
        

    


    # queue = []#deque(maxlen=10_000)
    # reg = r"(\"|\{|\[|\}|\])"
    # parsed = {'{': "OO", "}": "OE", "[": "AO", "]": "AE", "\"": "SS"}
    # closers  = {"OO": "OE", "AO": "AE", "SS":"SS"}
    #matches = [(x.span()[0], parsed[x.group()]) for x in re.finditer(reg, myString)]
    # re.compile(r'\:(?=\")\"([^\"]+)\"(?=[\}\],])') # pulls out all strings
    # re.compile(r'\:(?=\[)([^\]]+)(?=\])') # pulls out all arrays
    # re.compile(r'(?=\{)\{([^\}])+(?=\})') // OPEN CLOSE DO NOT CONTAIN OBJECTS  (?=\{)\{([^\}\[\{])+(?=\})\}
    # GETS EVERY ARRAY = (?=\[)\[([^\[\]])+(?=\])\]
    # GETS STRINGS = re.compile("(?=\:\")(\:\")([^\"])+(\".{1})(?=[\}\]\"\s\,])")
    regxFour = re.compile(r"(?=\:\")(\:\")([^\\\"]+)(\")(?!\"[\}\]\s\,])([^\:\}\]]+\,)") # (?=:")(:")([^\\"]+)(")(?!"[\}\]\s,])([^:\}\]]+,)
    regTwo = re.compile(r"((\{\s*|\"success\"\s*:\s*true,)\s*\"data\")")
    regURL = re.compile(r'(\|[^\s\|:]+:)+') # make sure resulting object is not encased in a string, no spaces perhaps?
    regxFourImp = re.compile(r"(?=:\")(:\")([^\\\"]+)(\")(?!\"[\}\]\s,])([^:\}\]]+(,|\}|\]))")
    regThree = re.compile(r"(\"\w+\":)")
    #myString = re.sub(regThree, r'   \1   ', myString)
    # newResponse = [x.span() for x in re.finditer(regTwo, myString)]
    # urls = [x.span() for x in re.finditer(regURL, myString)]
    # [print(myString[x[0]-12:x[1]+50]) for x in newResponse]
    newString = ''
    lastStart = 0
    for group in re.finditer(regxFourImp, myString):
        start, stop = group.span()
        groupMatches = group.groups()
        toAdd =[]
        for gm in groupMatches:
            if (gm!=':\"') and (gm!='\"'):
                toAdd.append(re.sub(r'(?=[^\\])([^\\]\")', "", gm).strip())

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
            filteredObjects.append(json.loads(o))
        
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
            elif 'Invalid control' in msg:
                print(msg, charAt)
                try:
                    controlObject = o[:charAt] + o[charAt+1:]
                    filteredObjects.append(json.loads(controlObject))

                except json.decoder.JSONDecodeError as errorControl:
                    
                    msg = errorControl.args[0]
                    charAt = int(re.findall(r'char (\d+)', msg)[0])
                    print(errorControl, charAt)
                    print(controlObject[charAt-10:charAt] + f"<<<{controlObject[charAt]}>>>" + controlObject[charAt+1:charAt+10])

            
            else:
                # expecting ',' delimiter: line 1 column n+1 (char n)
                # case: stream interupts object with url indicator with the entire combined string from the api
                # solution: get the object with the greater length and check to see if it has the call url parameter inside, if not pop it from interupted object and place in full object
                while o[charAt]!="\"": # use "{" for broken streams and "\""
                    charAt-=1
                try:
                    stringObj = o[charAt:]
                    fullObject = json.loads(stringObj)
                except json.decoder.JSONDecodeError as er:
                    msg = er.args[0]
                    charStreamReturn = int(re.findall(r'char (\d+)', msg)[0])
            
                    try:
                        nextObject = json.loads(stringObj[:charStreamReturn])
                        nextObject['url'] = urls[i]
                        filteredObjects.append(nextObject)

                    except json.decoder.JSONDecodeError as er2:
                        try:
                            print(msg2)   
                            msg2 = er2.args[0]
                            offendingString = int(re.findall(r'char (\d+)', msg)[0])
                            endOfObject = o[-100:]
                            closer = stringObj[offendingString:].index(endOfObject)
                            secondHalf = stringObj[offendingString-2:][:closer+len(endOfObject)+2]
                            fullObject = looseObjs[-1] + secondHalf
                            finalForm = json.loads(fullObject)
                            finalForm['url'] = urls[i]
                            filteredObjects.append(finalForm)
                        except:
                            msg = er2.args[0]
                            offendingString = int(re.findall(r'char (\d+)', msg)[0])
                            print(fullObject[offendingString], repr(fullObject[offendingString]), ord(fullObject[offendingString]))
                            raise ValueError

        print(f'@{i}. FilteredObjects = {len(filteredObjects)} . {type(filteredObjects[-1])}')


    with open(dataFile.replace("txt", "json"), "w") as jfile:
        jfile.write(json.dumps(filteredObjects))
    
    return None

# for folder, _, files in os.walk("./requests/server/collections/toFix/"):
    
#     for file in files:
#         if file.endswith('json'):
#             next
#         else:
#             try:
#                 forceClose(folder+file)
#                 print('successfully parse {}'.format(file))    
#             except BaseException as error:
#                 print(error, file)
            





forceClose("./requests/server/collections/toFix/cashback420.txt")

#partitionString('{"type": "boose", "cost": 129.99, "tax": 23.22, "devices": ["soundbar", "voice remote", "smart alexa"], "customerInfo": {"address": "4501 Brekley Ridge", "zipCode": "75921", "repeat": true, "_id": {"oid": 2391312084123, "REF": 129031923}}}',
#openChar="{", closeChar="}")
