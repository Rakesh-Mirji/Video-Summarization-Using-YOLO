from re import DEBUG, sub
from flask import Flask, render_template, request, redirect, send_file, url_for
from werkzeug.utils import secure_filename, send_from_directory
import os
import subprocess

app= Flask(__name__)

@app.route('/', methods=['POST','GET'])
def index():
    if request.method == 'POST':
        name = request.form['url']
        subprocess.run(['python','summerize.py','-f',f'{name}', '--tiny_yolo'])
        return redirect(url_for('.display',name=name[:-4]))
    return render_template('index.html')

@app.route('/display/<name>')
def display(name):
    output=name+'_output.mp4'
    print(f'\n\n{output}\n\n')
    return render_template('display.html',name=output)

@app.route('/download/<path>')
def download_file(path):
    print(f'\n\n{path}\n\n')
    return send_file(path, as_attachment=True)

@app.route('/about/')
def about():
    return render_template('about.html')

@app.route('/know/')
def know():
    return render_template('know.html')


app.run(debug=True)
