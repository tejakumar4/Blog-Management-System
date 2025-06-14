from flask import Flask, render_template, request, session, redirect, flash
from werkzeug.utils import secure_filename
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json, os, math
from flask_mail import Mail

#load the config the file for changable parametes
with open("config.json",'r') as c:
	params = json.load(c)["params"]

app = Flask(__name__)

app.secret_key ="super-secret-key"
app.config['UPLOAD_FOLDER'] = params['upload_location']

#email configuration to send updates
app.config.update(
	MAIL_SERVER = 'smtp.gmail.com',
	MAIL_PORT = '465',
	MAIL_USE_SSL = True,
	MAIL_USERNAME = params['gmail_user'],
	MAIL_PASSWORD = params['gmail_password']
)
mail = Mail(app)

local_server = params["local_server"]

if local_server == "True":
	app.config["SQLALCHEMY_DATABASE_URI"] = params['local_uri']
else:
	app.config["SQLALCHEMY_DATABASE_URI"] = params['prod_uri']

db = SQLAlchemy(app)


class Contact(db.Model):
    """
    Setup sql table "Contact" to store contact details
    """
    sno = db.Column(db.Integer, primary_key=True, nullable=False)
    name = db.Column(db.String(150), nullable=False)           # Increased from 80 to 150
    email = db.Column(db.String(150), nullable=False)          # Increased from 80 to 150
    phone_num = db.Column(db.String(100), unique=False, nullable=True)  # Increased from 12 to 100
    mes = db.Column(db.String(150), nullable=False)            # Increased from 120 to 150
    date = db.Column(db.String(100), nullable=False)           # Increased from 12 to 100

class Posts(db.Model):
    """
    Setup sql table "Posts" to store blogs to be displayed on website
    """
    sno = db.Column(db.Integer, primary_key=True, nullable=False)
    title = db.Column(db.String(150), nullable=False)          # Increased from 100 to 150
    sub_heading = db.Column(db.String(100), nullable=True)     # Increased from 50 to 100
    content = db.Column(db.String(150), nullable=False)        # Increased from 80 to 150
    slug = db.Column(db.String(100), unique=True, nullable=False)  # Increased from 12 to 100
    img_file = db.Column(db.String(150), nullable=True)        # Increased from 120 to 150
    date = db.Column(db.String(100), nullable=False)           # Increased from 12 to 100

class Comment(db.Model):
    """
    Setup SQL table 'Comment' to store post comments
    """
    sno = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, nullable=False)  # FK to Posts.sno
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    comment = db.Column(db.String(500), nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)

class Like(db.Model):
    """
    Setup SQL table 'Like' to store likes for each post
    """
    sno = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, nullable=False)  # FK to Posts.sno
    ip_address = db.Column(db.String(100), nullable=False)  # To restrict multiple likes from same user



@app.route("/") #Homepage
def home():
	posts = Posts.query.filter_by().all()
	last = math.ceil(len(posts)/int(params['no_of_posts']))

	#pagination logic
	page = request.args.get('page')
	if not str(page).isnumeric():
		page = 1
	
	page = int(page)
	posts = posts[(page-1)*int(params['no_of_posts']): (page-1)*int(params['no_of_posts'])+int(params['no_of_posts'])]

	if page==1: #First Page
		prev = "#"
		nexxt = "/?page=" + str(page+1)
	elif page==last: #Last Page
		prev="/?page=" + str(page-1)
		nexxt = "#"
	else:  #Middle Page
		prev="/?page=" + str(page-1)
		nexxt = "/?page=" + str(page+1)

	return render_template("index.html",params=params,posts=posts,prev=prev, nexxt=nexxt, page=page, last=last)



@app.route("/dashboard", methods=['GET','POST'])
def dashboard():
	if ('user' in session and session['user'] == params['admin_user']):
		posts= Posts.query.all()
		return render_template('dashboard.html', params=params, posts=posts)

	if request.method=="POST":
		username = request.form.get('username')
		password = request.form.get('pass')

		if (username == params['admin_user'] and password == params['admin_password']):
			session['user'] = username
			posts= Posts.query.all()
			return render_template('dashboard.html', params=params, posts = posts)

	
	return render_template("login.html",params=params)

@app.route("/about")
def about():
	
	return render_template("about.html",params=params)

@app.route("/contact", methods=["GET","POST"])
def contact():
	if(request.method == "POST"):
		name = request.form.get("name")
		email = request.form.get("email")
		phone = request.form.get("phone")
		message = request.form.get("message")
		
		entry = Contact(name=name,email=email,phone_num=phone,mes=message,date=datetime.now())
		db.session.add(entry)
		db.session.commit()
		mail.send_message(f"New Message from {name} via {params['blog_heading']}",
						sender=email,
						recipients=[params['gmail_user']],
						body= message + "\n" + phone + "\n"+ email
					)
		flash("Thank you for writing to us, we'll get back to you at the earliest!", "success")
	return render_template("contact.html",params=params)

