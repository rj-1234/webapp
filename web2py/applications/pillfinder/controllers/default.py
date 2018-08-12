# -*- coding: utf-8 -*-
# -------------------------------------------------------------------------
# This is a sample controller
# this file is released under public domain and you can use without limitations
# -------------------------------------------------------------------------

# ---- example index page ----
def index():
    response.flash = T("Hello World")
    return dict(message=T('Welcome to web2py!'))

# ---- API (example) -----
@auth.requires_login()
def api_get_user_email():
    if not request.env.request_method == 'GET': raise HTTP(403)
    return response.json({'status':'success', 'email':auth.user.email})

# ---- Smart Grid (example) -----
@auth.requires_membership('admin') # can only be accessed by members of admin groupd
def grid():
    response.view = 'generic.html' # use a generic view
    tablename = request.args(0)
    if not tablename in db.tables: raise HTTP(403)
    grid = SQLFORM.smartgrid(db[tablename], args=[tablename], deletable=False, editable=False)
    return dict(grid=grid)

# ---- Embedded wiki (example) ----
def wiki():
    auth.wikimenu() # add the wiki to the menu
    return auth.wiki() 

# ---- Action for login/register/etc (required for auth) -----
def user():
    """
    exposes:
    http://..../[app]/default/user/login
    http://..../[app]/default/user/logout
    http://..../[app]/default/user/register
    http://..../[app]/default/user/profile
    http://..../[app]/default/user/retrieve_password
    http://..../[app]/default/user/change_password
    http://..../[app]/default/user/bulk_register
    use @auth.requires_login()
        @auth.requires_membership('group name')
        @auth.requires_permission('read','table name',record_id)
    to decorate functions that need access control
    also notice there is http://..../[app]/appadmin/manage/auth to allow administrator to manage users
    """
    return dict(form=auth())

# ---- action to server uploaded static content (required) ---
@cache.action()
def download():
    """
    allows downloading of uploaded files
    http://..../[app]/default/download/[filename]
    """
    return response.download(request, db)








# do our thing

import boto3
import os
from PIL import Image
import colorgram
import webcolors
import numpy as np
import cv2
import statistics
import pandas as pd

from skimage import filters
os.environ['AWS_DEFAULT_REGION'] = 'us-east-2'

def color(file):
    colors = colorgram.extract(file, 2)
    first_color = colors[1]
    rgb = first_color.rgb
    return (rgb)


def closest_colour(requested_colour):
    min_colours = {}
    for key, name in webcolors.css3_hex_to_names.items():
        r_c, g_c, b_c = webcolors.hex_to_rgb(key)
        rd = (r_c - requested_colour[0]) ** 2
        gd = (g_c - requested_colour[1]) ** 2
        bd = (b_c - requested_colour[2]) ** 2
        min_colours[(rd + gd + bd)] = name
    return min_colours[min(min_colours.keys())]


def get_colour_name(requested_colour):
    try:
        closest_name = actual_name = webcolors.rgb_to_name(requested_colour)
    except ValueError:
        closest_name = closest_colour(requested_colour)
        actual_name = None
    return actual_name, closest_name


def final_response(image):
    # Getting text
    data = {}
    s3 = boto3.client('s3')
    # s3.create_bucket(Bucket='my-bucket')
    bucket = 'avadakadaba'
    photo = image
    s3.upload_file(photo, bucket, photo)
    client = boto3.client('rekognition')
    response = client.detect_text(Image={'S3Object': {'Bucket': 'avadakadaba', 'Name': photo}})
    textDetections = response['TextDetections']
    text2 = ""
    for text in textDetections:
        if text['DetectedText'] not in text2:
            text2 = text2 + text['DetectedText']
    # print("text is: " + text2)
    text2.replace("1","|").replace("I","|")

    # Getting color
    requested_colour = color(photo)
    actual_name, closest_name = get_colour_name(requested_colour)
    if "grey" in closest_name:
        closest_name = "white"
    if "rose" in closest_name:
        closest_name = "pink"
    if "red" in closest_name:
        closest_name = "red"
    if "yellow" in closest_name:
        closest_name = "yellow"
    # print("closest colour name:", closest_name)

    # Getting shape
    shape=""
    img = cv2.imread(photo)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray = cv2.Canny(np.asarray(gray), 50, 250)

    _,contours, h = cv2.findContours(gray, 1, 2)

    avgArray = []
    for cnt in contours:
        approx = cv2.approxPolyDP(cnt, 0.01 * cv2.arcLength(cnt, True), True)
        avgArray.append(len(approx))

    # print((avgArray))
    edges = statistics.median(avgArray)
    # print(edges)

    if edges < 15:
        # print("cylinder")
        shape = "cylinder"
        # cv2.drawContours(photo, [cnt], 0, 255, -1)
    # elif edges == 3:
    #     print("triangle")
    #     cv2.drawContours(img, [cnt], 0, (0, 255, 0), -1)
    # elif edges == 4:
    #     print("square")
    #     cv2.drawContours(img, [cnt], 0, (0, 0, 255), -1)
    # elif edges == 9:
    #     print("half-circle")
    #     cv2.drawContours(img, [cnt], 0, (255, 255, 0), -1)
    elif edges > 15:
        # print("circle")
        shape = "circle"
        # cv2.drawContours(photo, [cnt], 0, (0, 255, 255), -1)
    # cv2.imshow('img', gray)
    # cv2.waitKey(0)
    # cv2.destroyAllWindows()
    data = {"uploadName":photo,"text":text2,"color":closest_name,"shape":shape}
    return data
    # print(data)


def process_pill():
    image = ""
    response = final_response(image)


def detected_pill():
