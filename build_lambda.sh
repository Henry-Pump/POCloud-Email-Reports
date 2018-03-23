!#/bin/bash
env/bin/pip install boto3 tzlocal meshify requests
rm -f lambda.zip
mkdir -p deploy
cp env/lib/python3.6/site-packages/* deploy
cp meshify.py deploy
cp reports_s3_xlsx.py deploy

cd deploy
zip -r ../lambda.zip ./*
cd ..
