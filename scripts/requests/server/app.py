from flask import Flask, request, render_template

import time, json, re, os


app = Flask(__name__)

@app.route('/docs', methods=['GET', 'POST'])
def docs():
    if request.method=="POST":
        data = json.loads(request.get_data(as_text=True))
        length = request.content_length

        if os.path.exists("./collections/cashback/cashback050322.json"):
            with open(f'./collections/cashback/cashback050322.json', 'r', encoding='utf-8') as file:
                past_data = json.loads(file.read())
                data.extend(past_data)

        with open(f'./collections/cashback/cashback050322.json', 'w', encoding='utf-8') as file:
            file.write(json.dumps(data))
        print(f'successfly wrote {length} to disk')

        return({"data": {"length": length}, "continue": 1})

    else:
        data = json.loads(request.get_data(as_text=True))
        length = request.content_length
        if os.path.exists("./collections/cashback/cashback050322.json"):
            with open(f'./collections/cashback/cashback050322.json', 'r', encoding='utf-8') as file:
                past_data = json.loads(file.read())
                data.extend(past_data)

        with open(f'./collections/cashback/cashback050322.json', 'w', encoding='utf-8') as file:
            file.write(json.dumps(data))
        print(f'successfly wrote {length} to disk')

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
