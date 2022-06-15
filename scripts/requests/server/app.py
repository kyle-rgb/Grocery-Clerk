from flask import Flask, request, render_template

import time, json, re, os, datetime as dt


app = Flask(__name__)
i = 0 
@app.route('/docs', methods=['GET', 'POST'])
def docs():
    d = dt.datetime.now()
    dateCode= dt.datetime.strftime(d, "%m%d%y")
    global i     
    # TODO: use continue to communicate program execution back to extension
    if request.method=="POST":
        i += 25
        data = json.loads(request.get_data(as_text=True))
        length = request.content_length
        contentType = request.args.get("type")

        if os.path.exists(f"./collections/{contentType}/{contentType}{dateCode}.json"):
            with open(f'./collections/{contentType}/{contentType}{dateCode}.json', 'r', encoding='utf-8') as file:
                past_data = json.loads(file.read())
                data.extend(past_data)
        else:
            try:
                os.mkdir(f"./collections/{contentType}")
            except FileExistsError():
                print('skipping directory creation')
        with open(f'./collections/{contentType}/{contentType}{dateCode}.json', 'w', encoding='utf-8') as file:
            file.write(json.dumps(data))
        print(f'successfly wrote {length} to disk. have received {i} objects')

        return({"data": {"length": length}, "continue": 1})

@app.route('/fixit')
def fixit():
    i = int(request.args.get("index"))
    # BUG: 
    # past scraped data that has urls mixed with streams, will need to parse further to get data out of it. Any Sales Data Pre-April 28th has this issue
    oldScrapedDocs = ["cashback/cashback420.txt", "cashback/cbk.txt", "cashback/cbk2.txt", "digital/digital19.txt", "digital/digital_1_420.txt", "digital/digital_2_420.txt",\
        "digital/digital.txt", "digital/digital8.txt", "digital/digital299.txt"]
    regex = re.compile(r"\|?([A-z0-9\/\.?=&]+\:\|[A-z0-9\/\.?=&]+\:)(.+?)\|")
    
    with open(f"./collections/{oldScrapedDocs[i]}", "r") as file:
        docString = file.read()
        docString += "|"
        entries = re.findall(regex, docString)
        dataArray = []
        j = 0
        for route, object in entries:
            newObjects = object.split("}, ")
            routes = route.split(":|")
            try:
                object = json.loads(newObjects)
                object["url"] = "https://www.kroger.com/" + routes[0]
                dataArray.append(object)
            except:
                dataArray.append(0)

    return {"data": dataArray}


if __name__ == "__main__":
    app.config['TEMPLATES_AUTO_RELOAD'] = True
    app.run(debug = False)
