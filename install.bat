echo Installing pip
python ./libraries/get-pip.py
echo Installing apscheduler
pip install apscheduler
echo Installing Tweepy
cd ./libraries/tweepy-master
python setup.py install