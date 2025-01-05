# app.py

import os
import uuid
import re
from datetime import datetime
from functools import wraps

from flask import (
    Flask,
    request,
    redirect,
    url_for,
    flash,
    session,
    get_flashed_messages,
    jsonify
)
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.exceptions import NotFound

# If you install Flask-Mail: pip install Flask-Mail
from flask_mail import Mail, Message

###########################################################
#  1. Application and Configuration
###########################################################

app = Flask(__name__)

# Setting up the secret key for session/flash usage:
app.secret_key = os.urandom(24)

# Configuration of your upload folder and allowed file types
UPLOAD_FOLDER = os.path.join('static', 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'mp4', 'webm', 'ogg'}

# Ensure the folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50 MB

# Configuration for Flask-Mail
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'entreprise2rc@gmail.com'
app.config['MAIL_PASSWORD'] = 'your_secure_app_password'
app.config['MAIL_DEFAULT_SENDER'] = 'info@2rc.com'

mail = Mail(app)

###########################################################
#  2. Dummy Data Structures (emulating a simple DB)
###########################################################

# Users
# ------------------------------------------------------------------------------
users = [
    {
        "id": str(uuid.uuid4()),
        "username": "issou",  # Example admin user
        "password": generate_password_hash("12"),  # Example admin password
        "role": "admin"
    }
]

# Destinations
# ------------------------------------------------------------------------------
destinations = [
    {
        "id": str(uuid.uuid4()),
        "nom": "Agadez",
        "description": "Porte du désert, connue pour sa Grande Mosquée et le festival Cure Salée.",
        "image": "/static/uploads/agadez.jpg",
        "order": 1
    },
    {
        "id": str(uuid.uuid4()),
        "nom": "Niamey",
        "description": "Capitale animée du Niger, avec son grand marché et le Musée National.",
        "image": "/static/uploads/niamey.jpg",
        "order": 2
    },
    {
        "id": str(uuid.uuid4()),
        "nom": "Le Parc National du W",
        "description": "Magnifique réserve naturelle abritant une faune diversifiée.",
        "image": "/static/uploads/parc_w.jpg",
        "order": 3
    },
    {
        "id": str(uuid.uuid4()),
        "nom": "Zinder",
        "description": "Ancienne capitale, riche en histoire et en culture, avec son palais du Sultan.",
        "image": "/static/uploads/zinder.jpg",
        "order": 4
    },
    {
        "id": str(uuid.uuid4()),
        "nom": "Arbre du Ténéré (disparu)",
        "description": "Autrefois l'arbre le plus isolé du monde, un symbole du Sahara.",
        "image": "/static/uploads/arbre_tenere.jpg",
        "order": 5
    }
]

# Culture items
# ------------------------------------------------------------------------------
culture = [
    {
        "id": str(uuid.uuid4()),
        "nom": "Les Touaregs",
        "description": "Peuple nomade du Sahara, connu pour sa culture et ses traditions uniques.",
        "image": None
    },
    {
        "id": str(uuid.uuid4()),
        "nom": "La musique Haoussa",
        "description": "Rythmes vibrants et chants traditionnels de l'ethnie Haoussa.",
        "image": None
    },
    {
        "id": str(uuid.uuid4()),
        "nom": "L'artisanat nigérien",
        "description": "Travail du cuir, poterie, tissage, reflétant le savoir-faire local.",
        "image": None
    },
    {
        "id": str(uuid.uuid4()),
        "nom": "Les fêtes traditionnelles",
        "description": "Célébrations colorées marquant les événements importants de la vie communautaire.",
        "image": None
    }
]

# Practical infos
# ------------------------------------------------------------------------------
infos_pratiques = {
    "visa": (
        "Un visa peut être nécessaire selon votre nationalité. "
        "Vérifiez les exigences auprès de l'ambassade du Niger."
    ),
    "langues": "Français (officiel), Haoussa, Djerma et autres langues locales.",
    "monnaie": "Franc CFA (XOF).",
    "santé": (
        "Consultez votre médecin pour les vaccinations recommandées "
        "et les précautions à prendre."
    ),
    "sécurité": (
        "Informez-vous sur la situation sécuritaire et suivez les "
        "conseils des autorités locales."
    ),
    "transport": (
        "Vols internationaux vers Niamey. Transports locaux variés (taxis, bus)."
    )
}

# Custom pages
# ------------------------------------------------------------------------------
custom_pages = []

# Homepage media: images or videos to be displayed in a carousel
# ------------------------------------------------------------------------------
homepage_media = [
    # Example:
    # {"id": str(uuid.uuid4()), "type": 'image', "path": "/static/uploads/example.jpg", "title": "Titre de l'image"}
]

# Site settings
# ------------------------------------------------------------------------------
site_settings = {
    "title": "Tourisme Niger",
    "description": "Découvrez les merveilles du Niger avec nous.",
    "color_primary": "#2C3E50",   # Dark blue
    "color_secondary": "#18BC9C", # Turquoise
    "footer_text": "© 2025 Tourisme Niger. Tous droits réservés."
}

# Activity log: store admin actions
# ------------------------------------------------------------------------------
activity_logs = []

# Contact messages
# ------------------------------------------------------------------------------
messages = []

###########################################################
#  3. Helper Functions
###########################################################

def allowed_file(filename: str) -> bool:
    """
    Checks if the file extension is in ALLOWED_EXTENSIONS.
    """
    return (
        '.' in filename
        and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
    )

