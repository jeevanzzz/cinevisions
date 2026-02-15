from flask import Flask, render_template, request, redirect, session, send_from_directory, flash, url_for, jsonify
import sqlite3, os, random, datetime
from werkzeug.security import generate_password_hash, check_password_hash

import smtplib
from email.message import EmailMessage


app = Flask(__name__)
app.secret_key = "CINEVISIONS_SECRET_KEY"

UPLOAD_FOLDER = "static/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ---------------- DB ----------------
def get_db():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    return conn

def create_notification(message, type):
    try:
        db = get_db()
        db.execute("INSERT INTO notifications (message, type) VALUES (?, ?)", (message, type))
        db.commit()
    except Exception as e:
        print(f"Failed to create notification: {e}")

# ---------------- PUBLIC ----------------
# ---------------- EVENT CONTENT ----------------
def get_featured_content():
    content = []
    
    # Images
    img_dir = "static/images/Featured_Portfolio"
    if os.path.exists(img_dir):
        for f in os.listdir(img_dir):
            if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
                content.append({
                    "path": f"images/Featured_Portfolio/{f}",
                    "media_type": "image",
                    "title": f.rsplit('.', 1)[0].replace('_', ' ').title(),
                    "category": "Featured Shot"
                })

    # Videos
    vid_dir = "static/videos/Featured_Portfolio_videos"
    if os.path.exists(vid_dir):
        for f in os.listdir(vid_dir):
            if f.lower().endswith(('.mp4', '.mov', '.webm')):
                content.append({
                    "path": f"videos/Featured_Portfolio_videos/{f}",
                    "media_type": "video",
                    "title": f.rsplit('.', 1)[0].replace('_', ' ').title(),
                    "category": "Featured Film"
                })
    
    random.shuffle(content)
    return content

@app.route("/")
def home():
    featured_data = get_featured_content()
    return render_template("home.html", data=featured_data)

@app.route("/portfolio")
def portfolio():
    
    db = get_db()
    
    # Categories container
    categories = {
        "wedding": [],
        "pre_wedding": [],
        "model": [],
        "cinematic": [],
        "baby_shoot": [],
        "cultural": [],
        "others": []
    }
    
    # 1. Fetch from Database (Admin Uploads)
    try:
        rows = db.execute("SELECT * FROM portfolio").fetchall()
        for r in rows:
            item = dict(r)
            cat = item.get('category', '').lower().replace(' ', '_').replace('-', '_')
            
            # Map DB categories to our buckets
            target_list = categories.get("others") # Default
            
            if "wedding" in cat and "pre" not in cat: target_list = categories.get("wedding")
            elif "pre" in cat: target_list = categories.get("pre_wedding")
            elif "model" in cat: target_list = categories.get("model")
            elif "cinematic" in cat: target_list = categories.get("cinematic")
            elif "baby" in cat: target_list = categories.get("baby_shoot")
            elif "cultural" in cat: target_list = categories.get("cultural")
            elif "film" in cat: target_list = categories.get("cinematic")

            target_list.append({
                "type": "db",
                "path": f"uploads/{item['filename']}",
                "media_type": "video" if item['filename'].lower().endswith(('.mp4', '.mov', '.webm')) else "image",
                "title": item['title']
            })
    except Exception as e:
        print(f"DB Error: {e}")

    # 2. Fetch from Static Folders (Bulk/Gallery)
    # We will treat 'portfolio_gallery' files as a mix, or try to auto-categorize by filename?
    # For now, let's add them to the marquee/All list, AND distribute them if keywords found.
    
    static_images = []
    
    # Helper to create item dict
    def create_item(filename, path, cat_list=None):
        f = filename.lower()
        item = {
            "type": "static",
            "path": path,
            "media_type": "video" if f.endswith(('.mp4', '.mov', '.webm')) else "image",
            "title": filename.rsplit('.', 1)[0].replace('_', ' ').replace('-', ' ').title()
        }
        static_images.append(item)
        if cat_list is not None:
            cat_list.append(item)
        return item

    # 1. NEW STRUCTURE: static/images/portfolio_gallery (Subfolders)
    base_gal_path = "static/images/portfolio_gallery" # Fixed typo
    if os.path.exists(base_gal_path):
        # Scan specific subfolders
        subfolders = {
            "Baby_shoot_gallery": categories["baby_shoot"],
            "Culturel": categories["cultural"],
            "Model_shoot_gallery": categories["model"],
            "prewedding_gallery": categories["pre_wedding"],
            "Wedding_Gallery": categories["wedding"]
        }
        
        for folder_name, target_list in subfolders.items():
            folder_path = os.path.join(base_gal_path, folder_name)
            if os.path.exists(folder_path):
                for f in os.listdir(folder_path):
                    if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
                        create_item(f, f"images/portfolio_gallery/{folder_name}/{f}", target_list)

    # 2. OLD STRUCTURE COMPATIBILITY (Flat folder)
    # Just in case some files are still there
    flat_gal_path = "static/images/portfolio_gallery"
    if os.path.exists(flat_gal_path):
        for f in os.listdir(flat_gal_path):
             if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
                # Try auto-categorize if not from subfolder
                target = categories["others"]
                if "pre" in f.lower(): target = categories["pre_wedding"]
                elif "wedding" in f.lower(): target = categories["wedding"]
                elif "baby" in f.lower(): target = categories["baby_shoot"]
                elif "model" in f.lower(): target = categories["model"]
                elif "cultur" in f.lower() or "haldi" in f.lower(): target = categories["cultural"]
                
                create_item(f, f"images/portfolio_gallery/{f}", target)

    # 3. Cinematic Videos
    cine_path = "static/videos/cinematic_shoots"
    if os.path.exists(cine_path):
        for f in os.listdir(cine_path):
            if f.lower().endswith(('.mp4', '.mov', '.webm')):
                create_item(f, f"videos/cinematic_shoots/{f}", categories["cinematic"])

    # 4. Old Marquee Folder (images/portfolio) - Just for marquee, no category
    old_port_path = "static/images/portfolio"
    if os.path.exists(old_port_path):
         for f in os.listdir(old_port_path):
            if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
                # Create item object for consistency
                item = {
                    "type": "static",
                    "path": f"images/portfolio/{f}",
                    "media_type": "video" if f.lower().endswith(('.mp4', '.mov', '.webm')) else "image",
                    "title": f.rsplit('.', 1)[0].replace('_', ' ').title()
                }
                static_images.append(item)

    random.shuffle(static_images)

    return render_template("portfolio.html", 
                           marquee_images=static_images, 
                           categories=categories)

