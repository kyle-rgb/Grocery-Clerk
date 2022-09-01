from flask import Flask, request, render_template

import time, json, re, os, datetime as dt

app = Flask(__name__)
i = None
issues = []
@app.route('/docs', methods=['GET', 'POST'])
def docs():
    d = dt.datetime.now()
    dateCode= dt.datetime.strftime(d, "%m%d%y")
    if request.method=="POST":
        data = json.loads(request.get_data(as_text=True))
        length = request.content_length
        store = request.args.get("type")
        folder = request.args.get('folder')
        if folder:
            folder+="/"
        elif folder==None:
            folder=''

        if os.path.exists(f"./collections/{store}/{folder}{dateCode}.json"):
            with open(f'./collections/{store}/{folder}{dateCode}.json', 'r', encoding='utf-8') as file:
                past_data = json.loads(file.read())
                data.extend(past_data)
        else:
            os.makedirs(f"./collections/{store}/{folder}", exist_ok=True)
        
        with open(f'./collections/{store}/{folder}{dateCode}.json', 'w', encoding='utf-8') as file:
            file.write(json.dumps(data))
    
        print(f'successfly wrote {length} bytes to disk. have received and archived {len(data)} objects')

        return({"data": {"length": length}, "continue": 1})

@app.route('/i', methods=['GET', 'POST'])
def setPost():
    if request.method=="POST" and request.args.get("i"):
        global i
        i = int(request.args.get('i'))
        return json.dumps({'success': True})
    elif request.method=="POST" and request.args.get('directive'):
        i = 0
        return {"message": "i was reset"}
    elif request.method=="GET":
        if i:
            return json.dumps({"i": i})
        else:
            return json.dumps({'wait': True})

@app.route('/issues', methods=['GET', 'POST'])
def tackleIssue():
    if request.method=="POST":
        global issues
        issues.append(request.get_data(as_text=True))
        return {'set': True}
    else:
        return {'issues': len(issues)}

@app.route('/testing', methods=['GET'])
def returnvars():
    global issues
    return {"issues": issues}


if __name__ == "__main__":
    print("started @ = ", dt.datetime.now())
    app.config['TEMPLATES_AUTO_RELOAD'] = True
    app.run(debug = False)
