#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import datetime
import os
import sys
import traceback
import itertools
from more_itertools import chunked

from flask import Flask, flash, request, redirect, url_for
import magic
from tweepy import *
from werkzeug.utils import secure_filename
import subprocess
import slack


#Authorization
f = open(os.path.join(os.path.dirname(__file__), 'config2.txt'))
data = f.read()
f.close()
lines = data.split('\n')

def get_oauth():
    consumer_key = lines[0]
    consumer_secret = lines[1]
    access_key = lines[2]
    access_secret = lines[3]
    auth = OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_key, access_secret)
    return auth

auth = get_oauth()
api = API(auth)

ALLOWED_MIMETYPE = set(['image/jpeg', 'image/gif', 'image/png', 'image/webp'])

app = Flask(__name__, static_folder='images')
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(__file__), 'images/')
#app.config['MAX_CONTENT_LENGTH'] = 10240 *  1024 

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            return '''
            <!doctype html>
            <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <title>エラー</title>
            <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bulma@0.8.0/css/bulma.min.css">
            <title>ファイルを選択してください</title>
            </head>
            <body>
            <p>ファイルを選択してください</p>
            </body>
            </html>
            '''
        file = request.files['file']
        comment = request.form['comment']
        # if user does not select file, browser also
        # submit an empty part without filename
        if file.filename == '':
            return '''
            <!doctype html>
            <html>
            <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <title>エラー</title>
            <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bulma@0.8.0/css/bulma.min.css">
            <title>ファイルを選択してください</title>
            </head>
            <body>
            <p>ファイルを選択してください</p>
            </body>
            </html>
            '''
        if file:
            filename = secure_filename(file.filename)
            _, ext = os.path.splitext(file.filename)
            current_time = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
            filename = os.path.join(app.config['UPLOAD_FOLDER'], current_time+ext)
            file.save(filename)
            mimetype = magic.from_file(filename, mime=True)
            if mimetype not in ALLOWED_MIMETYPE:
                return '''
                <!doctype html>
                <html>
                <head>
                <meta charset="utf-8">
                <meta name="viewport" content="width=device-width, initial-scale=1">
                <title>エラー</title>
                <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bulma@0.8.0/css/bulma.min.css">
                </head>
                <body>
                <p>エラーが起こりました。JPEG, GIF, PNG, WebP以外の画像をアップロードしていませんか？</p>
                </body>
                </html>
                '''
            if ext == '':
                ext = '.' + mimetype.split('/')[1]
                os.rename(filename, filename+ext)
                filename = filename + ext
            try:
                if os.path.getsize(filename) > 700*1000 or mimetype == 'image/webp':
                    subprocess.call('convert {} -thumbnail 400x400^ -gravity center -extent 400x400 -define jpeg:extent=700kb /tmp/output.jpg'.format(filename), shell=True)
                    api.update_profile_image('/tmp/output.jpg')
                else:
                    api.update_profile_image(filename)
                client = slack.WebClient(token=os.environ['SLACK_TOKEN'])

                response = client.files_upload(
                    channels='#icon_history',
                    initial_comment=comment,
                    title=os.path.basename(filename),
                    file=filename)
            except:
                traceback.print_exc()
                return '''
                <!doctype html>
                <html>
                <head>
                <meta charset="utf-8">
                <meta name="viewport" content="width=device-width, initial-scale=1">
                <title>エラー</title>
                <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bulma@0.8.0/css/bulma.min.css">
                </head>
                <body>
                <p>原因不明のエラーが起こりました。時間をおいてまた実行してください</p>
                </body>
                </html>
                '''
            return '''
            <!doctype html>
            <html>
            <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <title>アップロードされました</title>
            <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bulma@0.8.0/css/bulma.min.css">
            <meta charset="utf-8"/>
            </head>
            <body>
            <section class="section">
            <div class="container">
            <div class="content">
            <p>アイコンは正常に変更されました。</p>
            </div>
            </div>
            </section>
            </body>
            </html>
            '''
    image_list = sorted(os.listdir("images"), reverse=True)
    string = """
<!doctype html>
<html>
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>kivantium icon changer</title>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bulma@0.8.0/css/bulma.min.css">
    <script defer src="https://use.fontawesome.com/releases/v5.3.1/js/all.js"></script>
    <style>
    img { object-fit: cover; } 
    </style>
  </head>
  <body>
    <section class="section">
      <div class="container">
        <h1 class="title">kivantium icon changer</h1>
        <div class="content">
          <p>画像ファイルをアップロードしてください (JPEG, PNG, GIF, WebP)</p>
          <ul>
            <li>現行システムに移行してからのアイコン履歴を表示するようにしました。 (2020/04/16)</li>
            <li>スマートフォン向けにデザインを変更しました。 (2020/03/02)</li>
            <li>コメント機能がつきました。(2020/03/02)</li>
            <li>ファイルサイズの上限が10MBになりました（自動で400x400にトリミングされます） (2019/03/04)</li>
          </ul>
          <form method="post" enctype="multipart/form-data" accept="image/*">
            <div class="field">
              <div id="file-js" class="file has-name is-fullwidth">
                <label class="file-label">
                  <input class="file-input" type="file" name="file">
                  <span class="file-cta">
                    <span class="file-icon">
                      <i class="fas fa-upload"></i>
                    </span>
                    <span class="file-label">
                      ファイルを選択
                    </span>
                  </span>
                  <span class="file-name">
                    選択されていません
                  </span>
                </label>
              </div>
            </div>
            <div class="field">
              <div class="control"><input type="text" class="input" name="comment" placeholder="コメント（任意）"></div>
            </div>
            <div class="field">
              <input class="button is-link" type="submit" value="Upload">
            </div>
          </form>
        </div>
      </div>
    </section>
<section class="section">
<div class="container">
<h2 class="title">icon history</h2>
<div class="columns is-mobile is-multiline is-gapless">"""
    for filename in image_list[:24]:
        string += """
    <div class="column is-2-mobile is-2-tablet is-1-desktop">
    <figure class="image is-square">
    <img class="is-rounded" src="/icon/images/{}" style="padding:3%">
    </figure>
    </div>
    """.format(filename)
    string += '''
</div>
<p class="subtitle"><a href="history">もっと見る</a></p>
</div>
</section>
<script>
const fileInput = document.querySelector('#file-js input[type=file]');
fileInput.onchange = () => {
  if (fileInput.files.length > 0) {
    const fileName = document.querySelector('#file-js .file-name');
    fileName.textContent = fileInput.files[0].name;
  }
}
</script>
</body>
</html>'''
    return string

@app.route('/history', methods=['GET'])
def show_history():
    image_list = sorted(os.listdir("images"), reverse=True)
    string = """
<!doctype html>
<html>
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>kivantium icon changer</title>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bulma@0.8.0/css/bulma.min.css">
    <script defer src="https://use.fontawesome.com/releases/v5.3.1/js/all.js"></script>
    <style>
    img { object-fit: cover; } 
    </style>
  </head>
  <body>
<section class="section">
<div class="container">
<h2 class="title">icon history</h2>
<div class="columns is-mobile is-multiline is-gapless">"""
    for filename in image_list:
        string += """
    <div class="column is-2-mobile is-2-tablet is-1-desktop">
    <figure class="image is-square">
    <img class="is-rounded" src="/icon/images/{}" style="padding:3%">
    </figure>
    </div>
    """.format(filename)

    string += '''
</div>
</div>
</section>
<script>
const fileInput = document.querySelector('#file-js input[type=file]');
fileInput.onchange = () => {
  if (fileInput.files.length > 0) {
    const fileName = document.querySelector('#file-js .file-name');
    fileName.textContent = fileInput.files[0].name;
  }
}
</script>
</body>
</html>'''
    return string

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=12345)
