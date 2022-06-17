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
            try:
                os.mkdir(f"./collections/{store}")
            except:
                print('skipping directory creation')
        with open(f'./collections/{store}/{folder}{dateCode}.json', 'w', encoding='utf-8') as file:
            file.write(json.dumps(data))
        print(f'successfly wrote {length} to disk. have received {i} objects')

        return({"data": {"length": length}, "continue": 1})

if __name__ == "__main__":
    app.config['TEMPLATES_AUTO_RELOAD'] = True
    app.run(debug = False)
