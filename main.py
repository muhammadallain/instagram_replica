
from datetime import datetime, timedelta
from multiprocessing.sharedctypes import Value
import google.oauth2.id_token
import random, local_constants
from google.cloud import datastore, storage
from flask import Flask, render_template, request, redirect, url_for
from google.auth.transport import requests

app = Flask(__name__)
datastore_client = datastore.Client()
firebase_request_adapter = requests.Request()

def createUserInfo(claims, username, firstname, lastname):
    entity_key = datastore_client.key('UserInfo', claims['email'])
    entity = datastore.Entity(key=entity_key)
    entity.update({
        'email': claims['email'],
        'username': username,
        'profile_name': firstname + ' ' + lastname,
        'followers': [],
        'following': [],
        'post_list': []
    })
    datastore_client.put(entity)

def follow(current_user, target_user):
    following_keys = current_user['following']
    following_keys.append(target_user['email'])
    current_user.update({
        'following': following_keys
    })
    datastore_client.put(current_user)
    followed_keys = target_user['followers']
    followed_keys.append(current_user['email'])
    target_user.update({
        'followers': followed_keys
    })
    datastore_client.put(target_user)
    

def unfollow(current_user, target_user):
    following_keys = current_user['following']
    following_keys.remove(target_user['email'])
    current_user.update({
        'following': following_keys
    })
    datastore_client.put(current_user)
    followed_keys = target_user['followers']
    followed_keys.remove(current_user['email'])
    target_user.update({
        'followers': followed_keys
    })
    datastore_client.put(target_user)
    
    
def retrieve_entity(kind, id):
    entity_key = datastore_client.key(kind, id)
    entity = datastore_client.get(entity_key)
    return entity

def createPostInfo(image, caption, user_info):
    id = random.getrandbits(63)
    if image.filename.lower().split('.')[1] in ['jpg', 'jpeg', 'png']:
        storage_client = storage.Client(project=local_constants.PROJECT_NAME)
        bucket = storage_client.bucket(local_constants.PROJECT_STORAGE_BUCKET)
        blob = bucket.blob(image.filename)
        blob.upload_from_string( image.read(), content_type= "image/jpeg")
        blob.make_public()
        image_link = blob.public_url
        entity_key = datastore_client.key('PostInfo', id)
        entity = datastore.Entity(key = entity_key)
        entity.update({
            'image_link': image_link,
            'caption': caption,
            'posted_by': user_info['email'],
            'post_time': datetime.now(),
            'comments': []
        })
        datastore_client.put(entity)
        post_keys = user_info['post_list']
        post_keys.append(id)
        user_info.update({
            'post_list': post_keys
        })
        datastore_client.put(user_info)
    else:
        pass

def createCommentInfo(comment, user_info, post_id):
    id = random.getrandbits(63)
    entity_key = datastore_client.key('CommentInfo', id)
    entity = datastore.Entity(key = entity_key)
    entity.update({
        'comment': comment,
        'post_id': post_id,
        'posted_by': user_info['username'],
        'user_id': user_info['email'],
        'post_time': datetime.now()
    })
    datastore_client.put(entity)
    post = retrieve_entity('PostInfo', post_id)
    comment_dic = post['comments']
    comment_dic.append(entity)
    post.update({
        'comments': comment_dic
    })
    datastore_client.put(post)
    
def get_multiple_entities(user, list_type, kind):
    ids = user[list_type]
    keys = []
    for i in range(len(ids)):
        keys.append(datastore_client.key(kind, ids[i]))
    entities = datastore_client.get_multi(keys)
    return entities

def search_user(keyword):
    results = list(datastore_client.query(kind= "UserInfo").fetch())
    users = [user for user in results if keyword.lower() in user['profile_name'].lower()]
    return users

def get_feed(user):
    feed = [post for person in get_multiple_entities(user=user, list_type='following', kind='UserInfo') for post in get_multiple_entities(user=person, list_type='post_list', kind='PostInfo')]
    posts = get_multiple_entities(user=user, list_type='post_list', kind='PostInfo')
    for post in posts:
        feed.append(post)
    feed.sort(key=lambda x: x['post_time'], reverse=True)
    return feed[0:50]


@app.route('/unfollow/<tuid>')
def unfollow_user(tuid):
    id_token = request.cookies.get("token")
    error_message = None
    claims = None
    current_user = None
    target_user = None
    if id_token:
        try:
            claims = google.oauth2.id_token.verify_firebase_token(
                id_token, firebase_request_adapter)
            current_user = retrieve_entity('UserInfo', claims['email'])
            entity_key = datastore_client.key('UserInfo', tuid)
            target_user = datastore_client.get(entity_key)
            unfollow(current_user, target_user)
        except ValueError as exc:
            error_message = str(exc)
    return redirect(url_for('user_profile', id=tuid))
    
