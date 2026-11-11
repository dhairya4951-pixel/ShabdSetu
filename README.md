# शब्दसेतु — ShabdSetu

A bilingual Indian-language dictionary application that lets users search for
words using both Devanagari script and romanised spellings.

Built with Python, Django, SQLite and vanilla HTML/CSS/JS.

## Quick start

```bash
# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Create an admin account
python manage.py createsuperuser

# Start the development server
python manage.py runserver
```

Visit the admin panel at `http://127.0.0.1:8000/admin/` to add dictionary entries.

## Tech stack

| Layer     | Technology          |
|-----------|---------------------|
| Backend   | Django 6.0, Python 3.13 |
| Database  | SQLite              |
| Frontend  | Django Templates, HTML, CSS, vanilla JS |

## Project structure

```
Project/
├── shabdsetu/          # Django project settings, root URLs
├── dictionary/         # Main app — models, views, search, templates
├── data/               # Raw dictionary data for seeding (CSV/JSON)
├── manage.py
├── requirements.txt
└── README.md
```

## Licence

This project is part of the Garuda Prakashan × Rishihood live project.

