import json, re, os, unicodedata
from pprint import pprint

from multiprocessing import Pool
from tracemalloc import start

from cv2 import Mat
from numpy import append

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
        jj = json.loads(myString)
        #jj = json.loads(j)


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

    filename = 'parsed' + dataFile.split('/')[-1]
    filename = "/".join(dataFile.split('/')[:-1] + [filename])
    with open(filename, 'w', encoding="utf-8") as file:
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

def canItBe(func, error, stringMain, testStrings):
    test_cases = [stringMain+x for x in testStrings]
    print([stringMain[-100:]+"<TESTCASES>"+x[:100] for x in testStrings])
    r = []
    for t in test_cases:
        try:

            func(t)
            r.append(True)
        except error as e:
            r.append(False)
    return r

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
        
        

    

    # pprint([x for x in re.findall(r'(?!,\s)(.{100})(?=\{\"data\")(.{70})', myString)])
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
    regFive = re.compile(r"(?=:\{?\[?\")(:\")(.*?)(?=\"[\}\],\{\[]+\"[A-z])")
    regxFour = re.compile(r"(?=\:\")(\:\")([^\\\"]+)(\")(?!\"[\}\]\s\,])([^\:\}\]]+\,)") # (?=:")(:")([^\\"]+)(")(?!"[\}\]\s,])([^:\}\]]+,)
    regTwo = re.compile(r"((\{\s*|\"success\"\s*:\s*true,)\s*\"data\")")
    regURL = re.compile(r'(\|[^\s\|:]+:)+') # make sure resulting object is not encased in a string, no spaces perhaps?
    regxFourImp = re.compile(r"(?=:\")(:\")([^\\\"]+)(\")(?!\"[\}\]\s,])([^:\}\]]+(,|\}|\]))")
    regThree = re.compile(r"(\"\w+\":)")
    #myString = re.sub(regThree, r'   \1   ', myString)
    # newResponse = [x.span() for x in re.finditer(regTwo, myString)]
    # urls = [x.span() for x in re.finditer(regURL, myString)]
    # [print(myString[x[0]-12:x[1]+50]) for x in newResponse]
    
    
    # for j, group in enumerate(l):#re.finditer(regFive, myString):
    #     if j%10_000==0:
    #         print(j)
    #     groupMatches = group.groups()
    #     if '"' in groupMatches[1]:
    #         print(groupMatches[1])
    #         start, stop = group.span()
    #         data = re.sub(r'(?<=[^\\])"', "",groupMatches[1])
    #         newString = newString + myString[lastStart:start] + groupMatches[0] + data
    #         lastStart = stop
    #     else:
    #         start, stop = group.span()
    #         newString = newString + myString[lastStart:stop] 
    #         lastStart = stop
    #newString = newString + myString[lastStart:]
    urlsAndObjects = re.split(regURL, myString)
    urls = list(filter(lambda x: re.match(regURL, x), urlsAndObjects))
    objects = list(filter(lambda x: ((x!='')and(re.match(regURL, x))==None), urlsAndObjects))
    filteredObjects = []
    k=0
    enders = []
    oS = []
    eS = []


    print("URLS:", len(urls), "OBJECTS:", len(objects))
    for i, o in enumerate(objects):
        completeObjectRegex = re.compile(r"(,\s)(?=\{\"(data|success)\")") # check to see if object is complete and duplicated
        brokenObjectRegex = re.compile(r"(?<!,\s)(\{\"(data|success)\")")
        completeObjects = re.split(completeObjectRegex, o)

        if len(completeObjects)==1:
            # object broken by stream, we know that the stream breakpoint is the start of the original string
            # search nonsplit string for its beginning, get both the span to find break location
            # object is closed successfully, so get ending and search the stream breaker for the ending location
            # append broken first half with broken second helf compare objects equality and add single object
            startOfStream = re.sub(r'([\"\{\}\[\]\(\).$])', r'\\\1', o[:500])
            endOfStream = re.sub(r'([\"\{\}\[\]\(\).$])', r'\\\1', o[-500:])
            starts = [x.span() for x in re.finditer(startOfStream, o)]
            ends = [x.span() for x in re.finditer(endOfStream, o)]
            #print(o[ends[0][1]:ends[0][1]+100])
            if len(starts)!=2 or len(ends)!=2:
                print(starts, ends)
                raise re.error('indicators contain an unescaped general character')
            
            cutoff = o[:starts[1][0]]
            s1 = o[starts[0][0]:starts[1][0]] + o[ends[0][1]+1:] 
            s2 = o[starts[1][0]:ends[0][1]]
            a = max([s1, s2], key=len)
            b = o[starts[0][0]:starts[1][0]]#min([s1, s2], key=len)
            
            newString = ''
            lastStart = 0
            for group in re.finditer(regFive, a):
                groupMatches = group.groups()
                if '"' in groupMatches[1]:
                    start, stop = group.span()
                    data = re.sub(r'(?<![\\])"', " ",groupMatches[1])
                    newString = newString + a[lastStart:start] + groupMatches[0] + data
                    lastStart = stop
                else:
                    start, stop = group.span()
                    newString = newString + a[lastStart:stop] 
                    lastStart = stop
            newString = newString + a[lastStart:]
            try:
                filteredObjects.append(json.loads(newString))
                
            except json.decoder.JSONDecodeError as e:

                if e.pos == len(newString)-1:
                    try:
                        print(e)
                        print(newString[-200:])
                        print(newString[:200])
                        json.loads(newString)

                    except json.decoder.JSONDecodeError as je:
                        print(je)
                        with open('g.json', 'w', encoding='utf-8') as h:
                            h.write(newString)
                        
                else:
                    msg = e.args[0]
                    charAt = e.pos
                    
                    endOfStream = re.sub(r'([\"\{\}\[\]\(\).$])', r'\\\1', newString[e.pos:e.pos+1000])
                    mat = [x.span() for x in re.finditer(endOfStream, newString[:e.pos])]
                    eos = newString[e.pos:e.pos+1000] 
                    eos = re.sub(r'([\"\{\}\[\]\(\).$])', r'\\\1', eos)
                    mat = [x.span() for x in re.finditer(eos, newString)]
                    returnal = b[-100:] + newString[mat[0][0]:mat[0][1]]
                    unstreamed = newString[mat[1][0]-100:mat[1][1]]
                    n=1
                    while returnal not in unstreamed:
                        returnal = b[-100+n:] + newString[charAt-n:][:100]
                        n +=1
                        if n > 50:
                            break
                    
                    if n == 51:
                        file = dataFile.replace('.txt', '')
                        file = file.replace('./requests/server/collections/toFix/', '')
                        with open(f'./requests/server/collections/toFix/fixes/{file}ToFix.txt', 'w', encoding='utf-8') as f:
                            f.write(f"<NEWSTRING{i}>")
                            f.write(newString[:charAt])
                            f.write(f"<ORIG_OBJECT{i}>")
                            f.write(cutoff)
                            f.write(f"<S1{i}>")
                            f.write(s1)
                            f.write(f"<S2{i}>")
                            f.write(s2)
                            f.write('<END_OF_STRING>')
                    else:
                        try:
                            n-=1
                            secondTry = b + newString[charAt-n:]
                            json.loads(secondTry)
                            print('passed 2')
                        except json.decoder.JSONDecodeError as e2:
                            print(e2)
                            print(f"{secondTry[e2.pos-500:e2.pos]}" + f"<<<<<{secondTry[e2.pos]}>>>>>",  f"{secondTry[e2.pos+1:e2.pos+500]}" )
                            
                    
                    
                    
                    #print([(newString[x[0]-100:x[0]], f"<<{newString[x[0]:x[1]]}>>", newString[x[1]:x[1]+100]) for x in mat])
                   
                    # while mat == []:
                    #     charAt-= 1
                    #     eos = b[-100:] + newString[charAt:charAt+100]
                    #     print(eos)
                    #     eos = re.sub(r'([\"\{\}\[\]\(\).$])', r'\\\1', eos)
                    #     mat = [x.span() for x in re.finditer(eos, newString[:e.pos])]
                        
                    # print(mat)
                    # returningString = newString[e.pos+1:e.pos+500]
                    # startOfStream = re.sub(r'([\"\{\}\[\]\(\).$])', r'\\\1', returningString)
                    # # print([x.span() for x in re.finditer(startOfStream, newString[charAt:])])
                    # endOfStream = re.sub(r'([\"\{\}\[\]\(\).$])', r'\\\1', b[-500:])
                    # matches = [x.span() for x in re.finditer(endOfStream, newString)]
                    # matches = [re.sub(r'([\"\{\}\[\]\(\).$])', r'\\\1',newString[x[1]:x[1]+500])for x in matches]
                    # matches = [x.span() for x in re.finditer(matches[0], newString)]
                    #print("\n", matches)
            print('#'*50, f'object {i}', f'length: {len(o)}', '#'*50)
            print('\n')

        else:
            try:
                filteredObjects.append(json.loads(completeObjects[0]))
            except json.decoder.JSONDecodeError as e2:
                secondTry = completeObjects[0]
                lastStart = 0
                newString = ''
                for group in re.finditer(regFive, secondTry):
                    groupMatches = group.groups()
                    if '"' in groupMatches[1]:
                        start, stop = group.span()
                        data = re.sub(r'(?<![\\])"', " ",groupMatches[1])
                        newString = newString + secondTry[lastStart:start] + groupMatches[0] + data
                        lastStart = stop
                    else:
                        start, stop = group.span()
                        newString = newString + secondTry[lastStart:stop] 
                        lastStart = stop
                newString = newString + secondTry[lastStart:]
                try:
                    filteredObjects.append(json.loads(newString))
                except json.decoder.JSONDecodeError as e3:
                    print(i, e3)

    newFile = dataFile.split("/")
    fileName = newFile[-1].replace('.txt', '.json')
    newFile = "/".join(newFile[:-1]+["fixes"]+[fileName])
    with open(newFile, 'w', encoding='utf-8') as final:
        final.write(json.dumps(filteredObjects))

        # else: 
        #     # print(completeObjects[0]==completeObjects[-1])
    # for i, o in enumerate(objects):
    #     # Stream writes in 3 ways:
    #         # writing of object attributes are cut off by a repeat call
    #         # An Object's stream exhausts mid-parameter, causing parms to be cut off.
    #         # the intercepting object can also be cut off mid paramter by the starting streams return.   
    #     try:
    #         # 1st: see if the stream was written in one buffer
    #         filteredObjects.append(json.loads(o))
        
    #     except json.decoder.JSONDecodeError as error:
    #         print(error)
    #         msg = error.args[0]
    #         charAt = int(re.findall(r'char (\d+)', msg)[0])
    #         looseObjs = []
    #         looseObjs.append(o[:charAt])
    #         if msg.startswith("Extra"):
    #             try:
    #                 firstData = json.loads(o[:charAt])
    #                 secondData = json.loads(o[charAt+2:])
    #                 if firstData==secondData:
    #                     firstData['url'] = urls[i]
    #                     filteredObjects.append(firstData)
    #             except json.decoder.JSONDecodeError as error2:
    #                 msg = error2.args[0]
    #                 charAt = int(re.findall(r'char (\d+)', msg)[0])
    #         elif 'Invalid control' in msg:
    #             print(msg, charAt)
    #             try:
    #                 controlObject = o[:charAt] + o[charAt+1:]
    #                 filteredObjects.append(json.loads(controlObject))

    #             except json.decoder.JSONDecodeError as errorControl:
                    
    #                 msg = errorControl.args[0]
    #                 charAt = int(re.findall(r'char (\d+)', msg)[0])
    #                 print(errorControl, charAt)
    #                 print(controlObject[charAt-10:charAt] + f"<<<{controlObject[charAt]}>>>" + controlObject[charAt+1:charAt+10])

            
    #         else:
    #             # expecting ',' delimiter: line 1 column n+1 (char n)
    #             # case: stream interupts object with url indicator with the entire combined string from the api
    #             # solution: get the object with the greater length and check to see if it has the call url parameter inside, if not pop it from interupted object and place in full object
    #             print(msg)
    #             print(o[charAt-15:charAt], f"<<<<{o[charAt]}>>>>", o[charAt+1:charAt+15])
    #             while o[charAt]!="\"": # use "{" for broken streams and "\""
    #                 if o[charAt]=='{':
    #                     break
    #                 charAt-=1
    #             try:
    #                 print(o[charAt-15:charAt], f"<<<<{o[charAt]}>>>>", o[charAt+1:charAt+15])
    #                 stringObj = o[charAt:]
    #                 fullObject = json.loads(stringObj)
    #             except json.decoder.JSONDecodeError as er:
    #                 msg = er.args[0]
    #                 charStreamReturn = int(re.findall(r'char (\d+)', msg)[0])
    #                 print(msg)
    #                 print(o[charAt:][charStreamReturn-15:charStreamReturn], f"<<<<{o[charAt:][charStreamReturn]}>>>>", o[charAt:][charStreamReturn+1:charStreamReturn+15])
    #                 try:
    #                     nextObject = json.loads(stringObj[:charStreamReturn])
    #                     nextObject['url'] = urls[i]
    #                     filteredObjects.append(nextObject)

    #                 except json.decoder.JSONDecodeError as er2:
    #                     try:
    #                         print(msg2)   
    #                         msg2 = er2.args[0]
    #                         offendingString = int(re.findall(r'char (\d+)', msg)[0])
    #                         endOfObject = o[-100:]
    #                         closer = stringObj[offendingString:].index(endOfObject)
    #                         secondHalf = stringObj[offendingString-2:][:closer+len(endOfObject)+2]
    #                         fullObject = looseObjs[-1] + secondHalf
    #                         finalForm = json.loads(fullObject)
    #                         finalForm['url'] = urls[i]
    #                         filteredObjects.append(finalForm)
    #                     except:
    #                         msg = er2.args[0]
    #                         offendingString = int(re.findall(r'char (\d+)', msg)[0])
    #                         print(fullObject[offendingString], repr(fullObject[offendingString]), ord(fullObject[offendingString]))
    #                         raise ValueError

    #     print(f'@{i}. FilteredObjects = {len(filteredObjects)} . {type(filteredObjects[-1])}')


    # with open(dataFile.replace("txt", "json"), "w") as jfile:
    #     jfile.write(json.dumps(filteredObjects))
    
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
            





# forceClose("./requests/server/collections/toFix/cashback420.txt")
destroyIDs("./requests/server/collections/trips/trips051622.json")
#partitionString('{"type": "boose", "cost": 129.99, "tax": 23.22, "devices": ["soundbar", "voice remote", "smart alexa"], "customerInfo": {"address": "4501 Brekley Ridge", "zipCode": "75921", "repeat": true, "_id": {"oid": 2391312084123, "REF": 129031923}}}',
#openChar="{", closeChar="}")
