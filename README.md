# Louise Ferreira - Portfolio & Cinema Analytics

A comprehensive personal portfolio website with advanced cinema data analytics, combining professional experience, AI research projects, and a rich movie dataset enriched from multiple sources.

🌐 **Live Site**: [https://louiseluli.github.io](https://louiseluli.github.io) *(Update with your actual URL)*

![Portfolio Preview](images/preview.png)

---

## 🎯 Overview

This portfolio showcases:

- **Professional Experience**: Machine Learning Engineer with focus on AI Ethics and Fairness
- **Research Projects**: Bias detection frameworks, RAG systems, and ML pipelines
- **Cinema Analytics**: 2,282+ movies analyzed with enriched metadata
- **Interactive Visualizations**: Data-driven insights from decades of cinema

---

## ✨ Features

### Portfolio Website
- ✅ Responsive, modern design with smooth animations
- ✅ Professional experience timeline
- ✅ Featured AI/ML projects showcase
- ✅ Interactive cinema analytics dashboard
- ✅ Mobile-friendly navigation
- ✅ SEO optimized

### Data Enrichment System
- ✅ **IMDb Integration**: Official non-commercial datasets
- ✅ **TMDB API**: Genres, keywords, recommendations, images
- ✅ **OMDB API**: Posters and plot descriptions
- ✅ **Wikidata**: Extended metadata and cultural context
- ✅ **DoestheDogDie**: Content warnings and triggers

### Analytics Capabilities
- 📊 Advanced data visualization
- 🎬 Movie recommendation system
- 📈 Trend analysis across decades
- 🌍 Geographic and cultural insights
- ⭐ Rating and genre correlations

---

## 🛠️ Technology Stack

### Frontend
- **HTML5** - Semantic markup
- **CSS3** - Modern styling with custom properties
- **JavaScript (ES6+)** - Interactive features
- **Font Awesome** - Icons

### Backend/Data Processing
- **Python 3.12+** - Data enrichment and analysis
- **pandas** - Data manipulation
- **requests** - API interactions
- **Streamlit** *(optional)* - Data dashboard

### APIs & Data Sources
- IMDb Non-Commercial Datasets
- TMDB (The Movie Database) API
- OMDB (Open Movie Database) API
- Wikidata SPARQL endpoint
- DoestheDogDie API

---

## 🚀 Quick Start

### Prerequisites

```bash
# Python 3.12+
python --version

# pip for package management
pip --version

# Git
git --version
```

### Installation

1. **Clone the repository**

```bash
git clone https://github.com/louiseluli/louise-portfolio.git
cd louise-portfolio
```

2. **Install Python dependencies**

```bash
pip install -r requirements.txt
```

3. **Set up API keys**

Create a `.env` file in the root directory:

```bash
# .env
TMDB_API_KEY=your_tmdb_api_key_here
OMDB_API_KEY=your_omdb_api_key_here
```

**Get API Keys:**
- TMDB: https://www.themoviedb.org/settings/api
- OMDB: http://www.omdbapi.com/apikey.aspx

4. **Download IMDb datasets** *(optional for full enrichment)*

```bash
python scripts/enrich_movies.py --download-only
```

### Running Locally

```bash
# Option 1: Simple HTTP server
python -m http.server 8000

# Option 2: Using Node.js (if installed)
npx http-server

# Then open: http://localhost:8000
```

---

## 📊 Data Enrichment

### Movie Data Enrichment

Enrich your movie watchlist with data from multiple sources:

```bash
python scripts/enrich_movies.py
```

**What it does:**
1. Downloads IMDb datasets (title.basics, ratings, crew, principals)
2. Merges with your `Watched.csv` file
3. Enriches each movie with:
   - TMDB: genres, keywords, recommendations, similar movies, images
   - OMDB: high-quality posters and detailed plot descriptions
   - Wikidata: cultural context, film posters, inspirations
4. Outputs: `data/enriched_movies.csv`

### People (Actors/Directors) Enrichment

```bash
python scripts/enrich_people.py
```

**Enriches:**
- Basic info: name, birth/death dates, professions
- TMDB: biography, profile images, filmography, gender
- Wikidata: family, awards, physical attributes, languages

### Custom Dataset Creation

```python
from scripts.enrich_movies import MovieDataEnricher

# Initialize with your API keys
enricher = MovieDataEnricher(
    tmdb_api_key="YOUR_KEY",
    omdb_api_key="YOUR_KEY"
)

# Load your data
df = enricher.load_watchlist('path/to/your/watchlist.csv')

# Enrich step by step
df = enricher.enrich_with_tmdb(df)
df = enricher.enrich_with_omdb(df)
df = enricher.enrich_with_wikidata(df)

# Save
enricher.save_enriched_data(df, 'output.csv')
```

---

## 📁 Project Structure

```
louise-portfolio/
├── index.html              # Main portfolio page
├── css/
│   └── style.css          # All styling
├── js/
│   └── main.js            # Interactive features
├── pages/
│   ├── cinema.html        # Cinema analytics dashboard
│   ├── data.html          # Dataset explorer
│   └── analysis.html      # ML insights
├── scripts/
│   ├── enrich_movies.py   # Movie data enrichment
│   ├── enrich_people.py   # People data enrichment
│   └── analyze_data.py    # Data analysis utilities
├── data/
│   ├── Watched.csv        # Original watchlist
│   ├── enriched_movies.csv # Enriched movie data
│   └── enriched_people.csv # Enriched people data
├── images/                 # Images and assets
├── .github/
│   └── workflows/
│       └── deploy.yml     # GitHub Actions deployment
├── requirements.txt        # Python dependencies
├── .gitignore
└── README.md
```

---

## 🌐 Deployment

### GitHub Pages (Recommended)

1. **Push to GitHub**

```bash
git add .
git commit -m "Initial portfolio setup"
git push origin main
```

2. **Enable GitHub Pages**

- Go to repository **Settings** → **Pages**
- Source: Deploy from branch `main`
- Folder: `/ (root)`
- Click **Save**

3. **Access your site**

Your site will be live at: `https://yourusername.github.io/repository-name/`

### Automatic Deployment

The included `.github/workflows/deploy.yml` enables:
- Automatic deployment on push to main
- Build validation
- Asset optimization

---

## 📝 Customization Guide

### Update Your Information

1. **Personal Details** (`index.html`)
   - Name, title, bio
   - Social media links
   - Contact information

2. **Experience Timeline** (`index.html`, line ~150)
   - Add/edit work experience
   - Update tech stacks
   - Modify dates and descriptions

3. **Projects** (`index.html`, line ~250)
   - Add new projects
   - Update descriptions and links
   - Change technologies used

4. **Colors & Branding** (`css/style.css`, `:root`)
   ```css
   --primary-color: #8B5CF6;    /* Your brand color */
   --secondary-color: #EC4899;   /* Accent color */
   ```

5. **Cinema Stats**
   - Update stats in `js/main.js` (line ~120)
   - Modify counters based on your data

### Add New Sections

```html
<!-- Add to index.html -->
<section id="new-section" class="new-section">
    <div class="container">
        <h2 class="section-title">New Section</h2>
        <!-- Your content -->
    </div>
</section>
```

```css
/* Add to css/style.css */
.new-section {
    background: var(--dark-bg);
    padding: var(--section-padding);
}
```

---

## 🎨 Design System

### Color Palette
- **Primary**: `#8B5CF6` (Purple) - Brand color
- **Secondary**: `#EC4899` (Pink) - Accents
- **Success**: `#10B981` (Green) - Positive actions
- **Dark BG**: `#0F172A` - Main background
- **Light BG**: `#1E293B` - Cards and sections

### Typography
- **Headings**: System fonts (Segoe UI, Roboto, etc.)
- **Body**: Default system font stack
- **Code**: Courier New, monospace

### Spacing Scale
```
Small:  0.5rem (8px)
Medium: 1rem (16px)
Large:  2rem (32px)
XLarge: 3rem (48px)
```

---

## 📊 Data Schema

### Enriched Movies Dataset

| Column | Source | Type | Description |
|--------|--------|------|-------------|
| Const | IMDb | string | IMDb ID (tconst) |
| Title | IMDb | string | Movie title |
| Year | IMDb | integer | Release year |
| IMDb Rating | IMDb | float | Average rating |
| genres_merged | IMDb + TMDB | string | Merged genre list |
| tmdb_id | TMDB | integer | TMDB movie ID |
| tmdb_keywords | TMDB | JSON | Keywords array |
| tmdb_recommendations | TMDB | JSON | Recommended movies |
| tmdb_tagline | TMDB | string | Movie tagline |
| omdb_poster | OMDB | string | Poster URL |
| omdb_plot | OMDB | string | Full plot |
| wiki_main_subject | Wikidata | string | Main themes |

### Enriched People Dataset

| Column | Source | Type | Description |
|--------|--------|------|-------------|
| nconst | IMDb | string | IMDb person ID |
| imdb_name | IMDb | string | Person name |
| gender | TMDB | string | Gender identity |
| biography | TMDB | text | Full biography |
| place_of_birth | TMDB | string | Birthplace |
| combined_credits | TMDB | JSON | Filmography |
| wiki_awards | Wikidata | JSON | Awards received |

---

## 🔧 Troubleshooting

### API Rate Limits

If you hit rate limits:

```python
# Adjust in scripts/enrich_movies.py
self.request_delay = 0.5  # Increase delay between requests
```

### IMDb Dataset Issues

If downloads fail:
- Check https://datasets.imdbws.com/ for availability
- Manually download and place in `data/imdb/`

### Missing Dependencies

```bash
pip install --upgrade -r requirements.txt
```

---

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📄 License

This project is open source and available under the [MIT License](LICENSE).

---

## 👤 Author

**Louise Ferreira**
- GitHub: [@louiseluli](https://github.com/louiseluli)
- LinkedIn: [louisesfer](https://linkedin.com/in/louisesfer)
- Email: louisesfer@gmail.com

---

## 🙏 Acknowledgments

- **IMDb** - For non-commercial datasets
- **TMDB** - For comprehensive movie database API
- **OMDB** - For additional movie metadata
- **Wikidata** - For cultural and contextual data
- **DoestheDogDie** - For content warnings
- **Font Awesome** - For beautiful icons

---

## 📈 Roadmap

- [ ] Add TV series enrichment
- [ ] Implement ML recommendation engine
- [ ] Create interactive data visualizations
- [ ] Add user authentication for personalized experiences
- [ ] Build API for accessing enriched data
- [ ] Mobile app for cinema tracking

---

## 💬 Support

Having issues? Found a bug? Have a feature request?

- 📧 Email: louisesfer@gmail.com
- 🐛 [Open an issue](https://github.com/louiseluli/louise-portfolio/issues)

---

<div align="center">

### Built with 💜 by Louise Ferreira

**Building ethical AI for a more just world**

[Portfolio](https://louiseluli.github.io) • [LinkedIn](https://linkedin.com/in/louisesfer) • [GitHub](https://github.com/louiseluli)

</div>
