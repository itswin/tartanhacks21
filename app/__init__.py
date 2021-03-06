from flask import Flask
import os

app = Flask(__name__)

from app import run_app