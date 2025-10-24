# 📁 Complete File Reference Guide

## 🎯 Quick Navigation

| What You Want | File to Edit |
|--------------|--------------|
| Change personal info | `config.json` or `index.html` |
| Change colors | `css/style.css` (line 1-20) |
| Add/edit experience | `index.html` (line 150-230) |
| Add/edit projects | `index.html` (line 250-350) |
| Analyze movies | `scripts/analyze_data.py` |
| Enrich movie data | `scripts/enrich_movies.py` |
| Cinema dashboard | `pages/cinema.html` |

---

## 📄 Core Website Files

### `index.html` (20,925 bytes)
**What it is**: Your main portfolio page
**Contains**:
- Hero section with your name and tagline
- About section with your identity and background
- Experience timeline (CloudWalk, IDB, EY, HSBC, etc.)
- Featured projects showcase
- Cinema analytics preview
- Contact information
- Footer

**Key Sections** (line numbers):
- Lines 1-20: HTML setup & meta tags
- Lines 30-90: Navigation bar
- Lines 95-125: Hero section (name, stats, buttons)
- Lines 130-180: About section
- Lines 185-280: Experience timeline
- Lines 285-380: Projects grid
- Lines 385-430: Cinema analytics preview
- Lines 435-460: Contact section
- Lines 465-480: Footer

**Edit For**:
- Personal information (name, email, social links)
- Work experience details
- Project descriptions and links
- Cinema statistics

---

### `css/style.css` (13,094 bytes)
**What it is**: All the styling and design
**Contains**:
- Color variables (easy to change theme!)
- Typography settings
- Layout and grid systems
- Animations and transitions
- Responsive design (mobile, tablet, desktop)
- Dark theme styling

**Key Sections**:
- Lines 1-25: CSS Variables (colors, spacing, fonts)
- Lines 27-55: Reset and base styles
- Lines 57-90: Typography
- Lines 92-180: Navigation bar
- Lines 182-320: Hero section
- Lines 322-400: About section
- Lines 402-520: Experience timeline
- Lines 522-640: Projects grid
- Lines 642-720: Cinema section
- Lines 722-780: Contact section
- Lines 782-820: Footer
- Lines 822-900: Animations
- Lines 902-1050: Responsive design (mobile)

**Edit For**:
- Colors (`:root` section at top)
- Fonts and typography
- Spacing and layout
- Animations and effects

---

### `js/main.js` (3,876 bytes)
**What it is**: Interactive features and animations
**Contains**:
- Smooth scrolling
- Mobile menu toggle
- Scroll animations
- Active navigation highlighting
- Counter animations
- Parallax effects
- Easter egg (Konami code!)

**Key Functions**:
- Lines 1-15: Smooth scrolling
- Lines 17-40: Mobile menu
- Lines 42-60: Navbar scroll effects
- Lines 62-90: Fade-in animations
- Lines 92-120: Active nav highlighting
- Lines 122-180: Counter animations
- Lines 182-200: Parallax effect
- Lines 202-250: Easter egg code

**Edit For**:
- Animation timings
- Counter values
- Interactive behaviors

---

## 📊 Data & Analytics Files

### `scripts/analyze_data.py` (6,432 bytes)
**What it does**: Analyzes your watched movies
**Creates**: `data/cinema_insights.json`
**Run**: `python scripts/analyze_data.py`

**Features**:
- Basic statistics (count, runtime, ratings)
- Genre analysis and distribution
- Decade breakdowns
- Director rankings
- Rating distributions
- Watching patterns over time
- Your ratings analysis

**Output Example**:
```json
{
  "total_movies": 2280,
  "avg_rating": 6.45,
  "top_genres": {
    "Drama": 1141,
    "Comedy": 1129
  }
}
```

---

### `scripts/enrich_movies.py` (18,921 bytes)
**What it does**: Enriches movies with TMDB, OMDB, Wikidata
**Creates**: `data/enriched_movies.csv`
**Run**: `python scripts/enrich_movies.py`

**APIs Used**:
- IMDb non-commercial datasets
- TMDB (genres, keywords, recommendations, images)
- OMDB (posters, plots)
- Wikidata (cultural context, metadata)

**Features**:
- Downloads IMDb datasets
- Merges data from multiple sources
- Intelligent genre merging
- Rate limiting (API-friendly)
- Progress tracking
- Error handling