@app.route("/services")
def services():
    return render_template("services.html")

@app.route("/about")
def about():
    return render_template("about.html")

# ---------------- CONTACT ----------------
@app.route("/contact", methods=["GET","POST"])
def contact():
    if request.method == "POST":
        phone = request.form["phone"]
        if not phone.isdigit() or len(phone) != 10:
            flash("Please enter a valid 10-digit phone number.", "danger")
            return redirect("/contact")

        db = get_db()
        db.execute("""
            INSERT INTO contact_requests 
            (name, phone, email, event_type, event_date, message)
            VALUES (?,?,?,?,?,?)
        """, (
            request.form["name"],
            request.form["phone"],
            request.form.get("email"),
            request.form["event_type"],
            request.form.get("event_date"),
            request.form.get("message")
        ))
        db.commit()

        # Notification
        create_notification(f"New enquiry from {request.form['name']}", "contact")

        # Prepare and send email to admin
        name = request.form["name"]
        phone = request.form["phone"]
        email = request.form.get("email")
        event_type = request.form["event_type"]
        event_date = request.form.get("event_date")
        message = request.form.get("message")

        subject = "📩 New Contact Enquiry Received"
        body = f"""
New contact enquiry submitted on CineVisions website:

Name: {name}
Phone: {phone}
Email: {email or 'N/A'}
Event Type: {event_type}
Event Date: {event_date or 'N/A'}
Message:
{message or 'No additional details'}
"""
        # Use the same admin email as feedback
        send_email("jeevanbangera94@gmail.com", subject, body)

        flash("Thank you for your enquiry! We will contact you soon.", "success")
        return redirect("/contact")
    return render_template("contact.html")

# ---------------- USER AUTH ----------------
@app.route("/auth", methods=["GET", "POST"])
def auth():
    if request.method == "POST":
        action = request.form.get("action")
        if action == "login":
            email = request.form["email"] # Acts as Username too
            password = request.form["password"]
            
            # Check Admin
            if email == "cinevisions" and password == "admin@1805":
                session["admin"] = True
                session["user_name"] = "CineVisions" # Show in Navbar
                return redirect("/dashboard")

            # Check User
            db = get_db()
            user = db.execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()
            if user and check_password_hash(user["password"], password):
                session["user_id"] = user["id"]
                session["user_name"] = user["name"]
                return redirect("/?login=success")
            return render_template("auth.html", error="Invalid credentials", active_tab="login")
        elif action == "register":
            name = request.form["name"]
            email = request.form["email"]
            password = request.form["password"]
            db = get_db()
            try:
                db.execute("INSERT INTO users (name,email,password) VALUES (?,?,?)", (name, email, generate_password_hash(password)))
                db.commit()
                create_notification(f"New user registered: {name}", "user")
                return redirect("/auth?registered=1")
            except:
                return render_template("auth.html", error="Email already exists", active_tab="register")
    # GET request
    tab = request.args.get("tab", "login")
    return render_template("auth.html", active_tab=tab)


