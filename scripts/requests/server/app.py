from sre_constants import SUCCESS
from flask import Flask, request, render_template

import time


app = Flask(__name__)

@app.route('/docs')
def docs():
    i = int(time.perf_counter())
    data = request.get_data(as_text=True)
    length = request.content_length
    with open(f'./digital{i}.txt', 'w', encoding='utf-8') as file:
        file.write(data)
    print('successfly wrote')
    print('the requested data wanted in a file format was', length)
    
    return({"data": {"length": length}})


if __name__ == "__main__":
    app.config['TEMPLATES_AUTO_RELOAD'] = True
    app.run(debug = True)
