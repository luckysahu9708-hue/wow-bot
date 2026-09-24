from flask import Flask
app = Flask(__name__)
@app.route("/")
def home():
    return "<h1 style='background:black;color:white;text-align:center;padding-top:200px;font-family:Arial'>🔴 This Website is Inactive<br><p style='color:gray;font-size:16px'>by Lucky</p></h1>"
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=10000)
