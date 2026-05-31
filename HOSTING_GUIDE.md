# How to Host Your Emotion Wellness Web App

Since you built this with Streamlit, hosting it for the world to see is incredibly easy and **100% free**!

## Hosting on Streamlit Community Cloud (Recommended)

Streamlit Community Cloud is the easiest way to host your app. It takes your code directly from GitHub and turns it into a live website.

### Step 1: Upload your code to GitHub
1. Create a free account at [GitHub.com](https://github.com/).
2. Create a new repository (e.g., named `emotion-wellness-app`).
3. Upload these specific files from your project folder to the repository:
   - `app.py`
   - `train_model.py`
   - `model.pkl` (Make sure you generate this first by running `python train_model.py` locally)
   - `music_config.json`
   - `requirements.txt`

### Step 2: Deploy on Streamlit
1. Go to [share.streamlit.io](https://share.streamlit.io/) and log in with your GitHub account.
2. Click **New app**.
3. Select your repository (`emotion-wellness-app`), the branch (`main`), and the main file path (`app.py`).
4. Click **Deploy!**

That's it! In about 2-3 minutes, your app will be live on the internet with a shareable URL. 

### Why is this safe?
Since you are hosting the app yourself, you are in control. The user's input is processed immediately on the Streamlit server and is not saved to any database or sent to third parties.

### How to update your Spotify Links?
Whenever you want to add new songs to a specific mood, you just edit the `music_config.json` file in your GitHub repository. The website will automatically update!
