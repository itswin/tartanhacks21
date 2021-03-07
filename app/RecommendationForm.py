from flask import Flask, render_template, redirect, url_for
from flask_bootstrap import Bootstrap
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectField, RadioField
from wtforms.validators import DataRequired

class RecommendationForm(FlaskForm):
    acoustic = RadioField('Acoustic Level:', choices = [(1,1)])
    genre = SelectField('Genre To Base Off Of', choices = [(1,"Pop"), 
                                                            (2,"Hip Hop/Rap"),
                                                            (3,"Rock"),
                                                            (4,"Dance/EDM"),
                                                            (5,"Latin"),
                                                            (6,"Indie/Alternative"),
                                                            (7,"Classical"),
                                                            (8,"K-Pop"),
                                                            (9,"Country"),
                                                            (10,"Metal")])
    submit = SubmitField('Submit')