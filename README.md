# tartanhacks21
TartanHacks21

for running authentication:
in command line:
`pip install spotipy`\
`pip install flask`\
`export FLASK_APP=app_host.py`\
`flask run`\
open it on http://127.0.0.1:5000/

for clour stuff:
Need to install cloud stuff beforehand\
`pip3 install google-cloud-storage google-cloud-language`

Need to export some gcloud variables so\
`source .gcloud_setup`

Note: gcloud pricing is tied to Winston's credit card so don't go crazy on the sentiment testing lol.\
It won't actually charge me until we hit like 5k requests, and even then it's only like $1 per 1k requests.\
But just something to keep in mind.

For spotify-test.py, need to export some spotify credentials first, so run \
`source setup_spotify_environment.sh`
