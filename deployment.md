# 🚀 How to Put Your Website Online (A Simple Guide)

Follow these steps to move your code from your computer to the whole world!

## Step 1: Get Your "Passwords" Ready
1.  Find the file named `.env.example`.
2.  Make a copy of it and name the new copy exactly `.env`.
3.  Open `.env` and fill in all the blank spots with your special keys and passwords.
    *   *Think of this like your secret treasure map.*

## Step 2: Save Your Work on GitHub
Every time you finish making something cool, save it to GitHub:
1.  Open your "Terminal" (the black box where you type code).
2.  Type this and press Enter:
    ```bash
    git add .
    ```
3.  Then type this (you can change the message in the quotes):
    ```bash
    git commit -m "I added some cool new stuff!"
    ```
4.  Finally, push it to GitHub:
    ```bash
    git push origin main
    ```

## Step 3: Send it to Google Cloud (The Magic Step)
We made a special "Magic Button" script to do the hard work for you.
1.  In your Terminal, type this to make the script ready:
    ```bash
    chmod +x deploy.sh
    ```
2.  Now, run the script to launch your website:
    ```bash
    ./deploy.sh
    ```
3.  **Watch the screen!** Google will ask you a few questions. Usually, you can just press **Enter** or type **y** for "Yes".

## Step 4: You Are Live! 🎈
1.  When the script finishes, it will give you a link that looks like `https://vivid-flow-xyz.a.run.app`.
2.  Click that link. **Boom!** Your website is alive for everyone to see.

---

### 🛠️ What happens behind the scenes?
1.  **Code on local:** You write the code on your computer.
2.  **Push to git:** You save a copy on GitHub so you never lose it.
3.  **Push to GCP:** Your computer sends the code to Google's super-computers.
4.  **Build on GCP:** Google turns your code into a "Container" (like a digital lunchbox that holds everything the app needs).
5.  **Go live:** Google gives you a web link and starts the app!

### 🌟 Pro Tip for Your Domain
If you want to use your own special name (like `mycoolsite.com`), go to the **Google Cloud Console**, find **Cloud Run**, and click **Manage Custom Domains**. It's like putting a nameplate on your new digital house!