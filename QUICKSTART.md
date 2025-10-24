# 🚀 Quick Start Guide - Deploy Your Portfolio in 5 Minutes

## Step 1: Get Your Repository Ready

1. **Create a new repository on GitHub**
   - Go to https://github.com/new
   - Name it: `yourname.github.io` (e.g., `louiseluli.github.io`)
   - Make it Public
   - Don't add README, .gitignore, or license (we have them)

2. **Clone this project to your local machine**
   ```bash
   git clone <this-folder-path>
   cd louise-portfolio
   ```

## Step 2: Customize Your Information

### Quick Edit: config.json
Edit `config.json` to update all your information in one place:

```json
{
  "personal": {
    "name": "Your Name",
    "title": "Your Title",
    "email": "your.email@example.com",
    "github": "https://github.com/yourusername",
    "linkedin": "https://linkedin.com/in/yourprofile"
  }
  // ... update other sections
}
```

### Or Edit HTML Directly
Open `index.html` and search for:
- "Louise Ferreira" → Replace with your name
- "louisesfer@gmail.com" → Replace with your email
- Social links → Update with your profiles

## Step 3: Add Your Movie Data

1. Export your IMDb watchlist:
   - Go to https://www.imdb.com/list/watchlist
   - Click "Export" → Download CSV
   
2. Replace `data/Watched.csv` with your file

3. Run analysis (optional):
   ```bash
   python scripts/analyze_data.py
   ```

## Step 4: Deploy to GitHub

```bash
# Initialize git (if not already)
git init

# Add all files
git add .

# Commit
git commit -m "Initial portfolio setup"

# Connect to your GitHub repository
git remote add origin https://github.com/yourusername/yourname.github.io.git

# Push
git branch -M main
git push -u origin main
```

## Step 5: Enable GitHub Pages

1. Go to your repository on GitHub
2. Click **Settings** → **Pages**
3. Under "Source":
   - Branch: `main`
   - Folder: `/ (root)`
4. Click **Save**

⏱️ Wait 2-5 minutes for deployment

🎉 Your site will be live at: `https://yourusername.github.io`

---

## 🎨 Customization Tips

### Change Colors
Edit `css/style.css` at the top (`:root` section):

```css
:root {
    --primary-color: #8B5CF6;    /* Change this */
    --secondary-color: #EC4899;   /* And this */
}
```

### Add New Projects
Edit `index.html` around line 250, copy a project card:

```html
<div class="project-card">
    <div class="project-header">
        <i class="fas fa-your-icon"></i>
        <h3>Your Project Name</h3>
    </div>
    <p class="project-description">
        Your project description...
    </p>
    <!-- ... -->
</div>
```

### Update Experience
Edit the timeline section around line 150 in `index.html`

---

## 🔧 Advanced: API Integration

### Get API Keys

1. **TMDB** (Free)
   - Register: https://www.themoviedb.org/settings/api
   - Copy API Key

2. **OMDB** (Free)
   - Register: http://www.omdbapi.com/apikey.aspx
   - Copy API Key

### Set Up Environment

Create `.env` file:
```bash
TMDB_API_KEY=your_key_here
OMDB_API_KEY=your_key_here
```

### Run Enrichment

```bash
# Install dependencies
pip install -r requirements.txt

# Download IMDb datasets (large!)
python scripts/enrich_movies.py --download-only

# Enrich your movies (this takes time!)
python scripts/enrich_movies.py

# Enrich people data
python scripts/enrich_people.py
```

---

## 📱 Testing Locally

```bash
# Option 1: Python
python -m http.server 8000

# Option 2: Node.js
npx http-server

# Open: http://localhost:8000
```

---

## ❓ Common Issues

### "Site not loading"
- Wait 5 minutes after first push
- Check Settings → Pages is enabled
- Check repository name is `username.github.io`

### "Images not showing"
- Make sure images are in `images/` folder
- Check paths in HTML are correct
- Push images to GitHub

### "Movies not showing"
- Check `data/Watched.csv` exists
- Run `python scripts/analyze_data.py`
- Check browser console for errors

---

## 🆘 Need Help?

- 📧 Email: louisesfer@gmail.com
- 🐛 Issues: Create issue on GitHub
- 📖 Docs: See full README.md

---

## ✅ Checklist

- [ ] Updated personal information
- [ ] Changed colors/theme
- [ ] Added your movie data
- [ ] Tested locally
- [ ] Pushed to GitHub
- [ ] Enabled GitHub Pages
- [ ] Site is live!
- [ ] Shared with friends 🎉

---

**Built with 💜**

Need more customization? Check out the full [README.md](README.md)
