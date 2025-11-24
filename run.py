from app import app
from flask_session import Session

# Configure session
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_PERMANENT'] = False

# Initialize Session
Session(app)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