def login_required(f):
    """
    Decorator to ensure the user is logged in.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            flash("Veuillez vous connecter pour accéder à cette page.", "danger")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


###########################################################
#  4. Global HTML Template Rendering
###########################################################

def render_page(title, content, active_page=None):
    """
    Renders a full-page HTML layout with a sidebar, navbar, footer, and given content.
    `title` is for the <title> tag, while `content` is inserted as the main body.
    `active_page` highlights the corresponding link in the nav.
    """
    # Generate sidebar items
    sidebar_items = [
        ('Accueil', '/'),
        ('Destinations', '/destinations'),
        ('Culture', '/culture'),
        ('Infos Pratiques', '/infos-pratiques'),
        ('Contact', '/contact'),
    ]

    # Extend items if user is logged in
    if session.get('logged_in'):
        sidebar_items.extend([
            ('Gestion', '/manage'),
            ('Déconnexion', '/logout')
        ])
    else:
        sidebar_items.extend([
            ('Connexion', '/login'),
            ('Inscription', '/register')
        ])

    # Generate the HTML for the sidebar links
    def icon_for_label(label):
        """
        A small helper to add relevant icons depending on the label.
        """
        if label == "Accueil":
            return "home"
        elif label == "Destinations":
            return "map"
        elif label == "Culture":
            return "culture"  # (not a real FA icon, you can pick another if you want)
        elif label == "Infos Pratiques":
            return "info-circle"
        elif label == "Contact":
            return "envelope"
        elif label == "Gestion":
            return "cogs"
        elif label == "Connexion":
            return "sign-in-alt"
        elif label == "Inscription":
            return "user-plus"
        elif label == "Déconnexion":
            return "sign-out-alt"
        return "file"

    sidebar_html = ''.join([
        f'''
        <a href="{url}" 
           class="{"active" if active_page == label else ""}">
           <i class="fa fa-{icon_for_label(label)} me-2"></i>{label}
        </a>
        '''
        for (label, url) in sidebar_items
    ])

    # Generate flash messages
    flash_messages = ''.join([
        f'''
        <div class="alert alert-{category} alert-dismissible fade show" role="alert">
            {message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        </div>
        '''
        for category, message in get_flashed_messages(with_categories=True)
    ])

    # Additional styles (Bootstrap & FontAwesome are loaded from a CDN)
    style = f"""
    <!-- Google Fonts -->
    <link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@400;600&family=Roboto&display=swap" rel="stylesheet">
    <!-- Bootstrap CSS -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <!-- Font Awesome -->
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <!-- CKEditor (loaded in <body>) -->
    <style>
        body {{
            font-family: 'Roboto', sans-serif;
            background-color: #f0f2f5;
        }}
        h1, h2, h3, h4, h5, h6 {{
            font-family: 'Montserrat', sans-serif;
        }}
        .navbar {{
            background-color: {site_settings['color_primary']} !important;
        }}
        .navbar-brand {{
            font-size: 1.5rem;
            font-weight: bold;
        }}
        .sidebar {{
            height: 100vh;
            position: fixed;
            top: 0;
            left: 0;
            width: 250px;
            background-color: {site_settings['color_secondary']};
            padding-top: 70px;
            transition: transform 0.3s ease-in-out;
            z-index: 1000;
        }}
        .sidebar.collapsed {{
            transform: translateX(-250px);
        }}
        .sidebar a {{
            padding: 15px 20px;
            display: block;
            color: white;
            text-decoration: none;
            transition: background 0.3s;
        }}
        .sidebar a:hover {{
            background-color: rgba(255, 255, 255, 0.1);
        }}
        .content {{
            margin-left: 250px;
            padding: 20px;
            transition: margin-left 0.3s ease-in-out;
        }}
        .content.collapsed {{
            margin-left: 0;
        }}
        .footer {{
            background-color: {site_settings['color_secondary']};
            color: white;
            padding: 20px 0;
        }}
        .footer a {{
            color: white;
            text-decoration: none;
            margin: 0 10px;
            transition: color 0.3s;
        }}
        .footer a:hover {{
            color: #ddd;
        }}
        .card-img-top {{
            height: 200px;
            object-fit: cover;
            border-top-left-radius: 15px;
            border-top-right-radius: 15px;
        }}
        .btn-custom {{
            background-color: {site_settings['color_primary']};
            color: white;
            border-radius: 50px;
            transition: background-color 0.3s ease, transform 0.3s ease;
        }}
        .btn-custom:hover {{
            background-color: {site_settings['color_secondary']};
            transform: scale(1.05);
        }}
        .dashboard-card {{
            transition: transform 0.3s, box-shadow 0.3s;
        }}
        .dashboard-card:hover {{
            transform: scale(1.05);
            box-shadow: 0 8px 16px rgba(0,0,0,0.2);
        }}
        .carousel-item {{
            height: 80vh;
            min-height: 300px;
        }}
        .carousel-item img, .carousel-item video {{
            object-fit: cover;
            height: 100%;
            width: 100%;
        }}
        .carousel-caption {{
            background-color: rgba(0, 0, 0, 0.5);
            padding: 15px;
            border-radius: 10px;
        }}
        @media (max-width: 768px) {{
            .sidebar {{
                transform: translateX(-250px);
            }}
            .sidebar.collapsed {{
                transform: translateX(0);
            }}
            .content {{
                margin-left: 0;
            }}
            .content.collapsed {{
                margin-left: 250px;
            }}
        }}
    </style>
    """

    # Return the entire HTML content
    return f"""<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{site_settings['title']} - {title}</title>
    {style}
    <!-- Chart.js for the activity logs -->
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
</head>
<body>
    <!-- Sidebar -->
    <div class="sidebar" id="sidebar">
        {sidebar_html}
        <hr class="bg-light">
        {''.join([
            f'<a href="/pages/{page["url"]}" class="btn btn-link text-start"><i class="fa fa-file-alt me-2"></i>{page["title"]}</a>'
            for page in custom_pages
        ]) if custom_pages else '<p class="text-white ms-3">Aucune page personnalisée.</p>'}
    </div>

    <!-- Navbar -->
    <nav class="navbar navbar-expand-lg navbar-dark fixed-top">
        <div class="container-fluid">
            <button class="btn btn-secondary d-md-none" type="button" onclick="toggleSidebar()">
                <i class="fa fa-bars"></i>
            </button>
            <a class="navbar-brand ms-2" href="/">{site_settings['title']}</a>
            <button class="navbar-toggler" type="button" data-bs-toggle="collapse"
                    data-bs-target="#navbarSupportedContent" aria-controls="navbarSupportedContent"
                    aria-expanded="false" aria-label="Toggle navigation">
                <span class="navbar-toggler-icon"></span>
            </button>
            <div class="collapse navbar-collapse" id="navbarSupportedContent">
                <ul class="navbar-nav ms-auto mb-2 mb-lg-0">
                    {''.join([
                        f'<li class="nav-item"><a class="nav-link {"active" if active_page == label else ""}" href="{url}">{label}</a></li>'
                        for label, url in sidebar_items
                    ])}
                </ul>
            </div>
        </div>
    </nav>

    <!-- Main Content -->
    <div class="content" id="content">
        {flash_messages}
        {content}
    </div>

    <!-- Footer -->
    <footer class="footer text-center">
        <div class="container">
            <p>{site_settings['footer_text']}</p>
            <div class="mb-2">
                <a href="https://facebook.com" class="me-3"><i class="fab fa-facebook-f"></i></a>
                <a href="https://twitter.com" class="me-3"><i class="fab fa-twitter"></i></a>
                <a href="https://instagram.com"><i class="fab fa-instagram"></i></a>
            </div>
            <div>
                <a href="/privacy-policy" class="me-2">Politique de confidentialité</a> |
                <a href="/terms-of-service">Conditions d'utilisation</a>
            </div>
        </div>
    </footer>

    <!-- Bootstrap JS -->
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>

    <!-- Sidebar Toggle Script -->
    <script>
        function toggleSidebar() {{
            document.getElementById('sidebar').classList.toggle('collapsed');
            document.getElementById('content').classList.toggle('collapsed');
        }}
    </script>

    <!-- Slug Validation & Generation Script -->
    <script>
        function generateSlug(text) {{
            return text.toString().toLowerCase()
                .replace(/\\s+/g, '-')     // Replace spaces with -
                .replace(/[^\w\\-]+/g, '') // Remove all non-word chars
                .replace(/\\-\\-+/g, '-')   // Replace multiple - with single -
                .replace(/^-+/, '')        // Trim - from start of text
                .replace(/-+$/, '');       // Trim - from end of text
        }}
        document.addEventListener('DOMContentLoaded', function() {{
            const titleInput = document.getElementById('title');
            const slugInput = document.getElementById('url');
            const slugFeedback = document.getElementById('slugFeedback');
            if (titleInput && slugInput) {{
                titleInput.addEventListener('input', function() {{
                    if (!slugInput.disabled) {{
                        slugInput.value = generateSlug(this.value);
                    }}
                }});
                slugInput.addEventListener('blur', function() {{
                    const slug = this.value;
                    if (slug) {{
                        fetch(`/validate_slug?slug=${{slug}}`)
                            .then(response => response.json())
                            .then(data => {{
                                if (data.exists) {{
                                    slugInput.classList.add('is-invalid');
                                    slugFeedback.textContent = 'Cette URL est déjà utilisée.';
                                }} else {{
                                    slugInput.classList.remove('is-invalid');
                                    slugFeedback.textContent = '';
                                }}
                            }})
                            .catch(error => {{
                                console.error('Erreur:', error);
                            }});
                    }}
                }});
            }}
            // Confirmation delete modals
            var confirmDeleteModal = new bootstrap.Modal(document.getElementById('confirmDeleteModal'));
            document.querySelectorAll('.btn-danger').forEach(function(element) {{
                element.classList.add('btn-delete');
            }});
            document.querySelectorAll('.btn-delete').forEach(function(element) {{
                element.addEventListener('click', function(event) {{
                    event.preventDefault();
                    var href = this.getAttribute('href');
                    document.getElementById('confirmDeleteButton').setAttribute('href', href);
                    confirmDeleteModal.show();
                }});
            }});
        }});
    </script>

    <!-- Confirm Delete Modal -->
    <div class="modal fade" id="confirmDeleteModal" tabindex="-1" aria-labelledby="confirmDeleteModalLabel" aria-hidden="true">
      <div class="modal-dialog">
        <div class="modal-content">
          <div class="modal-header">
            <h1 class="modal-title fs-5" id="confirmDeleteModalLabel">Confirmer la Suppression</h1>
            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Fermer"></button>
          </div>
          <div class="modal-body">
            Êtes-vous sûr de vouloir supprimer cet élément ?
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Annuler</button>
            <a href="#" id="confirmDeleteButton" class="btn btn-danger">Supprimer</a>
          </div>
        </div>
      </div>
    </div>

    <!-- CKEditor -->
    <script src="https://cdn.ckeditor.com/4.20.1/standard/ckeditor.js"></script>