# ---------------- PASSWORD RESET ----------------
def send_email(to_email, subject, body):
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = "cinevisions@gmail.com"
    msg["To"] = to_email
    msg.set_content(body)

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login("jeevanbangera94@gmail.com", "cgqn lnal ffac hjdq")
            smtp.send_message(msg)
        return True
    except Exception as e:
        print(f"Email failed: {e}")
        return False

@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        email = request.form.get("email")
        db = get_db()
        user = db.execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()
        
        if user:
            # Generate OTP
            otp = str(random.randint(100000, 999999))
            expires_at = datetime.datetime.now() + datetime.timedelta(minutes=10)
            
            db.execute("INSERT INTO password_resets (email, otp, expires_at) VALUES (?, ?, ?)", 
                       (email, otp, expires_at))
            db.commit()
            
            # Send Email
            sent = send_email(email, "Password Reset OTP", f"Your OTP for password reset is: {otp}")
            
            if sent:
                session['reset_email'] = email
                flash("OTP sent to your email.", "info")
                return redirect("/verify-otp")
            else:
                flash("Failed to send email. Check logs.", "danger")
        else:
            flash("Email not found.", "danger")
            
    return render_template("forgot_password.html")

@app.route("/verify-otp", methods=["GET", "POST"])
def verify_otp():
    if "reset_email" not in session:
        return redirect("/forgot-password")
        
    if request.method == "POST":
        otp = request.form.get("otp")
        email = session['reset_email']
        
        db = get_db()
        record = db.execute("""
            SELECT * FROM password_resets 
            WHERE email=? AND otp=? AND expires_at > ?
            ORDER BY id DESC LIMIT 1
        """, (email, otp, datetime.datetime.now())).fetchone()
        
        if record:
            session['verified_reset'] = True
            return redirect("/reset-new-password")
        else:
            flash("Invalid or expired OTP", "danger")
            
    return render_template("verify_otp.html")

@app.route("/reset-new-password", methods=["GET", "POST"])
def reset_new_password():
    if "reset_email" not in session or "verified_reset" not in session:
        return redirect("/forgot-password")
        
    if request.method == "POST":
        password = request.form.get("password")
        email = session['reset_email']
        
        db = get_db()
        db.execute("UPDATE users SET password=? WHERE email=?", (generate_password_hash(password), email))
        db.execute("DELETE FROM password_resets WHERE email=?", (email,))
        db.commit()
        
        session.pop('reset_email', None)
        session.pop('verified_reset', None)
        
        return redirect("/auth?login=success&msg=Password+Updated")
        
    return render_template("reset_new_password.html")


@app.route("/auth/login", methods=["GET","POST"])
def user_login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        db = get_db()
        user = db.execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()

        if user and check_password_hash(user["password"], password):
            session["user_id"] = user["id"]
            session["user_name"] = user["name"]
            return redirect("/?login=success")

        return render_template("auth.html", error="Invalid credentials", active_tab="login")

    return render_template("auth.html", active_tab="login")

@app.route("/auth/register", methods=["GET","POST"])
def user_register():
    if request.method == "POST":
        db = get_db()
        try:
            db.execute("""
                INSERT INTO users (name,email,password)
                VALUES (?,?,?)
            """, (
                request.form["name"],
                request.form["email"],
                generate_password_hash(request.form["password"])
            ))
            db.commit()
            create_notification(f"New user registered: {request.form['name']}", "user")
            return redirect("/auth/login?registered=1")
        except:
            return render_template("auth.html", error="Email already exists", active_tab="register")

    return render_template("auth.html", active_tab="register")

@app.route("/logout")
def user_logout():
    session.clear()
    return redirect("/")

# ---------------- ADMIN ----------------
@app.route("/login", methods=["GET","POST"])
def admin_login():
    return redirect("/auth")