@app.route('/follow/<tuid>')
def follow_user(tuid):
    id_token = request.cookies.get("token")
    error_message = None
    claims = None
    current_user = None
    target_user = None
    if id_token:
        try:
            claims = google.oauth2.id_token.verify_firebase_token(
                id_token, firebase_request_adapter)
            current_user = retrieve_entity('UserInfo', claims['email'])
            entity_key = datastore_client.key('UserInfo', tuid)
            target_user = datastore_client.get(entity_key)
            follow(current_user, target_user)
        except ValueError as exc:
            error_message = str(exc)
    return redirect(url_for('user_profile', id=tuid))
    
@app.route('/user/<id>', methods=['GET', 'POST'])
def user_profile(id):
    id_token = request.cookies.get("token")
    error_message = None
    claims = None
    user_info = None
    entities = None
    profile = None
    follower_count = None
    following_count = None
    list_type = None
    prompt = None
    if request.method == 'GET':
        if id_token:
            try:
                claims = google.oauth2.id_token.verify_firebase_token(
                    id_token, firebase_request_adapter)
                user_info = retrieve_entity('UserInfo', claims['email'])
                profile = retrieve_entity('UserInfo', id)
                follower_count = len(profile['followers'])
                following_count = len(profile['following'])
                entities = get_multiple_entities(profile, 'post_list', 'PostInfo')
                entities.sort(key=lambda x: x['post_time'], reverse=True)
                for entity in entities:
                    entity['comments'].sort(key=lambda x: x['post_time'], reverse=True)
                if len(entities) == 0:
                    prompt = 'No Posts Found for User'
            except ValueError as exc:
                error_message = str(exc)
        return render_template('user.html', prompt=prompt, following_count=following_count, follower_count=follower_count, profile=profile, entities=entities, user_data=claims, error_message=error_message, user_info=user_info)
    else:
        if id_token:
            try:
                claims = google.oauth2.id_token.verify_firebase_token(
                    id_token, firebase_request_adapter)
                user_info = retrieve_entity('UserInfo', claims['email'])
                profile = retrieve_entity('UserInfo', id)
                follower_count = len(profile['followers'])
                following_count = len(profile['following'])
                if request.form['list_type'] == 'followers':
                    list_type = request.form['list_type']
                elif request.form['list_type'] == 'following':
                    list_type = request.form['list_type']
                entities = get_multiple_entities(profile, request.form['list_type'], 'UserInfo')
                for entity in entities:
                    entity[request.form['list_type']].sort(key=lambda x: x['post_time'], reverse=True)
                #entities.sort(key=lambda x: x['post_time'], reverse=True)
                if len(entities) == 0:
                    prompt = 'No Users Found in "' + request.form['list_type'] + '"'
            except ValueError as exc:
                error_message = str(exc)
        return render_template('user.html',prompt=prompt,list_type=list_type, following_count=following_count, follower_count=follower_count, profile=profile, entities=entities, user_data=claims, error_message=error_message, user_info=user_info)

@app.route('/generate_new_user', methods=['GET', 'POST'])
def generate_new_user():
    id_token = request.cookies.get("token")
    error_message = None
    claims = None
    if id_token:
        try:
            claims = google.oauth2.id_token.verify_firebase_token(
                id_token, firebase_request_adapter)
            if request.method == 'POST':
                createUserInfo(claims, request.form['username'], request.form['firstname'], request.form['lastname'])
                return redirect(url_for('root'))
            else:
                pass
        except ValueError as exc:
            error_message = str(exc)
    return render_template('homepage.html', user_data=claims, error_message=error_message)

@app.route('/', methods=['GET', 'POST'])
def root():
    id_token = request.cookies.get("token")
    error_message = None
    claims = None
    user_info = None
    users = None
    prompt = None
    feed = None
    if request.method == 'GET':
        if id_token:
            try:
                claims = google.oauth2.id_token.verify_firebase_token(
                    id_token, firebase_request_adapter)
                user_info = retrieve_entity('UserInfo', claims['email'])
                if user_info == None:
                    return redirect(url_for('generate_new_user'))
                feed = get_feed(user_info)
                for entity in feed:
                    entity['comments'].sort(key=lambda x: x['post_time'], reverse=True)
                if len(feed) == 0:
                    prompt = 'No Posts Found for User'
            except ValueError as exc:
                error_message = str(exc)
        return render_template('homepage.html', user_data=claims, error_message=error_message, user_info=user_info, feed=feed, prompt=prompt)
    else:
        if id_token:
            try:
                claims = google.oauth2.id_token.verify_firebase_token(
                    id_token, firebase_request_adapter)
                user_info = retrieve_entity('UserInfo', claims['email'])
                if request.form['submit'] == 'Upload':
                    createPostInfo(request.files['picture'], request.form['caption'], user_info)
                elif request.form['submit'] == 'Search':
                    users = search_user(request.form['keyword'])
                    if len(users) == 0:
                        prompt = 'No Users Found for "' + request.form['keyword'] + '"'
                    return render_template('homepage.html', prompt=prompt, users=users, user_data=claims, error_message=error_message, user_info=user_info)
                elif request.form['submit'] == 'Add Comment':
                    createCommentInfo(request.form['comment'], user_info, int(request.form['post_id']))
            except ValueError as exc:
                error_message = str(exc)
        return redirect(url_for('root'))


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)
