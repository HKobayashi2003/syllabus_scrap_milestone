# Pythonのベースイメージを使用
FROM python:latest
USER root

# 作業ディレクトリを設定
WORKDIR /work

# pythonlibraryのリストをホストから取得
COPY ./requirements.txt /requirements.txt   
# requirements.txt内のライブラリーを一括インストール 
RUN pip install -r /requirements.txt

# 以下、Selenium WebDriverを動かすための設定が必要です
# 例えば、Chrome WebDriverのインストールと設定
#RUN apt-get update
#RUN apt-get install -y wget xvfb
#RUN wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
#RUN apt install -y ./google-chrome-stable_current_amd64.deb
#RUN wget https://chromedriver.storage.googleapis.com/2.41/chromedriver_linux64.zip
#RUN unzip chromedriver_linux64.zip -d /usr/local/bin/

CMD ["/bin/bash"]