@app.route("/edit/<string:sno>", methods=['GET','POST'])
def edit(sno):
	if ('user' in session and session['user']==params['admin_user']):
		if request.method=='POST':
				
			title = request.form.get('title')
			sub_heading = request.form.get('sub_heading')
			content =request.form.get('content')
			slug = request.form.get('slug')
			img_file = request.form.get('img_file')
			date = datetime.now()
			
			if sno=='0':
				post = Posts(title=title, sub_heading=sub_heading, content=content, slug=slug, img_file=img_file, date=date)
				db.session.add(post)
				db.session.commit()
				flash("New post added successfully!!","success")
			
			else:
				post = Posts.query.filter_by(sno=sno).first()
				post.title = title
				post.sub_heading = sub_heading
				post.content= content 
				post.slug=slug
				post.img_file =img_file
				post.date =date
				db.session.commit()
				flash("Post edited successfully!!","success")
				return redirect('/edit/'+sno)

		post = Posts.query.filter_by(sno=sno).first()
		
		return render_template('edit.html', params=params, post=post,sno=sno)


@app.route('/uploader',methods=['GET','POST'])
def upload():
	if('user' in session and session['user']==params['admin_user']):
		if request.method=='POST':
			f = request.files['file1']
			f.save(os.path.join(app.config['UPLOAD_FOLDER'],secure_filename(f.filename)))
			
			return "Uploaded Successfully"

@app.route('/logout')
def logout():
	session.pop('user')
	return redirect('/dashboard')

@app.route('/delete/<string:sno>')
def delete(sno):
	if('user' in session and session['user']== params['admin_user']):
		
		post = Posts.query.filter_by(sno=sno).first()
		db.session.delete(post)
		db.session.commit()
		flash("Post deleted successfully!!","success")
	return redirect("/dashboard")

import requests  # Make sure this import is at the top of your file

@app.route('/chat', methods=['GET', 'POST'])
def chat():
    output = ""
    if request.method == 'POST':
        user_prompt = request.form.get('prompt')

        url = "https://open-ai21.p.rapidapi.com/conversationllama"

        payload = {
            "messages": [
                {
                    "role": "user",
                    "content": user_prompt  # Taking user input from the form
                }
            ],
            "web_access": False
        }

        headers = {
            "x-rapidapi-key": "9ee15000ecmsh71ea537720ddd2ap14d74bjsn31a802e28a7e",
            "x-rapidapi-host": "open-ai21.p.rapidapi.com",
            "Content-Type": "application/json"
        }

        try:
            response = requests.post(url, json=payload, headers=headers)
            api_response = response.json()
            # Debug print to terminal
            print(api_response)

            # Extracting the content of the AI's response
            output = api_response.get('result', 'No result key in response.')
        except Exception as e:
            output = f"Error: {str(e)}"

    return render_template('chat.html', params=params, output=output)


@app.route("/post/<string:post_slug>", methods=["GET", "POST"])
def post_query(post_slug):
    post = Posts.query.filter_by(slug=post_slug).first()
    comments = Comment.query.filter_by(post_id=post.sno).all()
    like_count = Like.query.filter_by(post_id=post.sno).count()

    if request.method == 'POST':
        if 'comment' in request.form:
            name = request.form.get('name')
            email = request.form.get('email')
            comment_text = request.form.get('comment')
            comment = Comment(post_id=post.sno, name=name, email=email, comment=comment_text)
            db.session.add(comment)
            db.session.commit()
            flash("Comment added successfully!", "success")
            return redirect(f"/post/{post_slug}")
        
        elif 'like' in request.form:
            ip = request.remote_addr
            existing_like = Like.query.filter_by(post_id=post.sno, ip_address=ip).first()
            if not existing_like:
                like = Like(post_id=post.sno, ip_address=ip)
                db.session.add(like)
                db.session.commit()
                flash("You liked this post!", "success")
            else:
                flash("You've already liked this post.", "warning")
            return redirect(f"/post/{post_slug}")

    return render_template("post.html", params=params, post=post, comments=comments, like_count=like_count)

@app.route("/admin-stats")
def admin_stats():
    if 'user' in session and session['user'] == params['admin_user']:
        total_posts = Posts.query.count()
        total_comments = Comment.query.count()
        total_likes = Like.query.count()
        total_users = Contact.query.count()  # Or change if you have a dedicated Users table

        return render_template('admin_stats.html', params=params,
                               total_posts=total_posts,
                               total_comments=total_comments,
                               total_likes=total_likes,
                               total_users=total_users)
    else:
        flash("Admin access required!", "danger")
        return redirect('/dashboard')  # or your login page


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        print("Database created successfully!")
    app.run(debug=False)