@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():
    if "admin" not in session:
        return redirect("/login")
    if request.method == "POST":
        title = request.form.get("title")
        category = request.form.get("category")
        files = request.files.getlist("file")

        if files and title and category:
            db = get_db()
            uploaded = False

            for file in files:
                if file.filename == '':
                    continue

                filename = file.filename
                # Determine media type
                ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
                media_type = "video" if ext in ['mp4', 'mov', 'avi', 'webm', 'mkv'] else "image"

                save_path = os.path.join(UPLOAD_FOLDER, filename)
                file.save(save_path)

                db.execute("INSERT INTO portfolio (title, category, filename, media_type) VALUES (?, ?, ?, ?)", 
                          (title, category, filename, media_type))
                uploaded = True

            if uploaded:
                db.commit()
                return redirect("/dashboard?upload=success")
            else:
                return render_template("dashboard.html", error="No valid files selected.")
        else:
            return render_template("dashboard.html", error="All fields are required.")
    return render_template("dashboard.html")

@app.route("/admin/media")
def admin_media():
    if "admin" not in session:
        return redirect("/login")
    db = get_db()
    media = db.execute("SELECT * FROM portfolio ORDER BY id DESC").fetchall()
    return render_template("admin_media.html", media=media)

@app.route("/users")
def admin_users():
    if "admin" not in session:
        return redirect("/login")
    db = get_db()
    users = db.execute("SELECT id,name,email FROM users ORDER BY id DESC").fetchall()
    return render_template("users.html", users=users)

@app.route("/admin/contacts")
def admin_contacts():
    if "admin" not in session:
        return redirect("/login")
    db = get_db()
    contacts = db.execute("SELECT * FROM contact_requests ORDER BY id DESC").fetchall()
    return render_template("admin_contacts.html", contacts=contacts)

# ---------------- FILE ACTIONS ----------------
@app.route("/download/<int:id>")
def download(id):
    if "admin" not in session:
        return redirect("/login")
    db = get_db()
    media = db.execute("SELECT filename FROM portfolio WHERE id=?", (id,)).fetchone()
    return send_from_directory(UPLOAD_FOLDER, media["filename"], as_attachment=True)

@app.route("/delete/<int:id>")
def delete(id):
    if "admin" not in session:
        return redirect("/login")
    db = get_db()
    media = db.execute("SELECT filename FROM portfolio WHERE id=?", (id,)).fetchone()
    os.remove(os.path.join(UPLOAD_FOLDER, media["filename"]))
    db.execute("DELETE FROM portfolio WHERE id=?", (id,))
    db.commit()
    return redirect("/admin/media")


@app.route("/submit-rating", methods=["POST"])
def submit_rating():
    rating = request.form.get("rating")
    feedback = request.form.get("feedback")

    if not rating:
        flash("Please select a rating", "danger")
        return redirect("/contact")

    # 1️⃣ Save to DB (THIS PART IS FINE)
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO ratings (rating, feedback) VALUES (?, ?)",
        (rating, feedback)
    )
    conn.commit()
    conn.close()

    # Notification
    create_notification(f"New {rating}-star rating received", "rating")

    # 2️⃣ Prepare Email
    msg = EmailMessage()
    msg["Subject"] = "⭐ New Customer Rating Received"
    msg["From"] = "cinevisions@gmail.com"
    msg["To"] = "jeevanbangera94@gmail.com"

    msg.set_content(f"""
New rating submitted on CineVisions website:

Rating: {rating}/5
Feedback:
{feedback or "No feedback provided"}
""")

    # 3️⃣ Try sending email (DO NOT CRASH SITE)
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(
                "jeevanbangera94@gmail.com",
                "cgqn lnal ffac hjdq"
            )
            smtp.send_message(msg)
    except Exception as e:
        print("⚠️ Email failed:", e)

    # 4️⃣ Always redirect cleanly
    flash("Thank you for your feedback ❤️", "success")
    return redirect("/contact")


@app.route("/admin/ratings")
def admin_ratings():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, rating, feedback, created_at
        FROM ratings
        ORDER BY created_at DESC
    """)
    ratings = cursor.fetchall()

    conn.close()
    return render_template("admin_ratings.html", ratings=ratings)



# ---------------- NOTIFICATIONS API ----------------
@app.route("/api/notifications/unread")
def get_unread_notifications():
    if "admin" not in session:
        return jsonify({"error": "Unauthorized"}), 403
    
    db = get_db()
    notifs = db.execute("SELECT * FROM notifications WHERE is_read=0 ORDER BY created_at DESC").fetchall()
    
    return jsonify([dict(n) for n in notifs])

@app.route("/api/notifications/mark-read/<int:id>", methods=["POST"])
def mark_notification_read(id):
    if "admin" not in session:
        return jsonify({"error": "Unauthorized"}), 403
        
    db = get_db()
    db.execute("UPDATE notifications SET is_read=1 WHERE id=?", (id,))
    db.commit()
    return jsonify({"success": True})


# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run(debug=True)