**New Columns Added**:
- `tmdb_id`: TMDB movie ID
- `tmdb_keywords`: Keywords array (JSON)
- `tmdb_recommendations`: Recommended movies (JSON)
- `tmdb_similar`: Similar movies (JSON)
- `tmdb_tagline`: Movie tagline
- `tmdb_images`: Posters, backdrops, logos (JSON)
- `genres_merged`: Combined IMDb + TMDB genres
- `omdb_poster`: High-quality poster URL
- `omdb_plot`: Detailed plot description
- `wiki_logo_image`: Wikidata logo
- `wiki_main_subject`: Main themes
- `wiki_film_poster`: Film poster URL
- `wiki_based_on`: Based on (book, story, etc.)
- `wiki_set_in_period`: Historical period
- `wiki_inspired_by`: Inspirations

---

### `scripts/enrich_people.py` (8,653 bytes)
**What it does**: Enriches actors/directors data
**Creates**: `data/enriched_people.csv`
**Run**: `python scripts/enrich_people.py`

**Features**:
- Extracts people from your movies
- TMDB biography and filmography
- Wikidata family and awards
- Gender information (4 categories)
- Profile images

**New Columns Added**:
- `tmdb_id`: TMDB person ID
- `gender`: Gender identity
- `also_known_as`: Alternative names (JSON)
- `biography`: Full biography
- `birthday`: Date of birth
- `deathday`: Date of death (if applicable)
- `place_of_birth`: Birthplace
- `profile_images`: Profile photos (JSON)
- `combined_credits`: Full filmography (JSON)
- `wiki_nickname`: Nicknames
- `wiki_family_name`: Family name
- `wiki_given_name`: Given name
- `wiki_ethnic_group`: Ethnicity
- `wiki_height`: Height
- `wiki_eye_color`: Eye color
- `wiki_hair_color`: Hair color

---

## 📚 Documentation Files

### `README.md` (10,869 bytes)
**Complete documentation** with:
- Project overview
- Features list
- Technology stack
- Installation instructions
- API setup guides
- Data enrichment tutorials
- Customization guide
- Deployment instructions
- Troubleshooting
- Project structure
- Data schema
- Contributing guidelines

---

### `QUICKSTART.md` (4,288 bytes)
**5-minute deployment guide** with:
- Three simple steps to deploy
- Quick customization tips
- Common issues & solutions
- Checklist for launch

---

### `PROJECT_SUMMARY.md` (14,287 bytes)
**Comprehensive overview** with:
- What you've got
- Project structure
- Deployment guide
- Customization options
- Data insights
- Technical features
- Next steps
- Pro tips

---

## 🎨 Additional Pages

### `pages/cinema.html` (6,234 bytes)
**What it is**: Cinema analytics dashboard
**Contains**:
- Statistics overview (movies, hours, ratings)
- Genre charts (placeholder for interactive viz)
- Decade analysis (placeholder)
- Director rankings (placeholder)
- ML recommendations (placeholder)

**Edit For**:
- Adding interactive charts
- Implementing visualizations
- Connecting to enriched data

---

## ⚙️ Configuration Files

### `config.json` (6,914 bytes)
**Central configuration** for:
- Personal information
- Experience history
- Projects showcase
- Education details
- Skills list
- Awards & recognition
- Cinema statistics
- Theme colors

**Edit This File** to update:
- Name, email, social links
- Job history
- Project descriptions
- Skills and technologies
- Website colors

---

### `requirements.txt` (587 bytes)
**Python dependencies**:
- pandas (data manipulation)
- requests (API calls)
- numpy (numerical operations)
- matplotlib, seaborn, plotly (visualizations)
- streamlit (optional dashboard)
- beautifulsoup4 (web scraping)
- python-dotenv (environment variables)

**Install**: `pip install -r requirements.txt`

---

### `.gitignore` (923 bytes)
**Prevents tracking**:
- Python cache files
- API keys and secrets
- Large datasets
- Virtual environments
- OS-specific files
- Temporary files

---

### `LICENSE` (1,072 bytes)
**MIT License** - Free to use, modify, and share

---

## 🚀 Deployment Files

### `.github/workflows/deploy.yml` (573 bytes)
**GitHub Actions workflow** for:
- Automatic deployment on push
- GitHub Pages configuration
- Build validation

**Triggers On**:
- Push to `main` branch
- Pull requests
- Manual workflow dispatch