</body>
</html>
"""

###########################################################
#  5. Routes
###########################################################

# SLUG VALIDATION
# ------------------------------------------------------------------------------
@app.route('/validate_slug')
def validate_slug():
    slug = request.args.get('slug', '').strip().lower()
    # Check if this slug is already used by any custom page
    exists = any(page['url'] == slug for page in custom_pages)
    return jsonify({'exists': exists})

# REGISTER
# ------------------------------------------------------------------------------
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username').strip()
        password = request.form.get('password').strip()
        confirm_password = request.form.get('confirm_password').strip()

        if not username or not password or not confirm_password:
            flash('Veuillez remplir tous les champs.', 'danger')
            return redirect(url_for('register'))

        if password != confirm_password:
            flash('Les mots de passe ne correspondent pas.', 'danger')
            return redirect(url_for('register'))

        if any(user['username'] == username for user in users):
            flash('Ce nom d\'utilisateur est déjà pris.', 'danger')
            return redirect(url_for('register'))

        # Create a new user with role 'user'
        hashed_password = generate_password_hash(password)
        users.append({
            "id": str(uuid.uuid4()),
            "username": username,
            "password": hashed_password,
            "role": "user"
        })
        flash('Inscription réussie! Vous pouvez maintenant vous connecter.', 'success')
        # Log activity
        activity_logs.append({
            "user": username,
            "action": "Inscription",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
        return redirect(url_for('login'))

    # Render page
    return render_page(
        "Inscription",
        f"""
        <div class="row justify-content-center">
            <div class="col-md-8">
                <div class="card shadow">
                    <div class="card-header text-white" 
                         style="background-color: {site_settings['color_secondary']};">
                        <h3 class="mb-0"><i class="fa fa-user-plus me-2"></i> Inscription</h3>
                    </div>
                    <div class="card-body">
                        <form method="post">
                            <div class="mb-3">
                                <label for="username" class="form-label">Nom d'utilisateur:</label>
                                <input type="text" class="form-control" name="username" id="username" required>
                            </div>
                            <div class="mb-3">
                                <label for="password" class="form-label">Mot de passe:</label>
                                <input type="password" class="form-control" name="password" id="password" required>
                            </div>
                            <div class="mb-3">
                                <label for="confirm_password" class="form-label">Confirmer le mot de passe:</label>
                                <input type="password" class="form-control" name="confirm_password" id="confirm_password" required>
                            </div>
                            <button type="submit" class="btn btn-primary">
                                <i class="fa fa-user-check me-2"></i> S'inscrire
                            </button>
                        </form>
                    </div>
                </div>
            </div>
        </div>
        """,
        active_page='Inscription'
    )

# LOGIN
# ------------------------------------------------------------------------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username').strip()
        password = request.form.get('password').strip()

        user = next((u for u in users if u['username'] == username), None)
        if user and check_password_hash(user['password'], password):
            session['logged_in'] = True
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['role'] = user['role']

            flash('Connexion réussie!', 'success')
            # Log activity
            activity_logs.append({
                "user": user['username'],
                "action": "Connexion",
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
            if user['role'] == 'admin':
                return redirect(url_for('manage'))
            else:
                return redirect(url_for('index'))
        else:
            flash('Nom d\'utilisateur ou mot de passe incorrect.', 'danger')

    return render_page(
        "Connexion",
        f"""
        <div class="row justify-content-center">
            <div class="col-md-8">
                <div class="card shadow">
                    <div class="card-header text-white" 
                         style="background-color: {site_settings['color_secondary']};">
                        <h3 class="mb-0"><i class="fa fa-sign-in-alt me-2"></i> Connexion</h3>
                    </div>
                    <div class="card-body">
                        <form method="post">
                            <div class="mb-3">
                                <label for="username" class="form-label">Nom d'utilisateur:</label>
                                <input type="text" class="form-control" name="username" id="username" required>
                            </div>
                            <div class="mb-3">
                                <label for="password" class="form-label">Mot de passe:</label>
                                <input type="password" class="form-control" name="password" id="password" required>
                            </div>
                            <button type="submit" class="btn btn-success">
                                <i class="fa fa-sign-in-alt me-2"></i> Se connecter
                            </button>
                        </form>
                    </div>
                </div>
            </div>
        </div>
        """,
        active_page='Connexion'
    )

# LOGOUT
# ------------------------------------------------------------------------------
@app.route('/logout')
def logout():
    if session.get('username'):
        activity_logs.append({
            "user": session['username'],
            "action": "Déconnexion",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
    session.clear()
    flash('Vous êtes déconnecté.', 'success')
    return redirect(url_for('index'))

# INDEX
# ------------------------------------------------------------------------------
@app.route('/')
def index():
    sorted_dest = sorted(destinations, key=lambda x: x['order'])
    featured_destinations = sorted_dest[:3]

    # Build the carousel if there's media
    if homepage_media:
        carousel_indicators = ''.join([
            f'''
            <button type="button" data-bs-target="#homepageCarousel" data-bs-slide-to="{i}"
                    {"class=\"active\"" if i == 0 else ""} 
                    aria-current="{"true" if i == 0 else "false"}" 
                    aria-label="Slide {i + 1}"></button>
            '''
            for i in range(len(homepage_media))
        ])

        carousel_items = ''.join([
            f'''
            <div class="carousel-item {"active" if i == 0 else ""}">
                {
                    '<img src="' + media['path'] + '" class="d-block w-100" alt="' + media.get('title', '') + '">'
                    if media['type'] == 'image'
                    else
                    f'<video class="d-block w-100" controls>'
                    f'<source src="{media["path"]}" type="video/{media["path"].rsplit(".", 1)[1].lower()}">'
                    f'Votre navigateur ne supporte pas les vidéos HTML5.</video>'
                }
                {
                    f'<div class="carousel-caption d-none d-md-block"><h5>{media["title"]}</h5></div>'
                    if media.get('title') else ''
                }
            </div>
            '''
            for i, media in enumerate(homepage_media)
        ])

        carousel_controls = """
        <button class="carousel-control-prev" type="button" 
                data-bs-target="#homepageCarousel" data-bs-slide="prev">
            <span class="carousel-control-prev-icon" aria-hidden="true"></span>
            <span class="visually-hidden">Précédent</span>
        </button>
        <button class="carousel-control-next" type="button" 
                data-bs-target="#homepageCarousel" data-bs-slide="next">
            <span class="carousel-control-next-icon" aria-hidden="true"></span>
            <span class="visually-hidden">Suivant</span>
        </button>
        """

        carousel = f"""
        <div id="homepageCarousel" class="carousel slide" data-bs-ride="carousel">
            <div class="carousel-indicators">
                {carousel_indicators}
            </div>
            <div class="carousel-inner">
                {carousel_items}
            </div>
            {carousel_controls}
        </div>
        """
    else:
        carousel = '<p class="text-center">Aucun média pour la page d\'accueil.</p>'

    content = f"""
    <section class="hero mb-4 fade-in">
        {carousel}
    </section>
    <section class="featured-destinations">
        <h2 class="mb-4">Destinations Phares</h2>
        <div class="row">
            {''.join([
                f'''
                <div class="col-md-4 mb-4">
                    <div class="card h-100 dashboard-card">
                        <img src="{dest['image']}" class="card-img-top" 
                             alt="Vue panoramique de {dest['nom']}">
                        <div class="card-body d-flex flex-column">
                            <h5 class="card-title">{dest['nom']}</h5>
                            <p class="card-text">{dest['description']}</p>
                            <a href="/destinations" class="btn btn-custom mt-auto">
                                <i class="fa fa-info-circle me-2"></i> En savoir plus
                            </a>
                        </div>
                    </div>
                </div>
                '''
                for dest in featured_destinations
            ])}
        </div>
    </section>
    """
    return render_page("Accueil", content, active_page='Accueil')

# DESTINATIONS
# ------------------------------------------------------------------------------
@app.route('/destinations')
def liste_destinations():
    search_query = request.args.get('search', '').strip().lower()
    page = int(request.args.get('page', 1))
    per_page = 6

    if search_query:
        filtered = [
            d for d in destinations
            if (search_query in d['nom'].lower() or search_query in d['description'].lower())
        ]
    else:
        filtered = destinations

    sorted_dest = sorted(filtered, key=lambda x: x['order'])
    total = len(sorted_dest)
    pages = (total + per_page - 1) // per_page
    paginated = sorted_dest[(page - 1)*per_page : page*per_page]

    # Generate pagination
    if pages > 1:
        pagination_buttons = ''.join([
            f'''
            <li class="page-item {"active" if i == page else ""}">
                <a class="page-link" 
                   href="?page={i}{f"&search={search_query}" if search_query else ""}">{i}</a>
            </li>
            '''
            for i in range(1, pages + 1)
        ])

        pagination = f"""
        <nav aria-label="Page navigation">
            <ul class="pagination justify-content-center">
                <li class="page-item {'disabled' if page <= 1 else ''}">
                    <a class="page-link"
                       href="?page={page-1}{f"&search={search_query}" if search_query else ''}"
                       tabindex="-1">Précédent</a>
                </li>
                {pagination_buttons}
                <li class="page-item {'disabled' if page >= pages else ''}">
                    <a class="page-link"
                       href="?page={page+1}{f"&search={search_query}" if search_query else ''}">
                       Suivant
                    </a>
                </li>
            </ul>
        </nav>
        """
    else:
        pagination = ''

    content = f"""
    <section class="destinations-page">
        <h2 class="mb-4">Découvrez nos magnifiques destinations</h2>
        <form method="get" class="row g-3 mb-4">
            <div class="col-md-10">
                <input type="text" class="form-control" name="search" 
                       placeholder="Rechercher une destination..." value="{search_query}">
            </div>
            <div class="col-md-2">
                <button type="submit" class="btn btn-custom w-100">
                    <i class="fa fa-search me-2"></i> Rechercher
                </button>
            </div>
        </form>
        <div class="row">
            {''.join([
                f'''
                <div class="col-md-4 mb-4">
                    <div class="card dashboard-card">
                        <img src="{dest['image']}" class="card-img-top"
                             alt="Vue panoramique de {dest['nom']}">
                        <div class="card-body d-flex flex-column">
                            <h5 class="card-title">{dest['nom']}</h5>
                            <p class="card-text">{dest['description']}</p>
                        </div>
                    </div>
                </div>
                '''
                for dest in paginated
            ])}
        </div>
        {pagination}
    </section>
    """
    return render_page("Destinations", content, active_page='Destinations')

# CULTURE
# ------------------------------------------------------------------------------
@app.route('/culture')
def culture_niger():
    search_query = request.args.get('search', '').strip().lower()
    page = int(request.args.get('page', 1))
    per_page = 6

    if search_query:
        filtered = [
            c for c in culture
            if (search_query in c['nom'].lower() or search_query in c['description'].lower())
        ]
    else:
        filtered = culture

    sorted_cult = sorted(filtered, key=lambda x: x['nom'])
    total = len(sorted_cult)
    pages = (total + per_page - 1) // per_page
    paginated = sorted_cult[(page - 1)*per_page : page*per_page]

    # Generate pagination
    if pages > 1:
        pagination_buttons = ''.join([
            f'''
            <li class="page-item {"active" if i == page else ""}">
                <a class="page-link" 
                   href="?page={i}{f"&search={search_query}" if search_query else ""}">{i}</a>
            </li>
            '''
            for i in range(1, pages + 1)
        ])
        pagination = f"""
        <nav aria-label="Page navigation">
            <ul class="pagination justify-content-center">
                <li class="page-item {'disabled' if page <= 1 else ''}">
                    <a class="page-link"
                       href="?page={page-1}{f"&search={search_query}" if search_query else ""}"
                       tabindex="-1">Précédent</a>
                </li>
                {pagination_buttons}
                <li class="page-item {'disabled' if page >= pages else ''}">
                    <a class="page-link"
                       href="?page={page+1}{f"&search={search_query}" if search_query else ""}">
                       Suivant
                    </a>
                </li>
            </ul>
        </nav>
        """
    else:
        pagination = ''

    content = f"""
    <section class="culture-page">
        <h2 class="mb-4">Plongez au cœur de la culture nigérienne</h2>
        <form method="get" class="row g-3 mb-4">
            <div class="col-md-10">
                <input type="text" class="form-control" name="search"
                       placeholder="Rechercher une culture..." value="{search_query}">
            </div>
            <div class="col-md-2">
                <button type="submit" class="btn btn-custom w-100">
                    <i class="fa fa-search me-2"></i> Rechercher
                </button>
            </div>
        </form>
        <div class="row">
            {''.join([
                f'''
                <div class="col-md-4 mb-4">
                    <div class="card dashboard-card">
                        {
                            '<img src="' + item['image'] + '" class="card-img-top" alt="' + item['nom'] + '">'
                            if item['image']
                            else ''
                        }
                        <div class="card-body d-flex flex-column">
                            <h5 class="card-title">{item['nom']}</h5>
                            <p class="card-text">{item['description']}</p>
                        </div>
                    </div>
                </div>
                '''
                for item in paginated
            ])}
        </div>
        {pagination}
    </section>
    """
    return render_page("Culture", content, active_page='Culture')

# INFOS PRATIQUES
# ------------------------------------------------------------------------------
@app.route('/infos-pratiques')
def informations_pratiques_route():
    items_html = []
    for key, value in infos_pratiques.items():
        items_html.append(f"""
        <div class="accordion-item">
            <h2 class="accordion-header" id="heading{key}">
                <button class="accordion-button collapsed" 
                        type="button" data-bs-toggle="collapse"
                        data-bs-target="#collapse{key}"
                        aria-expanded="false"
                        aria-controls="collapse{key}">
                    {key.capitalize()}
                </button>
            </h2>
            <div id="collapse{key}" class="accordion-collapse collapse"
                 aria-labelledby="heading{key}"
                 data-bs-parent="#infosPratiquesAccordion">
                <div class="accordion-body">
                    {value}
                </div>
            </div>
        </div>
        """)

    content = f"""
    <section class="infos-page">
        <h2 class="mb-4">Préparez votre voyage au Niger</h2>
        <div class="accordion" id="infosPratiquesAccordion">
            {''.join(items_html)}
        </div>
    </section>
    """
    return render_page("Infos Pratiques", content, active_page='Infos Pratiques')

# CONTACT
# ------------------------------------------------------------------------------
@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        nom = request.form.get('nom').strip()
        email = request.form.get('email').strip()
        msg_text = request.form.get('message').strip()

        if not nom or not email or not msg_text:
            flash('Veuillez remplir tous les champs du formulaire.', 'danger')
            return redirect(url_for('contact'))

        messages.append({
            "id": str(uuid.uuid4()),
            "nom": nom,
            "email": email,
            "message": msg_text,
            "lu": False
        })

        flash('Votre message a bien été envoyé !', 'success')
        if session.get('username'):
            activity_logs.append({
                "user": session['username'],
                "action": f"Envoyé un message via le formulaire de contact",
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
        else:
            activity_logs.append({
                "user": "Invité",
                "action": f"Envoyé un message via le formulaire de contact",
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
        return redirect(url_for('contact'))

    content = f"""
    <section class="contact-page">
        <h2 class="mb-4">N'hésitez pas à nous contacter</h2>
        <div class="row justify-content-center">
            <div class="col-md-8">
                <div class="card shadow">
                    <div class="card-body">
                        <form method="POST">
                            <div class="mb-3">
                                <label for="nom" class="form-label">Nom :</label>
                                <input type="text" class="form-control" name="nom" id="nom" required>
                            </div>
                            <div class="mb-3">
                                <label for="email" class="form-label">Email :</label>
                                <input type="email" class="form-control" name="email" id="email" required>
                            </div>
                            <div class="mb-3">
                                <label for="message" class="form-label">Message :</label>
                                <textarea class="form-control" name="message" id="message" rows="5" required></textarea>
                            </div>
                            <button type="submit" class="btn btn-custom">
                                <i class="fa fa-paper-plane me-2"></i> Envoyer
                            </button>
                        </form>
                    </div>
                </div>
            </div>
        </div>
    </section>
    """
    return render_page("Contact", content, active_page='Contact')

###########################################################
#  6. Admin / Manage Routes
###########################################################

@app.route('/manage', methods=['GET', 'POST'])
@login_required
def manage():
    # Check if user is admin
    if session.get('role') != 'admin':
        flash('Accès refusé. Administrateur requis.', 'danger')
        return redirect(url_for('index'))

    uploaded_files = [
        f for f in os.listdir(UPLOAD_FOLDER)
        if os.path.isfile(os.path.join(UPLOAD_FOLDER, f))
    ]
    content_admin = ""

    # Handle uploading new files
    if request.method == 'POST':
        if 'file' in request.files:
            file = request.files['file']
            media_type = request.form.get('media_type')  # 'homepage' or 'custom_page'
            if file.filename == '':
                flash('Aucun fichier sélectionné.', 'danger')
            elif file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

                if media_type == 'homepage':
                    homepage_media.append({
                        "id": str(uuid.uuid4()),
                        "type": (
                            'video'
                            if filename.rsplit('.', 1)[1].lower() in {'mp4', 'webm', 'ogg'}
                            else 'image'
                        ),
                        "path": f"/static/uploads/{filename}",
                        "title": request.form.get('title', '')
                    })
                    flash(
                        f'Fichier {filename} uploadé et ajouté à la page d\'accueil avec succès !',
                        'success'
                    )
                    activity_logs.append({
                        "user": session['username'],
                        "action": f"Uploadé média d'accueil: {filename}",
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    })
                elif media_type == 'custom_page':
                    flash(
                        f'Fichier {filename} uploadé avec succès pour les pages personnalisées!',
                        'success'
                    )
                    activity_logs.append({
                        "user": session['username'],
                        "action": f"Uploadé média pour pages personnalisées: {filename}",
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    })
            else:
                flash('Type de fichier non autorisé.', 'danger')
        elif 'setting_title' in request.form:
            # Update site settings
            site_settings['title'] = request.form.get('setting_title').strip()
            site_settings['description'] = request.form.get('setting_description').strip()
            site_settings['color_primary'] = request.form.get('setting_color_primary').strip()
            site_settings['color_secondary'] = request.form.get('setting_color_secondary').strip()
            site_settings['footer_text'] = request.form.get('setting_footer_text').strip()
            flash('Paramètres du site mis à jour avec succès!', 'success')
            activity_logs.append({
                "user": session['username'],
                "action": "Mis à jour les paramètres du site",
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
            return redirect(url_for('manage'))
        return redirect(url_for('manage'))

    # Display homepage media
    if homepage_media:
        homepage_media_html = ''.join([
            f'''
            <div class="col-md-4 mb-4">
                <div class="card dashboard-card">
                    {
                        '<img src="' + media['path'] + '" class="d-block w-100" alt="' + media.get('title', '') + '">'
                        if media['type'] == 'image'
                        else
                        f'<video class="d-block w-100" controls>'
                        f'<source src="{media["path"]}" type="video/{media["path"].rsplit(".", 1)[1].lower()}">'
                        f'Votre navigateur ne supporte pas les vidéos HTML5.</video>'
                    }
                    <div class="card-body text-center">
                        <p class="card-text">{media.get('title', '')}</p>
                        <a href="/manage/delete_homepage_media/{media['id']}" 
                           class="btn btn-danger btn-sm">
                           <i class="fa fa-trash me-2"></i> Supprimer
                        </a>
                    </div>
                </div>
            </div>
            '''
            for media in homepage_media
        ])
    else:
        homepage_media_html = '<p>Aucun média pour la page d\'accueil.</p>'

    # HOME PAGE MEDIA SECTION
    content_admin += f"""
    <section class="admin-section mb-5">
        <h2 class="mb-4">Gestion des Médias de la Page d'Accueil</h2>
        <form method="post" enctype="multipart/form-data" class="row g-3 mb-4">
            <div class="col-md-4">
                <label for="file" class="form-label">Sélectionner un média :</label>
                <input class="form-control" type="file" name="file" id="file" required>
            </div>
            <div class="col-md-4">
                <label for="media_type" class="form-label">Type de média :</label>
                <select class="form-select" name="media_type" id="media_type" required>
                    <option value="homepage" selected>Page d'Accueil</option>
                    <option value="custom_page">Pages Personnalisées</option>
                </select>
            </div>
            <div class="col-md-4">
                <label for="title" class="form-label">Titre (optionnel) :</label>
                <input type="text" class="form-control" name="title" id="title" placeholder="Titre du média">
            </div>
            <div class="col-12">
                <button type="submit" class="btn btn-success">
                    <i class="fa fa-upload me-2"></i> Upload
                </button>
            </div>
        </form>
        <h3 class="mb-3">Médias Uploadés pour la Page d'Accueil</h3>
        <div class="row">
            {homepage_media_html}
        </div>
    </section>
    """

    # FILES FOR CUSTOM PAGES
    content_admin += f"""
    <section class="admin-section mb-5">
        <h2 class="mb-4">Gestion des Médias pour les Pages Personnalisées</h2>
        <p>Les fichiers uploadés ici peuvent être utilisés dans les pages personnalisées.</p>
        <div class="row">
            {''.join([
                f'''
                <div class="col-md-4 mb-4">
                    <div class="card dashboard-card">
                        {
                            '<img src="/static/uploads/{file}" class="card-img-top" alt="{file}">'
                            if file.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg', 'gif'}
                            else
                            f'<video class="card-img-top" controls>'
                            f'<source src="/static/uploads/{file}" type="video/{file.rsplit(".", 1)[1].lower()}">'
                            f'</video>'
                        }
                        <div class="card-body text-center">
                            <p class="card-text">{file}</p>
                            <a href="/manage/delete_uploaded_image/{file}" 
                               class="btn btn-danger btn-sm">
                               <i class="fa fa-trash me-2"></i> Supprimer
                            </a>
                        </div>
                    </div>
                </div>
                '''
                for file in uploaded_files
            ]) if uploaded_files else '<p>Aucun fichier uploadé.</p>'}
        </div>
    </section>
    """

    # SITE SETTINGS SECTION
    content_admin += f"""
    <section class="admin-section mb-5">
        <h2 class="mb-4">Paramètres du Site</h2>
        <form method="post" class="row g-3">
            <div class="col-md-6">
                <label for="setting_title" class="form-label">Titre du Site :</label>
                <input type="text" class="form-control" 
                       name="setting_title" id="setting_title"
                       value="{site_settings['title']}" required>
            </div>
            <div class="col-md-6">
                <label for="setting_description" class="form-label">Description du Site :</label>
                <input type="text" class="form-control" 
                       name="setting_description" id="setting_description"
                       value="{site_settings['description']}" required>
            </div>
            <div class="col-md-4">
                <label for="setting_color_primary" class="form-label">Couleur Primaire :</label>
                <input type="color" class="form-control form-control-color"
                       name="setting_color_primary" id="setting_color_primary"
                       value="{site_settings['color_primary']}"
                       title="Choisissez une couleur primaire">
            </div>
            <div class="col-md-4">
                <label for="setting_color_secondary" class="form-label">Couleur Secondaire :</label>
                <input type="color" class="form-control form-control-color"
                       name="setting_color_secondary" id="setting_color_secondary"
                       value="{site_settings['color_secondary']}"
                       title="Choisissez une couleur secondaire">
            </div>
            <div class="col-md-4">
                <label for="setting_footer_text" class="form-label">Texte du Footer :</label>
                <input type="text" class="form-control" 
                       name="setting_footer_text" id="setting_footer_text"
                       value="{site_settings['footer_text']}" required>
            </div>
            <div class="col-12">
                <button type="submit" class="btn btn-success">
                    <i class="fa fa-save me-2"></i> Enregistrer les Paramètres
                </button>
            </div>
        </form>
    </section>
    """

    # MANAGE DESTINATIONS
    content_admin += f"""
    <section class="admin-section mb-5">
        <h2 class="mb-4">Gestion des Destinations</h2>
        <div class="mb-3">
            <a href="/manage/add_destination" class="btn btn-primary">
                <i class="fa fa-plus me-2"></i> Ajouter une destination
            </a>
        </div>
        <div class="table-responsive">
            <table class='table table-striped table-hover'>
                <thead class="table-warning">
                    <tr>
                        <th>Nom</th>
                        <th>Description</th>
                        <th>Image</th>
                        <th>Ordre</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    {''.join([
                        f"""
                        <tr>
                            <td>{dest['nom']}</td>
                            <td>{dest['description']}</td>
                            <td><img src='{dest['image']}' 
                                     alt='Vue panoramique de {dest['nom']}'
                                     width='100'></td>
                            <td>{dest['order']}</td>
                            <td>
                                <a href='/manage/edit_destination/{dest['id']}' 
                                   class='btn btn-sm btn-warning'>
                                   <i class='fa fa-edit me-1'></i> Modifier
                                </a>
                                <a href='/manage/delete_destination/{dest['id']}' 
                                   class='btn btn-sm btn-danger btn-delete'>
                                   <i class='fa fa-trash me-1'></i> Supprimer
                                </a>
                            </td>
                        </tr>
                        """
                        for dest in destinations
                    ])}
                </tbody>
            </table>
        </div>
    </section>
    """

    # MANAGE CULTURE
    content_admin += f"""
    <section class="admin-section mb-5">
        <h2 class="mb-4">Gestion de la Culture</h2>
        <div class="mb-3">
            <a href="/manage/add_culture" class="btn btn-primary">
                <i class="fa fa-plus me-2"></i> Ajouter une entrée culturelle
            </a>
        </div>
        <div class="table-responsive">
            <table class='table table-striped table-hover'>
                <thead class="table-warning">
                    <tr>
                        <th>Nom</th>
                        <th>Description</th>
                        <th>Image</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    {''.join([
                        f"""
                        <tr>
                            <td>{item['nom']}</td>
                            <td>{item['description']}</td>
                            <td>{
                                ('<img src="' + item['image'] + '" class="img-fluid" alt="' + item['nom'] + '" style="max-width: 150px;">')
                                if item['image'] else 'Aucune Image'
                            }</td>
                            <td>
                                <a href='/manage/edit_culture/{item['id']}' 
                                   class='btn btn-sm btn-warning'>
                                   <i class='fa fa-edit me-1'></i> Modifier
                                </a>
                                <a href='/manage/delete_culture/{item['id']}' 
                                   class='btn btn-sm btn-danger btn-delete'>
                                   <i class='fa fa-trash me-1'></i> Supprimer
                                </a>
                            </td>
                        </tr>
                        """
                        for item in culture
                    ])}
                </tbody>
            </table>
        </div>
    </section>
    """

    # MANAGE CUSTOM PAGES
    content_admin += f"""
    <section class="admin-section mb-5">
        <h2 class="mb-4">Gestion des Pages Personnalisées</h2>
        <div class="mb-3">
            <a href="/manage/add_page" class="btn btn-primary">
                <i class="fa fa-plus me-2"></i> Ajouter une page personnalisée
            </a>
        </div>
        <div class="table-responsive">
            <table class='table table-striped table-hover'>
                <thead class="table-warning">
                    <tr>
                        <th>Titre</th>
                        <th>URL</th>
                        <th>Méta Titre</th>
                        <th>Méta Description</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    {''.join([
                        f"""
                        <tr>
                            <td>{page['title']}</td>
                            <td>{page['url']}</td>
                            <td>{page.get('meta_title', '')}</td>
                            <td>{page.get('meta_description', '')}</td>
                            <td>
                                <a href='/manage/edit_page/{page['id']}' 
                                   class='btn btn-sm btn-warning'>
                                   <i class='fa fa-edit me-1'></i> Modifier
                                </a>
                                <a href='/manage/delete_page/{page['id']}' 
                                   class='btn btn-sm btn-danger btn-delete'>
                                   <i class='fa fa-trash me-1'></i> Supprimer
                                </a>
                            </td>
                        </tr>
                        """
                        for page in custom_pages
                    ])}
                </tbody>
            </table>
        </div>
    </section>
    """

    # MANAGE USERS
    content_admin += f"""
    <section class="admin-section mb-5">
        <h2 class="mb-4">Gestion des Utilisateurs</h2>
        <div class="mb-3">
            <a href="/manage/add_user" class="btn btn-primary">
                <i class="fa fa-user-plus me-2"></i> Ajouter un utilisateur
            </a>
        </div>
        <div class="table-responsive">
            <table class='table table-striped table-hover'>
                <thead class="table-warning">
                    <tr>
                        <th>Nom d'utilisateur</th>
                        <th>Rôle</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    {''.join([
                        f"""
                        <tr>
                            <td>{user['username']}</td>
                            <td>{user['role'].capitalize()}</td>
                            <td>
                                <a href='/manage/edit_user/{user['id']}' 
                                   class='btn btn-sm btn-warning'>
                                   <i class='fa fa-edit me-1'></i> Modifier
                                </a>
                                <a href='/manage/delete_user/{user['id']}' 
                                   class='btn btn-sm btn-danger btn-delete'>
                                   <i class='fa fa-trash me-1'></i> Supprimer
                                </a>
                            </td>
                        </tr>
                        """
                        for user in users
                        if user['role'] != 'admin'  # preventing the admin from being removed
                    ])}
                </tbody>
            </table>
        </div>
    </section>
    """

    # MANAGE CONTACT MESSAGES
    content_admin += f"""
    <section class="admin-section mb-5">
        <h2 class="mb-4">Boîte de Réception des Messages</h2>
        <div class="table-responsive">
            <table class='table table-striped table-hover'>
                <thead class="table-warning">
                    <tr>
                        <th>Nom</th>
                        <th>Email</th>
                        <th>Message</th>
                        <th>Lu</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    {''.join([
                        f"""
                        <tr>
                            <td>{msg['nom']}</td>
                            <td>{msg['email']}</td>
                            <td>{msg['message']}</td>
                            <td>{'Oui' if msg['lu'] else 'Non'}</td>
                            <td>
                                <a href="/manage/reply_message/{msg['id']}"
                                   class='btn btn-sm btn-primary'>
                                   <i class='fa fa-reply me-1'></i> Répondre
                                </a>
                                <a href="/manage/mark_message/{msg['id']}"
                                   class='btn btn-sm btn-info'>
                                   <i class='fa fa-eye me-1'></i> Marquer comme {'Non Lu' if msg['lu'] else 'Lu'}
                                </a>
                                <a href="/manage/delete_message/{msg['id']}"
                                   class='btn btn-sm btn-danger btn-delete'>
                                   <i class='fa fa-trash me-1'></i> Supprimer
                                </a>
                            </td>
                        </tr>
                        """
                        for msg in messages
                    ]) if messages else '<tr><td colspan="5" class="text-center">Aucun message reçu.</td></tr>'}
                </tbody>
            </table>
        </div>
    </section>
    """

    # SITE STATISTICS
    content_admin += f"""
    <section class="admin-section mb-5">
        <h2 class="mb-4">Statistiques du Site</h2>
        <div class="row">
            <div class="col-md-4">
                <div class="card text-white bg-primary mb-3 shadow dashboard-card">
                    <div class="card-header">
                        <i class="fa fa-map-marked-alt me-2"></i> Destinations
                    </div>
                    <div class="card-body">
                        <h5 class="card-title">{len(destinations)}</h5>
                        <p class="card-text">Nombre total de destinations.</p>
                    </div>
                </div>
            </div>
            <div class="col-md-4">
                <div class="card text-white bg-success mb-3 shadow dashboard-card">
                    <div class="card-header">
                        <i class="fa fa-book me-2"></i> Pages Personnalisées
                    </div>
                    <div class="card-body">
                        <h5 class="card-title">{len(custom_pages)}</h5>
                        <p class="card-text">Nombre total de pages personnalisées.</p>
                    </div>
                </div>
            </div>
            <div class="col-md-4">
                <div class="card text-white bg-warning mb-3 shadow dashboard-card">
                    <div class="card-header">
                        <i class="fa fa-users me-2"></i> Utilisateurs
                    </div>
                    <div class="card-body">
                        <h5 class="card-title">{len(users)}</h5>
                        <p class="card-text">Nombre total d'utilisateurs.</p>
                    </div>
                </div>
            </div>
        </div>
        <!-- Activity Log Chart -->
        <div class="card shadow">
            <div class="card-header">
                <h5 class="mb-0">
                    <i class="fa fa-chart-line me-2"></i> Journal d'Activité
                </h5>
            </div>
            <div class="card-body">
                <canvas id="activityChart" width="400" height="150"></canvas>
            </div>
        </div>
    </section>
    """

    # ACTIVITY LOG
    content_admin += f"""
    <section class="admin-section mb-5">
        <h2 class="mb-4">Journal d'Activité</h2>
        <div class="table-responsive">
            <table class='table table-striped table-hover'>
                <thead class="table-warning">
                    <tr>
                        <th>Utilisateur</th>
                        <th>Action</th>
                        <th>Timestamp</th>
                    </tr>
                </thead>
                <tbody>
                    {''.join([
                        f"""
                        <tr>
                            <td>{log['user']}</td>
                            <td>{log['action']}</td>
                            <td>{log['timestamp']}</td>
                        </tr>
                        """
                        for log in reversed(activity_logs[-10:])
                    ])}
                </tbody>
            </table>
        </div>
    </section>
    """

    # Build chart data
    activity_data = {}
    for log in activity_logs:
        act = log['action']
        activity_data[act] = activity_data.get(act, 0) + 1
    actions = list(activity_data.keys())
    counts = list(activity_data.values())

    content_admin += f"""
    <script>
        var ctx = document.getElementById('activityChart').getContext('2d');
        var activityChart = new Chart(ctx, {{
            type: 'bar',
            data: {{
                labels: {actions},
                datasets: [{{
                    label: '# d\'Actions',
                    data: {counts},
                    backgroundColor: 'rgba(54, 162, 235, 0.6)',
                    borderColor: 'rgba(54, 162, 235, 1)',
                    borderWidth: 1
                }}]
            }},
            options: {{
                scales: {{
                    y: {{
                        beginAtZero: true,
                        precision: 0
                    }}
                }}
            }}
        }});
    </script>
    """

    return render_page("Gestion", content_admin, active_page='Gestion')

###########################################################
#  7. Manage: Destinations
###########################################################

@app.route('/manage/add_destination', methods=['GET', 'POST'])
@login_required
def manage_add_destination():
    if session.get('role') != 'admin':
        flash('Accès refusé. Administrateur requis.', 'danger')
        return redirect(url_for('index'))

    uploaded_files = [
        f for f in os.listdir(UPLOAD_FOLDER)
        if os.path.isfile(os.path.join(UPLOAD_FOLDER, f))
    ]

    if request.method == 'POST':
        nom = request.form.get('nom').strip()
        description = request.form.get('description').strip()
        image = request.form.get('image')
        order = request.form.get('order').strip()

        if not nom or not description or not image or not order:
            flash('Veuillez remplir tous les champs.', 'danger')
            return redirect(url_for('manage_add_destination'))

        try:
            order_int = int(order)
        except ValueError:
            flash('L\'ordre doit être un nombre entier.', 'danger')
            return redirect(url_for('manage_add_destination'))

        destinations.append({
            "id": str(uuid.uuid4()),
            "nom": nom,
            "description": description,
            "image": image,
            "order": order_int
        })
        flash('La destination a été ajoutée avec succès!', 'success')
        activity_logs.append({
            "user": session['username'],
            "action": f"Ajouté destination: {nom}",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
        return redirect(url_for('manage'))

    content = f"""
    <section class="admin-section">
        <h2 class="mb-4">Ajouter une Destination</h2>
        <form method="post" class="row g-3">
            <div class="col-md-6">
                <label for="nom" class="form-label">Nom :</label>
                <input type="text" class="form-control" name="nom" id="nom" required>
            </div>
            <div class="col-md-6">
                <label for="order" class="form-label">Ordre d'affichage :</label>
                <input type="number" class="form-control" name="order" id="order" min="1" required>
            </div>
            <div class="col-12">
                <label for="description" class="form-label">Description :</label>
                <textarea class="form-control" name="description" id="description" rows="3" required></textarea>
            </div>
            <div class="col-12">
                <label for="image" class="form-label">Image :</label>
                <select class="form-select" name="image" id="image" required>
                    <option value="" disabled selected>Sélectionnez une image</option>
                    {''.join([
                        f'<option value="/static/uploads/{file}">{file}</option>'
                        for file in uploaded_files
                    ])}
                </select>
            </div>
            <div class="col-12">
                <button type="submit" class="btn btn-primary">
                    <i class="fa fa-plus me-2"></i> Ajouter
                </button>
            </div>
        </form>
    </section>
    """
    return render_page("Ajouter une Destination", content, active_page='Gestion')

@app.route('/manage/edit_destination/<string:destination_id>', methods=['GET', 'POST'])
@login_required
def manage_edit_destination(destination_id):
    if session.get('role') != 'admin':
        flash('Accès refusé. Administrateur requis.', 'danger')
        return redirect(url_for('index'))

    destination = next((d for d in destinations if d['id'] == destination_id), None)
    if not destination:
        flash('Destination non trouvée.', 'danger')
        return redirect(url_for('manage'))

    uploaded_files = [
        f for f in os.listdir(UPLOAD_FOLDER)
        if os.path.isfile(os.path.join(UPLOAD_FOLDER, f))
    ]

    if request.method == 'POST':
        nom = request.form.get('nom').strip()
        description = request.form.get('description').strip()
        image = request.form.get('image')
        order = request.form.get('order').strip()

        if not nom or not description or not image or not order:
            flash('Veuillez remplir tous les champs.', 'danger')
            return redirect(url_for('manage_edit_destination', destination_id=destination_id))

        try:
            order_int = int(order)
        except ValueError:
            flash('L\'ordre doit être un nombre entier.', 'danger')
            return redirect(url_for('manage_edit_destination', destination_id=destination_id))

        destination['nom'] = nom
        destination['description'] = description
        destination['image'] = image
        destination['order'] = order_int
        flash('La destination a été mise à jour avec succès!', 'success')
        activity_logs.append({
            "user": session['username'],
            "action": f"Modifié destination: {nom}",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
        return redirect(url_for('manage'))

    content = f"""
    <section class="admin-section">
        <h2 class="mb-4">Modifier la Destination: {destination['nom']}</h2>
        <form method="post" class="row g-3">
            <div class="col-md-6">
                <label for="nom" class="form-label">Nom :</label>
                <input type="text" class="form-control" name="nom" id="nom"
                       value="{destination['nom']}" required>
            </div>
            <div class="col-md-6">
                <label for="order" class="form-label">Ordre d'affichage :</label>
                <input type="number" class="form-control" name="order" id="order"
                       value="{destination['order']}" min="1" required>
            </div>
            <div class="col-12">
                <label for="description" class="form-label">Description :</label>
                <textarea class="form-control" name="description" id="description"
                          rows="3" required>{destination['description']}</textarea>
            </div>
            <div class="col-12">
                <label for="image" class="form-label">Image :</label>
                <select class="form-select" name="image" id="image" required>
                    <option value="" disabled>Sélectionnez une image</option>
                    {''.join([
                        f'<option value="/static/uploads/{file}" '
                        f'{"selected" if f"/static/uploads/{file}" == destination["image"] else ""}>'
                        f'{file}</option>'
                        for file in uploaded_files
                    ])}
                </select>
            </div>
            <div class="col-12">
                <button type="submit" class="btn btn-warning">
                    <i class="fa fa-save me-2"></i> Enregistrer
                </button>
            </div>
        </form>
    </section>
    """
    return render_page("Modifier une Destination", content, active_page='Gestion')

@app.route('/manage/delete_destination/<string:destination_id>', methods=['GET'])
@login_required
def manage_delete_destination(destination_id):
    if session.get('role') != 'admin':
        flash('Accès refusé. Administrateur requis.', 'danger')
        return redirect(url_for('index'))

    global destinations
    dest = next((d for d in destinations if d['id'] == destination_id), None)
    if dest:
        destinations = [d for d in destinations if d['id'] != destination_id]
        flash('La destination a été supprimée avec succès!', 'success')
        activity_logs.append({
            "user": session['username'],
            "action": f"Supprimé destination: {dest['nom']}",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
    else:
        flash('Destination non trouvée.', 'danger')
    return redirect(url_for('manage'))

###########################################################
#  8. Manage: Culture
###########################################################

@app.route('/manage/add_culture', methods=['GET', 'POST'])
@login_required
def manage_add_culture():
    if session.get('role') != 'admin':
        flash('Accès refusé. Administrateur requis.', 'danger')
        return redirect(url_for('index'))

    uploaded_files = [
        f for f in os.listdir(UPLOAD_FOLDER)
        if os.path.isfile(os.path.join(UPLOAD_FOLDER, f))
    ]

    if request.method == 'POST':
        nom = request.form.get('nom').strip()
        description = request.form.get('description').strip()
        image = request.form.get('image')

        if not nom or not description:
            flash('Veuillez remplir tous les champs.', 'danger')
            return redirect(url_for('manage_add_culture'))

        culture.append({
            "id": str(uuid.uuid4()),
            "nom": nom,
            "description": description,
            "image": image if image != 'None' else None
        })
        flash('L\'entrée culturelle a été ajoutée avec succès!', 'success')
        activity_logs.append({
            "user": session['username'],
            "action": f"Ajouté entrée culturelle: {nom}",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
        return redirect(url_for('manage'))

    content = f"""
    <section class="admin-section">
        <h2 class="mb-4">Ajouter une Entrée Culturelle</h2>
        <form method="post" class="row g-3">
            <div class="col-md-6">
                <label for="nom" class="form-label">Nom :</label>
                <input type="text" class="form-control" name="nom" id="nom" required>
            </div>
            <div class="col-md-6">
                <label for="image" class="form-label">Image :</label>
                <select class="form-select" name="image" id="image">
                    <option value="None" selected>Aucune image</option>
                    {''.join([
                        f'<option value="/static/uploads/{file}">{file}</option>'
                        for file in uploaded_files
                    ])}
                </select>
            </div>
            <div class="col-12">
                <label for="description" class="form-label">Description :</label>
                <textarea class="form-control" name="description" id="description"
                          rows="3" required></textarea>
            </div>
            <div class="col-12">
                <button type="submit" class="btn btn-primary">
                    <i class="fa fa-plus me-2"></i> Ajouter
                </button>
            </div>
        </form>
    </section>
    """
    return render_page("Ajouter une Entrée Culturelle", content, active_page='Gestion')

@app.route('/manage/edit_culture/<string:culture_id>', methods=['GET', 'POST'])
@login_required
def manage_edit_culture(culture_id):
    if session.get('role') != 'admin':
        flash('Accès refusé. Administrateur requis.', 'danger')
        return redirect(url_for('index'))

    item = next((c for c in culture if c['id'] == culture_id), None)
    if not item:
        flash('Entrée culturelle non trouvée.', 'danger')
        return redirect(url_for('manage'))

    uploaded_files = [
        f for f in os.listdir(UPLOAD_FOLDER)
        if os.path.isfile(os.path.join(UPLOAD_FOLDER, f))
    ]

    if request.method == 'POST':
        nom = request.form.get('nom').strip()
        description = request.form.get('description').strip()
        image = request.form.get('image')

        if not nom or not description:
            flash('Veuillez remplir tous les champs.', 'danger')
            return redirect(url_for('manage_edit_culture', culture_id=culture_id))

        item['nom'] = nom
        item['description'] = description
        item['image'] = image if image != 'None' else None
        flash('L\'entrée culturelle a été mise à jour avec succès!', 'success')
        activity_logs.append({
            "user": session['username'],
            "action": f"Modifié entrée culturelle: {nom}",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
        return redirect(url_for('manage'))

    content = f"""
    <section class="admin-section">
        <h2 class="mb-4">Modifier l'Entrée Culturelle: {item['nom']}</h2>
        <form method="post" class="row g-3">
            <div class="col-md-6">
                <label for="nom" class="form-label">Nom :</label>
                <input type="text" class="form-control" name="nom" id="nom"
                       value="{item['nom']}" required>
            </div>
            <div class="col-md-6">
                <label for="image" class="form-label">Image :</label>
                <select class="form-select" name="image" id="image">
                    <option value="None" {"selected" if not item['image'] else ""}>Aucune image</option>
                    {''.join([
                        f'<option value="/static/uploads/{file}" '
                        f'{"selected" if f"/static/uploads/{file}" == item["image"] else ""}>{file}</option>'
                        for file in uploaded_files
                    ])}
                </select>
            </div>
            <div class="col-12">
                <label for="description" class="form-label">Description :</label>
                <textarea class="form-control" name="description" id="description"
                          rows="3" required>{item['description']}</textarea>
            </div>
            <div class="col-12">
                <button type="submit" class="btn btn-warning">
                    <i class="fa fa-save me-2"></i> Enregistrer
                </button>
            </div>
        </form>
    </section>
    """
    return render_page("Modifier une Entrée Culturelle", content, active_page='Gestion')

@app.route('/manage/delete_culture/<string:culture_id>', methods=['GET'])
@login_required
def manage_delete_culture(culture_id):
    if session.get('role') != 'admin':
        flash('Accès refusé. Administrateur requis.', 'danger')
        return redirect(url_for('index'))

    global culture
    item = next((c for c in culture if c['id'] == culture_id), None)
    if item:
        culture = [c for c in culture if c['id'] != culture_id]
        flash('L\'entrée culturelle a été supprimée avec succès!', 'success')
        activity_logs.append({
            "user": session['username'],
            "action": f"Supprimé entrée culturelle: {item['nom']}",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
    else:
        flash('Entrée culturelle non trouvée.', 'danger')
    return redirect(url_for('manage'))

###########################################################
#  9. Manage: Media
###########################################################

@app.route('/manage/delete_uploaded_image/<string:filename>', methods=['GET'])
@login_required
def manage_delete_uploaded_image(filename):
    if session.get('role') != 'admin':
        flash('Accès refusé. Administrateur requis.', 'danger')
        return redirect(url_for('index'))

    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    try:
        os.remove(file_path)
        global homepage_media
        homepage_media = [
            m for m in homepage_media
            if m['path'] != f"/static/uploads/{filename}"
        ]
        flash(f'L\'image {filename} a été supprimée avec succès!', 'success')
        activity_logs.append({
            "user": session['username'],
            "action": f"Supprimé média uploadé: {filename}",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
    except FileNotFoundError:
        flash(f'L\'image {filename} n\'a pas été trouvée.', 'danger')
    return redirect(url_for('manage'))

@app.route('/manage/delete_homepage_media/<string:media_id>', methods=['GET'])
@login_required
def manage_delete_homepage_media(media_id):
    if session.get('role') != 'admin':
        flash('Accès refusé. Administrateur requis.', 'danger')
        return redirect(url_for('index'))

    global homepage_media
    md = next((m for m in homepage_media if m['id'] == media_id), None)
    if md:
        homepage_media = [m for m in homepage_media if m['id'] != media_id]
        flash('Le média a été supprimé de la page d\'accueil avec succès!', 'success')
        activity_logs.append({
            "user": session['username'],
            "action": f"Supprimé média d'accueil: {md['path']}",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
    else:
        flash('Média non trouvé.', 'danger')
    return redirect(url_for('manage'))

###########################################################
#  10. Manage: Custom Pages
###########################################################

@app.route('/manage/add_page', methods=['GET', 'POST'])
@login_required
def manage_add_page():
    if session.get('role') != 'admin':
        flash('Accès refusé. Administrateur requis.', 'danger')
        return redirect(url_for('index'))

    if request.method == 'POST':
        title = request.form.get('title').strip()
        url_slug = request.form.get('url').strip().lower().replace(' ', '-')
        content_txt = request.form.get('content').strip()
        meta_title = request.form.get('meta_title').strip()
        meta_description = request.form.get('meta_description').strip()

        if not title or not url_slug or not content_txt:
            flash('Veuillez remplir tous les champs obligatoires.', 'danger')
            return redirect(url_for('manage_add_page'))

        if any(p['url'] == url_slug for p in custom_pages):
            flash('Cette URL est déjà utilisée.', 'danger')
            return redirect(url_for('manage_add_page'))

        if not re.match(r'^[a-z0-9\-]+$', url_slug):
            flash(
                'L\'URL ne doit contenir que des lettres minuscules, des chiffres et des tirets.',
                'danger'
            )
            return redirect(url_for('manage_add_page'))

        custom_pages.append({
            "id": str(uuid.uuid4()),
            "title": title,
            "url": url_slug,
            "content": content_txt,
            "meta_title": meta_title,
            "meta_description": meta_description
        })
        flash('La page a été ajoutée avec succès!', 'success')
        activity_logs.append({
            "user": session['username'],
            "action": f"Ajouté page personnalisée: {title}",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
        return redirect(url_for('manage'))

    content = f"""
    <section class="admin-section">
        <h2 class="mb-4">Ajouter une Page Personnalisée</h2>
        <form method="post" class="row g-3">
            <div class="col-md-6">
                <label for="title" class="form-label">Titre <span class="text-danger">*</span>:</label>
                <input type="text" class="form-control" name="title" id="title" required>
            </div>
            <div class="col-md-6">
                <label for="url" class="form-label">URL <span class="text-danger">*</span>:</label>
                <input type="text" class="form-control" name="url" id="url" required>
                <div id="slugFeedback" class="invalid-feedback"></div>
            </div>
            <div class="col-md-6">
                <label for="meta_title" class="form-label">Méta Titre :</label>
                <input type="text" class="form-control" name="meta_title" id="meta_title"
                       placeholder="Titre pour le référencement">
            </div>
            <div class="col-md-6">
                <label for="meta_description" class="form-label">Méta Description :</label>
                <textarea class="form-control" name="meta_description" id="meta_description"
                          rows="3" placeholder="Description pour le référencement"></textarea>
            </div>
            <div class="col-12">
                <label for="content" class="form-label">Contenu <span class="text-danger">*</span>:</label>
                <textarea class="form-control" name="content" id="content" rows="10" required></textarea>
            </div>
            <div class="col-12">
                <button type="submit" class="btn btn-primary">
                    <i class="fa fa-plus me-2"></i> Ajouter
                </button>
            </div>
        </form>
        <div class="mt-3">
            <h5>Conseils pour inclure des médias :</h5>
            <ul>
                <li>
                    Pour ajouter une image (taille personnalisée) :
                    <code>&lt;img src="/static/uploads/votre_image.jpg" alt="Description" width="300"&gt;</code>
                </li>
                <li>
                    Pour ajouter une vidéo (taille personnalisée) :
                    <code>
                    &lt;video controls width="500"&gt;
                        &lt;source src="/static/uploads/votre_video.mp4" type="video/mp4"&gt;
                        Votre navigateur ne supporte pas les vidéos HTML5.
                    &lt;/video&gt;
                    </code>
                </li>
            </ul>
        </div>
        <script>CKEDITOR.replace('content');</script>
    </section>
    """
    return render_page("Ajouter une Page Personnalisée", content, active_page='Gestion')

@app.route('/manage/edit_page/<string:page_id>', methods=['GET', 'POST'])
@login_required
def manage_edit_page(page_id):
    if session.get('role') != 'admin':
        flash('Accès refusé. Administrateur requis.', 'danger')
        return redirect(url_for('index'))

    page = next((p for p in custom_pages if p['id'] == page_id), None)
    if not page:
        flash('Page non trouvée.', 'danger')
        return redirect(url_for('manage'))

    if request.method == 'POST':
        title = request.form.get('title').strip()
        url_slug = request.form.get('url').strip().lower().replace(' ', '-')
        content_txt = request.form.get('content').strip()
        meta_title = request.form.get('meta_title').strip()
        meta_description = request.form.get('meta_description').strip()

        if not title or not url_slug or not content_txt:
            flash('Veuillez remplir tous les champs obligatoires.', 'danger')
            return redirect(url_for('manage_edit_page', page_id=page_id))

        if any(p['url'] == url_slug and p['id'] != page_id for p in custom_pages):
            flash('Cette URL est déjà utilisée par une autre page.', 'danger')
            return redirect(url_for('manage_edit_page', page_id=page_id))

        if not re.match(r'^[a-z0-9\-]+$', url_slug):
            flash(
                'L\'URL ne doit contenir que des lettres minuscules, des chiffres et des tirets.',
                'danger'
            )
            return redirect(url_for('manage_edit_page', page_id=page_id))

        page['title'] = title
        page['url'] = url_slug
        page['content'] = content_txt
        page['meta_title'] = meta_title
        page['meta_description'] = meta_description
        flash('La page a été mise à jour avec succès!', 'success')
        activity_logs.append({
            "user": session['username'],
            "action": f"Modifié page personnalisée: {title}",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
        return redirect(url_for('manage'))

    content = f"""
    <section class="admin-section">
        <h2 class="mb-4">Modifier la Page: {page['title']}</h2>
        <form method="post" class="row g-3">
            <div class="col-md-6">
                <label for="title" class="form-label">
                    Titre <span class="text-danger">*</span>:
                </label>
                <input type="text" class="form-control" name="title" id="title"
                       value="{page['title']}" required>
            </div>
            <div class="col-md-6">
                <label for="url" class="form-label">
                    URL <span class="text-danger">*</span>:
                </label>
                <input type="text" class="form-control" name="url" id="url"
                       value="{page['url']}" required>
                <div id="slugFeedback" class="invalid-feedback"></div>
            </div>
            <div class="col-md-6">
                <label for="meta_title" class="form-label">Méta Titre :</label>
                <input type="text" class="form-control" name="meta_title" id="meta_title"
                       value="{page.get('meta_title', '')}"
                       placeholder="Titre pour le référencement">
            </div>
            <div class="col-md-6">
                <label for="meta_description" class="form-label">Méta Description :</label>
                <textarea class="form-control" name="meta_description" id="meta_description" rows="3"
                          placeholder="Description pour le référencement">{page.get('meta_description', '')}</textarea>
            </div>
            <div class="col-12">
                <label for="content" class="form-label">
                    Contenu <span class="text-danger">*</span>:
                </label>
                <textarea class="form-control" name="content" id="content"
                          rows="10" required>{page['content']}</textarea>
            </div>
            <div class="col-12">
                <button type="submit" class="btn btn-warning">
                    <i class="fa fa-save me-2"></i> Enregistrer
                </button>
            </div>
        </form>
        <div class="mt-3">
            <h5>Conseils pour inclure des médias :</h5>
            <ul>
                <li>
                    Pour ajouter une image :
                    <code>&lt;img src="/static/uploads/votre_image.jpg" alt="Description" width="300"&gt;</code>
                </li>
                <li>
                    Pour ajouter une vidéo :
                    <code>
                    &lt;video controls width="500"&gt;
                        &lt;source src="/static/uploads/votre_video.mp4" type="video/mp4"&gt;
                        Votre navigateur ne supporte pas les vidéos HTML5.
                    &lt;/video&gt;
                    </code>
                </li>
            </ul>
        </div>
        <script>CKEDITOR.replace('content');</script>
    </section>
    """
    return render_page("Modifier une Page Personnalisée", content, active_page='Gestion')

@app.route('/manage/delete_page/<string:page_id>', methods=['GET'])
@login_required
def manage_delete_page(page_id):
    if session.get('role') != 'admin':
        flash('Accès refusé. Administrateur requis.', 'danger')
        return redirect(url_for('index'))

    global custom_pages
    pg = next((p for p in custom_pages if p['id'] == page_id), None)
    if pg:
        custom_pages = [p for p in custom_pages if p['id'] != page_id]
        flash('La page a été supprimée avec succès!', 'success')
        activity_logs.append({
            "user": session['username'],
            "action": f"Supprimé page personnalisée: {pg['title']}",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
    else:
        flash('Page non trouvée.', 'danger')
    return redirect(url_for('manage'))

###########################################################
#  11. Manage: Users
###########################################################

@app.route('/manage/add_user', methods=['GET', 'POST'])
@login_required
def manage_add_user():
    if session.get('role') != 'admin':
        flash('Accès refusé. Administrateur requis.', 'danger')
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form.get('username').strip()
        password = request.form.get('password').strip()
        confirm_password = request.form.get('confirm_password').strip()
        role = request.form.get('role').strip()

        if not username or not password or not confirm_password or not role:
            flash('Veuillez remplir tous les champs.', 'danger')
            return redirect(url_for('manage_add_user'))

        if password != confirm_password:
            flash('Les mots de passe ne correspondent pas.', 'danger')
            return redirect(url_for('manage_add_user'))

        if any(u['username'] == username for u in users):
            flash('Ce nom d\'utilisateur est déjà pris.', 'danger')
            return redirect(url_for('manage_add_user'))

        hashed_password = generate_password_hash(password)
        users.append({
            "id": str(uuid.uuid4()),
            "username": username,
            "password": hashed_password,
            "role": role
        })
        flash('Utilisateur ajouté avec succès!', 'success')
        activity_logs.append({
            "user": session['username'],
            "action": f"Ajouté utilisateur: {username} avec rôle {role}",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
        return redirect(url_for('manage'))

    content = f"""
    <section class="admin-section">
        <h2 class="mb-4">Ajouter un Utilisateur</h2>
        <form method="post" class="row g-3">
            <div class="col-md-6">
                <label for="username" class="form-label">Nom d'utilisateur :</label>
                <input type="text" class="form-control" name="username" id="username" required>
            </div>
            <div class="col-md-6">
                <label for="role" class="form-label">Rôle :</label>
                <select class="form-select" name="role" id="role" required>
                    <option value="" disabled selected>Sélectionnez un rôle</option>
                    <option value="admin">Administrateur</option>
                    <option value="user">Utilisateur</option>
                </select>
            </div>
            <div class="col-md-6">
                <label for="password" class="form-label">Mot de passe :</label>
                <input type="password" class="form-control" name="password" id="password" required>
            </div>
            <div class="col-md-6">
                <label for="confirm_password" class="form-label">Confirmer le mot de passe :</label>
                <input type="password" class="form-control" name="confirm_password"
                       id="confirm_password" required>
            </div>
            <div class="col-12">
                <button type="submit" class="btn btn-primary">
                    <i class="fa fa-user-plus me-2"></i> Ajouter
                </button>
            </div>
        </form>
    </section>
    """
    return render_page("Ajouter un Utilisateur", content, active_page='Gestion')

@app.route('/manage/edit_user/<string:user_id>', methods=['GET', 'POST'])
@login_required
def manage_edit_user(user_id):
    if session.get('role') != 'admin':
        flash('Accès refusé. Administrateur requis.', 'danger')
        return redirect(url_for('index'))

    user = next((u for u in users if u['id'] == user_id), None)
    if not user:
        flash('Utilisateur non trouvé.', 'danger')
        return redirect(url_for('manage'))

    if request.method == 'POST':
        username = request.form.get('username').strip()
        role = request.form.get('role').strip()
        password = request.form.get('password').strip()
        confirm_password = request.form.get('confirm_password').strip()

        if not username or not role:
            flash('Veuillez remplir tous les champs obligatoires.', 'danger')
            return redirect(url_for('manage_edit_user', user_id=user_id))

        if password and password != confirm_password:
            flash('Les mots de passe ne correspondent pas.', 'danger')
            return redirect(url_for('manage_edit_user', user_id=user_id))

        if username != user['username'] and any(u['username'] == username for u in users):
            flash('Ce nom d\'utilisateur est déjà pris.', 'danger')
            return redirect(url_for('manage_edit_user', user_id=user_id))

        user['username'] = username
        user['role'] = role
        if password:
            user['password'] = generate_password_hash(password)
        flash('Utilisateur mis à jour avec succès!', 'success')
        activity_logs.append({
            "user": session['username'],
            "action": f"Modifié utilisateur: {username} avec rôle {role}",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
        return redirect(url_for('manage'))

    content = f"""
    <section class="admin-section">
        <h2 class="mb-4">Modifier l'Utilisateur: {user['username']}</h2>
        <form method="post" class="row g-3">
            <div class="col-md-6">
                <label for="username" class="form-label">Nom d'utilisateur :</label>
                <input type="text" class="form-control" name="username" id="username"
                       value="{user['username']}" required>
            </div>
            <div class="col-md-6">
                <label for="role" class="form-label">Rôle :</label>
                <select class="form-select" name="role" id="role" required>
                    <option value="admin" {"selected" if user['role'] == 'admin' else ""}>
                        Administrateur
                    </option>
                    <option value="user" {"selected" if user['role'] == 'user' else ""}>
                        Utilisateur
                    </option>
                </select>
            </div>
            <div class="col-md-6">
                <label for="password" class="form-label">Nouveau Mot de passe :</label>
                <input type="password" class="form-control" name="password" id="password"
                       placeholder="Laissez vide pour ne pas changer">
            </div>
            <div class="col-md-6">
                <label for="confirm_password" class="form-label">Confirmer le nouveau mot de passe :</label>
                <input type="password" class="form-control" name="confirm_password"
                       id="confirm_password" placeholder="Confirmez le nouveau mot de passe">
            </div>
            <div class="col-12">
                <button type="submit" class="btn btn-warning">
                    <i class="fa fa-save me-2"></i> Enregistrer
                </button>
            </div>
        </form>
    </section>
    """
    return render_page("Modifier un Utilisateur", content, active_page='Gestion')

@app.route('/manage/delete_user/<string:user_id>', methods=['GET'])
@login_required
def manage_delete_user(user_id):
    if session.get('role') != 'admin':
        flash('Accès refusé. Administrateur requis.', 'danger')
        return redirect(url_for('index'))

    global users
    usr = next((u for u in users if u['id'] == user_id), None)
    if usr and usr['role'] != 'admin':
        users = [u for u in users if u['id'] != user_id]
        flash('L\'utilisateur a été supprimé avec succès!', 'success')
        activity_logs.append({
            "user": session['username'],
            "action": f"Supprimé utilisateur: {usr['username']}",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
    else:
        flash('Utilisateur non trouvé ou impossible de supprimer un administrateur.', 'danger')
    return redirect(url_for('manage'))

###########################################################
#  12. Manage: Contact Messages
###########################################################

@app.route('/manage/delete_message/<string:message_id>', methods=['GET'])
@login_required
def manage_delete_message(message_id):
    if session.get('role') != 'admin':
        flash('Accès refusé. Administrateur requis.', 'danger')
        return redirect(url_for('index'))

    global messages
    msg = next((m for m in messages if m['id'] == message_id), None)
    if msg:
        messages = [m for m in messages if m['id'] != message_id]
        flash('Le message a été supprimé avec succès!', 'success')
        activity_logs.append({
            "user": session['username'],
            "action": f"Supprimé message de: {msg['nom']}",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
    else:
        flash('Message non trouvé.', 'danger')
    return redirect(url_for('manage'))

@app.route('/manage/mark_message/<string:message_id>', methods=['GET'])
@login_required
def manage_mark_message(message_id):
    if session.get('role') != 'admin':
        flash('Accès refusé. Administrateur requis.', 'danger')
        return redirect(url_for('index'))

    msg = next((m for m in messages if m['id'] == message_id), None)
    if msg:
        msg['lu'] = not msg['lu']
        flash(f"Le message a été marqué comme {'lu' if msg['lu'] else 'non lu'}.", 'success')
        activity_logs.append({
            "user": session['username'],
            "action": f"Marqué message de: {msg['nom']} comme {'lu' if msg['lu'] else 'non lu'}",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
    else:
        flash('Message non trouvé.', 'danger')
    return redirect(url_for('manage'))

@app.route('/manage/reply_message/<string:message_id>', methods=['GET', 'POST'])
@login_required
def manage_reply_message(message_id):
    if session.get('role') != 'admin':
        flash('Accès refusé. Administrateur requis.', 'danger')
        return redirect(url_for('index'))

    msg_obj = next((m for m in messages if m['id'] == message_id), None)
    if not msg_obj:
        flash('Message non trouvé.', 'danger')
        return redirect(url_for('manage'))

    if request.method == 'POST':
        reply_body = request.form.get('reply').strip()
        if not reply_body:
            flash('Le message de réponse ne peut pas être vide.', 'danger')
            return redirect(url_for('manage_reply_message', message_id=message_id))

        try:
            msg_email = Message(
                subject="Réponse à votre message",
                recipients=[msg_obj['email']],
                body=(
                    f"Bonjour {msg_obj['nom']},\n\n"
                    f"{reply_body}\n\n"
                    f"Cordialement,\nL'équipe de Tourisme Niger"
                )
            )
            mail.send(msg_email)
            flash('Réponse envoyée avec succès!', 'success')
            msg_obj['lu'] = True
            activity_logs.append({
                "user": session['username'],
                "action": f"Répondu au message de: {msg_obj['nom']}",
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
            return redirect(url_for('manage'))
        except Exception as e:
            flash(f'Erreur lors de l\'envoi de l\'email: {str(e)}', 'danger')
            return redirect(url_for('manage_reply_message', message_id=message_id))

    content = f"""
    <section class="admin-section">
        <h2 class="mb-4">Répondre au Message de {msg_obj['nom']}</h2>
        <form method="post" class="row g-3">
            <div class="col-12">
                <label for="email" class="form-label">Email :</label>
                <input type="email" class="form-control" id="email"
                       value="{msg_obj['email']}" disabled>
            </div>
            <div class="col-12">
                <label for="reply" class="form-label">Votre Réponse :</label>
                <textarea class="form-control" name="reply" id="reply"
                          rows="6" required></textarea>
            </div>
            <div class="col-12">
                <button type="submit" class="btn btn-primary">
                    <i class="fa fa-paper-plane me-2"></i> Envoyer la Réponse
                </button>
                <a href="/manage" class="btn btn-secondary">
                    <i class="fa fa-times me-2"></i> Annuler
                </a>
            </div>
        </form>
    </section>
    """
    return render_page("Répondre au Message", content, active_page='Gestion')

###########################################################
#  13. Custom Pages Routes
###########################################################

@app.route('/pages/<string:page_url>')
def custom_page_route(page_url):
    page = next((p for p in custom_pages if p['url'] == page_url), None)
    if not page:
        raise NotFound()

    return render_page(
        page['title'],
        f"""
        <section class="page-personnalisee">
            <h2 class="mb-4">{page['title']}</h2>
            <div class="content">
                {page['content']}
            </div>
        </section>
        """,
        active_page=page['title']
    )

###########################################################
#  14. Error Handling
###########################################################

@app.errorhandler(NotFound)
def page_not_found(error):
    return (
        render_page(
            "Page Non Trouvée",
            f"""
            <section class="text-center">
                <h2 class="display-4 text-danger">Erreur 404 - Page Non Trouvée</h2>
                <p class="lead">La page que vous recherchez n'existe pas.</p>
                <a href="/" class="btn btn-primary">
                    <i class="fa fa-home me-2"></i> Retour à l'accueil
                </a>
            </section>
            """,
            active_page=None
        ),
        404
    )

###########################################################
#  15. Run the Application
###########################################################
if __name__ == '__main__':
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    # app.run(debug=True)  # In production, turn debug=False or use a WSGI server
    app.run(debug=True)
