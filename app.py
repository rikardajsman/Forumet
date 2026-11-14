
from flask import Flask, request, render_template_string

app = Flask(__name__)

posts = []

@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        message = request.form.get("message", "").strip()
        if message:
            posts.append(message[:500])
    return render_template_string("""
<h1>AlphaStack</h1>
<h2>Welcome to the community for programmers!</h2>
<h3>Post something!</h3>
<form method="POST">
    <textarea name="message" placeholder="Discuss..." required></textarea>
    <button type="submit">Post</button>
</form>
<h3>Latest Discussions</h3>
{% for post in posts %}
    <p>{{ post }}</p>
{% endfor %}
""", posts=posts)

if __name__ == "__main__":
    app.run(debug=True)