---

## 📂 Data Files

### `data/Watched.csv` (425 KB)
**Your original movie data** with 2,280 movies:
- Position, IMDb ID (Const)
- Title, Original Title
- Year, Runtime
- Genres
- IMDb Rating, Num Votes
- Directors
- Your Rating (for rated movies)
- Created date

---

### `data/cinema_insights.json` (Generated)
**Analysis results** including:
- Basic statistics
- Genre distributions
- Decade breakdowns
- Director rankings
- Rating analysis
- Watching patterns

**Generated by**: `scripts/analyze_data.py`

---

### `data/enriched_movies.csv` (To be generated)
**Enriched movie data** with 50+ columns:
- Original CSV data
- TMDB data (keywords, recommendations, images)
- OMDB data (posters, plots)
- Wikidata metadata

**Generated by**: `scripts/enrich_movies.py`

---

### `data/enriched_people.csv` (To be generated)
**Enriched people data** with:
- IMDb basic info
- TMDB biographies and filmographies
- Wikidata family and awards

**Generated by**: `scripts/enrich_people.py`

---

## 📁 Directory Structure

```
louise-portfolio/
│
├── 📄 index.html              # Main portfolio page
├── 📄 README.md               # Full documentation
├── 📄 QUICKSTART.md           # Quick deployment guide
├── 📄 PROJECT_SUMMARY.md      # Project overview
├── 📄 config.json             # Configuration file
├── 📄 requirements.txt        # Python dependencies
├── 📄 .gitignore             # Git ignore rules
├── 📄 LICENSE                 # MIT License
│
├── 📁 css/
│   └── 📄 style.css          # All styling
│
├── 📁 js/
│   └── 📄 main.js            # Interactive features
│
├── 📁 pages/
│   └── 📄 cinema.html        # Cinema dashboard
│
├── 📁 scripts/
│   ├── 📄 enrich_movies.py   # Movie enrichment
│   ├── 📄 enrich_people.py   # People enrichment
│   └── 📄 analyze_data.py    # Data analysis
│
├── 📁 data/
│   ├── 📄 Watched.csv        # Original data
│   ├── 📄 cinema_insights.json  # Generated insights
│   ├── 📄 enriched_movies.csv   # (to be generated)
│   └── 📄 enriched_people.csv   # (to be generated)
│
├── 📁 images/                # Place images here
│
└── 📁 .github/workflows/
    └── 📄 deploy.yml         # Auto-deployment
```

---

## 🎯 File Size Summary

| File | Size | Purpose |
|------|------|---------|
| index.html | 21 KB | Main page |
| style.css | 13 KB | All styling |
| main.js | 4 KB | Interactions |
| README.md | 11 KB | Documentation |
| config.json | 7 KB | Configuration |
| enrich_movies.py | 19 KB | Movie enrichment |
| analyze_data.py | 6 KB | Data analysis |
| enrich_people.py | 9 KB | People enrichment |
| Watched.csv | 425 KB | Your movie data |
| **Total** | **~515 KB** | Lightweight! |

---

## 🔄 Workflow

### 1. Basic Setup
```bash
# Edit personal info
vim config.json

# Deploy to GitHub
git init && git add . && git commit -m "Launch"
git push origin main
```

### 2. Data Analysis
```bash
# Install dependencies
pip install -r requirements.txt

# Analyze your movies
python scripts/analyze_data.py
```

### 3. Data Enrichment (Optional)
```bash
# Get API keys (TMDB, OMDB)
# Create .env file

# Enrich movies
python scripts/enrich_movies.py

# Enrich people
python scripts/enrich_people.py
```

### 4. Customize
```bash
# Change colors: css/style.css
# Add projects: index.html
# Update experience: index.html
```

---

## ✅ What To Edit First

1. **`config.json`** → Update all personal info
2. **`css/style.css`** → Change colors (line 1-20)
3. **`index.html`** → Update projects and experience
4. **Add photo** → Place in `images/profile.jpg`
5. **Deploy!** → Push to GitHub

---

## 🎉 You're Ready!

All files are documented, organized, and ready to use.

**Any questions?** Check the README.md for detailed guides!

**Ready to deploy?** Follow QUICKSTART.md for 5-minute setup!

**Need help?** All files have comments and clear structure!

---

Made with 💜 for Louise Ferreira
