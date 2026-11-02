"""
Fabrique le site d'Arthur Brac de la Perrière.

Ce script lit les textes du dossier « contenu » (modifiables avec Pages CMS),
les place dans les modèles du dossier « modeles », optimise les photos du
dossier « medias », et écrit le site final dans le dossier « _site ».

GitHub le lance automatiquement à chaque modification (voir .github/workflows).
Pour le lancer à la main : python3 build.py
"""

import datetime
import pathlib
import re
import shutil

import markdown as md_lib
import yaml
from jinja2 import Environment, FileSystemLoader, select_autoescape
from markupsafe import Markup
from PIL import Image, ImageOps

RACINE = pathlib.Path(__file__).parent
SORTIE = RACINE / "_site"
URL_SITE = "https://arthurbrac.fr"


# ---------------------------------------------------------------- outils texte

def typo(html: str) -> str:
    """Espaces insécables de la typographie française (hors balises)."""
    morceaux = re.split(r"(<[^>]+>)", html)
    for i, m in enumerate(morceaux):
        if m.startswith("<"):
            continue
        m = re.sub(r" ([:;!?»])", " \\1", m)
        m = m.replace("« ", "« ")
        morceaux[i] = m
    return "".join(morceaux)


def md(texte) -> Markup:
    """Texte avec mise en forme simple (*italique*, **gras**, [lien](url), paragraphes)."""
    if not texte:
        return Markup("")
    html = md_lib.markdown(str(texte).strip())
    return Markup(typo(html))


def md_ligne(texte) -> Markup:
    """Comme md(), mais sans paragraphe autour (pour un titre ou une légende)."""
    html = str(md(texte))
    html = re.sub(r"^<p>(.*)</p>$", r"\1", html.strip(), flags=re.S)
    return Markup(html)


def poeme(texte) -> Markup:
    """Poème : garde les retours à la ligne, une ligne vide sépare les strophes."""
    if not texte:
        return Markup("")
    strophes = re.split(r"\n\s*\n", str(texte).strip())
    html = "".join(
        "<p>" + "<br>".join(str(Markup.escape(l.strip())) for l in s.splitlines()) + "</p>"
        for s in strophes)
    return Markup(typo(html))


# ---------------------------------------------------------------- photos

_cache_images = {}


def img(chemin, largeurs=(480, 960), qualite=78):
    """
    Optimise une photo du dossier medias en WebP, en plusieurs tailles.
    Renvoie src, srcset, largeur et hauteur pour la balise <img>.
    """
    if not chemin:
        return None
    cle = (chemin, tuple(largeurs))
    if cle in _cache_images:
        return _cache_images[cle]
    source = RACINE / chemin.lstrip("/")
    if not source.exists():
        print(f"  ATTENTION : photo introuvable : {chemin}")
        return None
    im = ImageOps.exif_transpose(Image.open(source)).convert("RGB")
    base = source.stem
    dossier = SORTIE / "medias" / "auto"
    dossier.mkdir(parents=True, exist_ok=True)
    variantes = []
    for w in largeurs:
        w = min(w, im.width)
        h = round(im.height * w / im.width)
        nom = f"{base}-{w}.webp"
        cible = dossier / nom
        if not cible.exists() or cible.stat().st_mtime < source.stat().st_mtime:
            im.resize((w, h), Image.LANCZOS).save(cible, "WEBP", quality=qualite, method=6)
        variantes.append((f"/medias/auto/{nom}", w, h))
    grande = variantes[-1]
    resultat = {
        "src": grande[0],
        "srcset": ", ".join(f"{u} {w}w" for u, w, _ in dict.fromkeys(variantes)),
        "largeur": grande[1],
        "hauteur": grande[2],
    }
    _cache_images[cle] = resultat
    return resultat


# ---------------------------------------------------------------- fabrication

def charger(nom):
    fichier = RACINE / "contenu" / f"{nom}.yml"
    with open(fichier, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


PAGES = [
    # (modèle, adresse de sortie, page active dans le menu)
    ("accueil.html", "index.html", ""),
    ("conferences.html", "conferences/index.html", "conferences"),
    ("livres.html", "livres/index.html", "livres"),
    ("apropos.html", "a-propos/index.html", "a-propos"),
    ("presse.html", "presse/index.html", "presse"),
    ("contact.html", "contact/index.html", "contact"),
    ("mentions.html", "mentions-legales/index.html", "mentions"),
    ("404.html", "404.html", ""),
]


def main():
    if SORTIE.exists():
        # on garde les photos déjà optimisées pour aller plus vite
        for p in SORTIE.iterdir():
            if p.name != "medias":
                shutil.rmtree(p) if p.is_dir() else p.unlink()
    SORTIE.mkdir(exist_ok=True)

    env = Environment(
        loader=FileSystemLoader(RACINE / "modeles"),
        autoescape=select_autoescape(["html"]),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    env.filters["md"] = md
    env.filters["md_ligne"] = md_ligne
    env.filters["poeme"] = poeme
    env.filters["typo"] = lambda t: Markup(typo(str(Markup.escape(t)))) if t else ""
    env.globals["img"] = img
    env.globals["url_site"] = URL_SITE
    env.globals["annee"] = datetime.date.today().year

    donnees = {
        "site": charger("site"),
        "accueil": charger("accueil"),
        "conferences": charger("conferences"),
        "temoignages": charger("temoignages").get("temoignages", []),
        "livres": charger("livres"),
        "apropos": charger("apropos"),
        "presse": charger("presse"),
        "contact": charger("contact"),
        "mentions": charger("mentions"),
    }
    pages = list(PAGES)
    for livre in donnees["livres"].get("livres", []):
        if livre.get("page_detaillee"):
            pages.append(("livre.html", f"livres/{livre['adresse']}/index.html", "livres", livre))

    adresses = []
    for modele, sortie, actif, *extra in pages:
        html = env.get_template(modele).render(actif=actif, livre=(extra[0] if extra else None), **donnees)
        cible = SORTIE / sortie
        cible.parent.mkdir(parents=True, exist_ok=True)
        cible.write_text(html, encoding="utf-8")
        if sortie != "404.html":
            adresses.append("/" + sortie.replace("index.html", ""))
        print(f"  page fabriquée : /{sortie}")

    # fichiers fixes : styles, polices, icônes, documents
    shutil.copytree(RACINE / "assets", SORTIE / "assets")
    # photos haute définition proposées au téléchargement (page Presse)
    for p in donnees["presse"].get("photos_hd", []):
        source = RACINE / p["photo"].lstrip("/")
        if source.exists():
            cible = SORTIE / p["photo"].lstrip("/")
            cible.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(source, cible)
    if (RACINE / "medias" / "documents").exists():
        shutil.copytree(RACINE / "medias" / "documents", SORTIE / "medias" / "documents", dirs_exist_ok=True)
    for fixe in ("CNAME",):
        if (RACINE / fixe).exists():
            shutil.copy(RACINE / fixe, SORTIE / fixe)

    # plan du site pour Google
    aujourdhui = datetime.date.today().isoformat()
    lignes = [f"  <url><loc>{URL_SITE}{a}</loc><lastmod>{aujourdhui}</lastmod></url>" for a in adresses]
    (SORTIE / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "\n".join(lignes) + "\n</urlset>\n", encoding="utf-8")
    (SORTIE / "robots.txt").write_text(
        f"User-agent: *\nAllow: /\n\nSitemap: {URL_SITE}/sitemap.xml\n", encoding="utf-8")
    print("Site prêt dans le dossier _site")


if __name__ == "__main__":
    main()
