"""Render the website's HTML pages from content.json."""
import html
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONTENT_FILE = os.path.join(ROOT, "content.json")

PAGES = ["index", "about", "experience", "publications", "projects", "hobbies", "ai-gallery", "tcg-blog"]


def t(s):
    """Text that may contain inline HTML; only bare ampersands are escaped."""
    return re.sub(r"&(?![a-zA-Z#][a-zA-Z0-9]*;)", "&amp;", s or "")


def a(s):
    """Attribute value."""
    return html.escape(s or "", quote=True)


def paragraphs(text, cls=""):
    cls_attr = f' class="{cls}"' if cls else ""
    parts = [p.strip() for p in re.split(r"\n\s*\n", text or "") if p.strip()]
    return "\n".join(f"          <p{cls_attr}>\n            {t(p)}\n          </p>" for p in parts)


def tags(items, cls="tag"):
    return "".join(f'<span class="{cls}">{t(x)}</span>' for x in items)


def head(site, meta, page_file):
    url = site["base_url"] + ("" if page_file == "index.html" else page_file)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <script>const t=localStorage.getItem('theme');if(t)document.documentElement.setAttribute('data-theme',t);document.documentElement.classList.add('js');</script>
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta name="description" content="{a(meta['description'])}">
  <title>{t(meta['title'])}</title>
  <link rel="icon" href="favicon.svg" type="image/svg+xml">
  <meta name="theme-color" content="#09090b">
  <meta property="og:type" content="website">
  <meta property="og:site_name" content="{a(site['name'])}">
  <meta property="og:title" content="{a(meta.get('og_title') or meta['title'])}">
  <meta property="og:description" content="{a(meta.get('og_description') or meta['description'])}">
  <meta property="og:url" content="{a(url)}">
  <meta property="og:image" content="{a(site['base_url'] + 'og-image.jpg')}">
  <meta property="og:image:width" content="1200">
  <meta property="og:image:height" content="630">
  <meta name="twitter:card" content="summary_large_image">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="style.css">
</head>
<body>
"""


NAV_ITEMS = [("about.html", "About"), ("experience.html", "Experience"), ("publications.html", "Publications"),
             ("projects.html", "Projects"), ("hobbies.html", "Hobbies")]


def nav(site, active):
    links = ""
    for href, label in NAV_ITEMS:
        cls = ' class="nav-active"' if href == active else ""
        links += f'        <li><a href="{href}"{cls}>{label}</a></li>\n'
    return f"""
  <nav id="navbar">
    <div class="nav-container">
      <a href="index.html" class="nav-logo">{t(site['initials'])}</a>
      <ul class="nav-links" id="nav-links">
{links}        <li><a href="#contact" class="nav-cta">Contact</a></li>
      </ul>
      <button class="theme-toggle" id="theme-toggle" aria-label="Switch to light mode">☀</button>
      <button class="nav-toggle" id="nav-toggle" aria-label="Toggle navigation">
        <span></span><span></span><span></span>
      </button>
    </div>
  </nav>

  <main>
"""


def footer(site, extra_scripts=""):
    return f"""
  </main>

  <footer id="contact">
    <div class="container">
      <div class="footer-top">
        <div class="footer-info">
          <span class="footer-name">{t(site['name'])}</span>
          <span class="footer-loc">{t(site['location'])}</span>
        </div>
        <div class="footer-links">
          <a href="mailto:{a(site['email'])}">Email</a>
          <a href="{a(site['github'])}" target="_blank" rel="noopener">GitHub</a>
          <a href="{a(site['linkedin'])}" target="_blank" rel="noopener">LinkedIn</a>
          <a href="{a(site['scholar'])}" target="_blank" rel="noopener">Scholar</a>
          <a href="{a(site['cv_file'])}" target="_blank" rel="noopener">CV</a>
        </div>
      </div>
      <p class="footer-copy">&copy; {t(str(site['copyright_year']))} {t(site['name'])}</p>
    </div>
  </footer>

  <script src="script.js"></script>
{extra_scripts}</body>
</html>
"""


def page_hero(back_href, back_label, label, title, desc):
    return f"""
    <section class="page-hero">
      <div class="container">
        <a href="{back_href}" class="back-link">&larr; {t(back_label)}</a>
        <span class="hero-label">{t(label)}</span>
        <h1 class="page-title">{t(title)}</h1>
        <p class="page-desc">{t(desc)}</p>
      </div>
    </section>
"""


GITHUB_ICON = '<svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor" aria-hidden="true"><path d="M12 .297c-6.63 0-12 5.373-12 12 0 5.303 3.438 9.8 8.205 11.385.6.113.82-.258.82-.577 0-.285-.01-1.04-.015-2.04-3.338.724-4.042-1.61-4.042-1.61C4.422 18.07 3.633 17.7 3.633 17.7c-1.087-.744.084-.729.084-.729 1.205.084 1.838 1.236 1.838 1.236 1.07 1.835 2.809 1.305 3.495.998.108-.776.417-1.305.76-1.605-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23A11.509 11.509 0 0 1 12 5.803c1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222 0 1.606-.014 2.898-.014 3.293 0 .322.216.694.825.576C20.565 22.092 24 17.592 24 12.297c0-6.627-5.373-12-12-12"/></svg>'
LINKEDIN_ICON = '<svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor" aria-hidden="true"><path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433a2.062 2.062 0 0 1-2.063-2.065 2.064 2.064 0 1 1 2.063 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z"/></svg>'
SCHOLAR_ICON = '<svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor" aria-hidden="true"><path d="M5.242 13.769L0 9.5 12 0l12 9.5-5.242 4.269C17.548 11.249 14.978 9.5 12 9.5c-2.977 0-5.548 1.748-6.758 4.269zM12 10a7 7 0 1 0 0 14 7 7 0 0 0 0-14z"/></svg>'

HOBBY_ICONS = {
    "image": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="3" y="3" width="18" height="18" rx="2"/><circle cx="9" cy="9" r="2"/><path d="m21 15-3.086-3.086a2 2 0 0 0-2.828 0L6 21"/></svg>',
    "book": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 7v14"/><path d="M3 18a1 1 0 0 1-1-1V4a1 1 0 0 1 1-1h5a4 4 0 0 1 4 4 4 4 0 0 1 4-4h5a1 1 0 0 1 1 1v13a1 1 0 0 1-1 1h-6a3 3 0 0 0-3 3 3 3 0 0 0-3-3z"/></svg>',
    "layers": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="m12.83 2.18a2 2 0 0 0-1.66 0L2.6 6.08a1 1 0 0 0 0 1.83l8.58 3.91a2 2 0 0 0 1.66 0l8.58-3.9a1 1 0 0 0 0-1.83Z"/><path d="m22 17.65-9.17 4.16a2 2 0 0 1-1.66 0L2 17.65"/><path d="m22 12.65-9.17 4.16a2 2 0 0 1-1.66 0L2 12.65"/></svg>',
}


def render_index(c):
    site, home = c["site"], c["home"]
    name_html = "<br>".join(t(line.strip()) for line in home["hero_name"].split("\n") if line.strip())
    photo_webp = site.get("photo_webp")
    webp_source = f'                <source srcset="{a(photo_webp)}" type="image/webp">\n' if photo_webp and os.path.exists(os.path.join(ROOT, photo_webp)) else ""

    exp_items = ""
    for e in [x for x in c["experience"]["research"] if x.get("featured")]:
        exp_items += f"""          <div class="exp-preview-item">
            <div class="exp-preview-left">
              <span class="exp-preview-role">{t(e['role'])}</span>
              <span class="exp-preview-org">{t(e.get('org_short') or e['org'])}</span>
            </div>
            <span class="exp-preview-date">{t(e['date'])}</span>
          </div>
"""

    pub_items = ""
    for p in [x for x in c["publications"]["papers"] if x.get("featured")]:
        pub_items += f"""          <li class="pub-preview-item">
            <span class="pub-preview-title">{t(p['title'])}</span>
            <span class="pub-preview-venue">{t(p.get('venue_short') or p['venue'])}</span>
          </li>
"""

    proj_items = ""
    for p in [x for x in c["projects"]["items"] if x.get("featured")]:
        proj_items += f"""          <li class="pub-preview-item">
            <span class="pub-preview-title">{t(p['title'])}</span>
            <span class="pub-preview-venue">{t(p['label'])}</span>
          </li>
"""

    hobby_cards = ""
    for card in home["hobby_cards"]:
        hobby_cards += f"""          <a href="{a(card['link'])}" class="hobby-card">
            <span class="hobby-card-icon">{HOBBY_ICONS.get(card.get('icon', 'image'), HOBBY_ICONS['image'])}</span>
            <span class="hobby-card-title">{t(card['title'])}</span>
            <span class="hobby-card-desc">{t(card['desc'])}</span>
          </a>
"""

    body = f"""
    <!-- Hero -->
    <section id="hero">
      <div class="hero-glow"></div>
      <div class="container">
        <div class="hero-content">
          <span class="hero-label">{t(home['hero_label'])}</span>
          <div class="hero-main">
            <div class="hero-text">
              <h1 class="hero-name">{name_html}</h1>
              <p class="hero-bio">
                {t(home['hero_bio'])}
              </p>
              <div class="hero-actions">
                <a href="mailto:{a(site['email'])}" class="btn btn-primary">Get in touch</a>
                <a href="{a(site['cv_file'])}" class="btn btn-secondary" target="_blank" rel="noopener">Download CV</a>
                <div class="social-links">
                  <a href="{a(site['github'])}" class="icon-btn" target="_blank" rel="noopener" aria-label="GitHub">
                    {GITHUB_ICON}
                  </a>
                  <a href="{a(site['linkedin'])}" class="icon-btn" target="_blank" rel="noopener" aria-label="LinkedIn">
                    {LINKEDIN_ICON}
                  </a>
                  <a href="{a(site['scholar'])}" class="icon-btn" target="_blank" rel="noopener" aria-label="Google Scholar">
                    {SCHOLAR_ICON}
                  </a>
                </div>
              </div>
            </div>
            <div class="hero-photo">
              <picture>
{webp_source}                <img src="{a(site['photo'])}" alt="{a(site['name'])}" class="hero-img" width="150" height="150">
              </picture>
            </div>
          </div>
        </div>
      </div>
      <a href="#about-preview" class="scroll-cue" aria-label="Scroll to content">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="m6 9 6 6 6-6"/></svg>
      </a>
    </section>

    <!-- About preview -->
    <section id="about-preview">
      <div class="container">
        <div class="preview-header">
          <h2 class="section-title">About</h2>
          <a href="about.html" class="view-all">More about me &rarr;</a>
        </div>
        <p class="preview-text">
          {t(home['about_text'])}
        </p>
        <div class="preview-tags">
          {tags(home['about_tags'])}
        </div>
      </div>
    </section>

    <!-- Experience preview -->
    <section id="experience-preview" class="surface-section">
      <div class="container">
        <div class="preview-header">
          <h2 class="section-title">Experience</h2>
          <a href="experience.html" class="view-all">Full history &rarr;</a>
        </div>
        <div class="exp-preview-list">
{exp_items}        </div>
      </div>
    </section>

    <!-- Publications preview -->
    <section id="publications-preview">
      <div class="container">
        <div class="preview-header">
          <h2 class="section-title">Publications</h2>
          <a href="publications.html" class="view-all">View all &rarr;</a>
        </div>
        <ul class="pub-preview-list">
{pub_items}        </ul>
      </div>
    </section>

    <!-- Projects preview -->
    <section id="projects-preview" class="surface-section">
      <div class="container">
        <div class="preview-header">
          <h2 class="section-title">Projects</h2>
          <a href="projects.html" class="view-all">View projects &rarr;</a>
        </div>
        <p class="section-sub">{t(home['projects_intro'])}</p>
        <ul class="pub-preview-list">
{proj_items}        </ul>
      </div>
    </section>

    <!-- Hobbies preview -->
    <section id="hobbies-preview">
      <div class="container">
        <div class="preview-header">
          <h2 class="section-title">Hobbies</h2>
          <a href="hobbies.html" class="view-all">Explore &rarr;</a>
        </div>
        <div class="hobby-cards">
{hobby_cards}        </div>
      </div>
    </section>
"""
    return head(site, home["meta"], "index.html") + nav(site, None) + body + footer(site)


def render_about(c):
    site, ab = c["site"], c["about"]
    groups = ""
    for g in ab["skills"]:
        groups += f"""          <div class="skill-group">
            <h4 class="skill-group-label">{t(g['label'])}</h4>
            <div class="skill-tags">
              {tags(g['tags'])}
            </div>
          </div>
"""
    body = page_hero("index.html", "Home", ab["hero_label"], ab["title"], ab["desc"]) + f"""
    <section>
      <div class="container">
        <h2 class="section-title">Bio</h2>
        <div class="about-content">
{paragraphs(ab['bio'])}
        </div>
      </div>
    </section>

    <section class="surface-section">
      <div class="container">
        <h2 class="section-title">Skills</h2>
        <div class="skills-grid">
{groups}        </div>
      </div>
    </section>
"""
    return head(site, ab["meta"], "about.html") + nav(site, "about.html") + body + footer(site)


def timeline(items, title_key, org_key):
    out = ""
    for it in items:
        bullets = "".join(f"              <li>{t(b)}</li>\n" for b in it.get("bullets", []))
        out += f"""          <div class="timeline-item">
            <div class="timeline-header">
              <div>
                <h3>{t(it[title_key])}</h3>
                <span class="timeline-org">{t(it[org_key])}</span>
              </div>
              <span class="timeline-date">{t(it['date'])}</span>
            </div>
            <ul class="timeline-bullets">
{bullets}            </ul>
          </div>

"""
    return out


def render_experience(c):
    site, ex = c["site"], c["experience"]
    edu = ""
    for e in ex["education"]:
        grade = f'\n            <div class="edu-grade">{t(e["grade"])}</div>' if e.get("grade") else ""
        edu += f"""          <div class="edu-card">
            <div class="edu-degree">{t(e['degree'])}</div>
            <div class="edu-institution">{t(e['institution'])}</div>
            <div class="edu-year">{t(e['year'])}</div>{grade}
          </div>
"""
    body = page_hero("index.html", "Home", ex["hero_label"], ex["title"], ex["desc"]) + f"""
    <section>
      <div class="container">
        <h2 class="section-title">Research Experience</h2>
        <div class="timeline">

{timeline(ex['research'], 'role', 'org')}        </div>
      </div>
    </section>

    <section class="surface-section">
      <div class="container">
        <h2 class="section-title">Education</h2>
        <div class="edu-grid">
{edu}        </div>
      </div>
    </section>

    <section>
      <div class="container">
        <h2 class="section-title">Courses &amp; Training</h2>
        <div class="timeline">

{timeline(ex['courses'], 'name', 'org')}        </div>
      </div>
    </section>
"""
    return head(site, ex["meta"], "experience.html") + nav(site, "experience.html") + body + footer(site)


def render_publications(c):
    site, pb = c["site"], c["publications"]
    papers = ""
    for p in pb["papers"]:
        authors = t(p["authors"]).replace(t(site["author_short"]), f"<strong>{t(site['author_short'])}</strong>")
        doi = f' &middot; <a href="https://doi.org/{a(p["doi"])}" target="_blank" rel="noopener">doi:{t(p["doi"])}</a>' if p.get("doi") else ""
        papers += f"""          <li class="pub-item">
            <p class="pub-title">{t(p['title'])}</p>
            <p class="pub-authors">{authors}</p>
            <p class="pub-venue">{t(p['venue'])}{doi}</p>
          </li>

"""
    talks = ""
    for k in pb["talks"]:
        talks += f"""          <div class="conf-item">
            <div class="conf-header">
              <span class="conf-title">{t(k['title'])}</span>
              <span class="conf-year">{t(k['year'])}</span>
            </div>
            <span class="conf-venue">{t(k['venue'])}</span>
          </div>

"""
    body = page_hero("index.html", "Home", pb["hero_label"], pb["title"], pb["desc"]) + f"""
    <section>
      <div class="container">
        <h2 class="section-title">Papers</h2>
        <ol class="pub-list">

{papers}        </ol>
      </div>
    </section>

    <section class="surface-section">
      <div class="container">
        <h2 class="section-title">Conference Presentations</h2>
        <div class="conf-list">

{talks}        </div>
      </div>
    </section>
"""
    return head(site, pb["meta"], "publications.html") + nav(site, "publications.html") + body + footer(site)


def render_projects(c):
    site, pr = c["site"], c["projects"]
    banners = ""
    for p in pr["items"]:
        desc = f'\n              <p class="project-banner-desc">{t(p["desc"])}</p>' if p.get("desc") else ""
        inner = f"""            <div class="project-banner-img">
              <img src="{a(p['image'])}" alt="{a(p.get('image_alt') or p['label'])}">
            </div>
            <div class="project-banner-body">
              <span class="project-banner-label">{t(p['label'])}</span>
              <h3 class="project-banner-title">{t(p['title'])}</h3>{desc}
              <div class="project-banner-tags">{tags(p['tags'], 'proj-tag')}</div>
"""
        if p.get("link"):
            banners += f"""          <a class="project-banner" href="{a(p['link'])}" target="_blank" rel="noopener">
{inner}              <span class="project-banner-arrow">&#8599;</span>
            </div>
          </a>

"""
        else:
            banners += f"""          <div class="project-banner project-banner-nohover">
{inner}              <span class="project-banner-arrow project-banner-wip">{t(p.get('status_text') or 'In progress')}</span>
            </div>
          </div>

"""
    body = page_hero("index.html", "Home", pr["hero_label"], pr["title"], pr["desc"]) + f"""
    <section>
      <div class="container">
        <div class="project-banners">

{banners}        </div>
      </div>
    </section>
"""
    return head(site, pr["meta"], "projects.html") + nav(site, "projects.html") + body + footer(site)


TCG_RENDER_SCRIPT = """  <script src="tcg-posts.js"></script>
  <script>
    (function () {
      var container = document.getElementById('%(id)s');
      var posts = (window.TCG_POSTS || [])%(slice)s;
      if (!posts.length) {
        container.innerHTML = '<p class="tcg-empty">No posts yet — check back soon.</p>';
        return;
      }
      container.innerHTML = posts.map(renderPost).join('');
    }());

    function renderPost(p) {
      var date = new Date(p.date).toLocaleDateString('en-GB', { day: 'numeric', month: 'long', year: 'numeric' });
      var photos = (p.photos || []).map(function (src) {
        return '<a href="' + src + '" target="_blank" rel="noopener"><img src="' + src + '" alt=""></a>';
      }).join('');
      return '<article class="tcg-post">'
        + '<time class="tcg-post-date">' + date + '</time>'
        + '<h3 class="tcg-post-title">' + p.title + '</h3>'
        + '<p class="tcg-post-body">' + p.body + '</p>'
        + (photos ? '<div class="tcg-post-photos">' + photos + '</div>' : '')
        + '</article>';
    }
  </script>
"""


def render_hobbies(c):
    site, hb = c["site"], c["hobbies"]
    art, manga, tcg = hb["ai_art"], hb["manga"], hb["tcg"]
    stack_img = art.get("stack_image") or (art["items"][0]["image"] if art["items"] else "")
    stack_alt = next((i["title"] for i in art["items"] if i["image"] == stack_img), "")
    chapters = ""
    for ch in manga["chapters"]:
        chapters += f"""          <a class="chapter-card" href="{a(ch['link'])}" target="_blank" rel="noopener">
            <img src="{a(ch['cover'])}" alt="{a(ch['label'])} Cover">
            <span class="chapter-label">{t(ch['label'])}</span>
          </a>
"""
    body = page_hero("index.html", "Home", hb["hero_label"], hb["title"], hb["desc"]) + f"""
    <!-- AI Art Gallery -->
    <section id="ai-art">
      <div class="container">
        <h2 class="section-title">{t(art['heading'])}</h2>
        <p class="section-sub">{t(art['intro'])}</p>
        <a href="ai-gallery.html" class="gallery-stack">
          <div class="stack-card stack-back-2"></div>
          <div class="stack-card stack-back-1"></div>
          <div class="stack-card stack-front">
            <img src="{a(stack_img)}" alt="{a(stack_alt)}">
            <span class="stack-label">View gallery &rarr;</span>
          </div>
        </a>
      </div>
    </section>

    <!-- AI One Piece Manga -->
    <section id="manga" class="surface-section">
      <div class="container">
        <h2 class="section-title">{t(manga['heading'])}</h2>
        <p class="section-sub">{t(manga['intro'])}</p>
        <p class="section-sub section-disclaimer"><em>{t(manga['disclaimer'])}</em></p>
        <div class="chapters-grid" id="chapters-grid">
{chapters}        </div>
      </div>
    </section>

    <!-- One Piece TCG -->
    <section id="tcg">
      <div class="container">
        <h2 class="section-title">{t(tcg['heading'])}</h2>
        <p class="section-sub">{t(tcg['intro'])}</p>
        <div class="tcg-blog" id="tcg-preview"></div>
        <div class="tcg-blog-footer">
          <a href="tcg-blog.html" class="btn btn-secondary">All posts &rarr;</a>
        </div>
      </div>
    </section>
"""
    scripts = TCG_RENDER_SCRIPT % {"id": "tcg-preview", "slice": f".slice(0, {tcg.get('preview_count', 3)})"}
    return head(site, hb["meta"], "hobbies.html") + nav(site, "hobbies.html") + body + footer(site, scripts)


def render_ai_gallery(c):
    site, g = c["site"], c["ai_gallery"]
    items = ""
    for it in c["hobbies"]["ai_art"]["items"]:
        items += f"""          <a class="gallery-item" href="{a(it['image'])}" target="_blank" rel="noopener">
            <img src="{a(it['image'])}" alt="{a(it['title'])}">
            <span class="gallery-label">{t(it['title'])}</span>
          </a>
"""
    body = page_hero("hobbies.html", "Hobbies", g["hero_label"], g["title"], g["desc"]) + f"""
    <section>
      <div class="container">
        <div class="gallery-grid">
{items}        </div>
      </div>
    </section>
"""
    return head(site, g["meta"], "ai-gallery.html") + nav(site, "hobbies.html") + body + footer(site)


def render_tcg_blog(c):
    site, b = c["site"], c["tcg_blog"]
    body = page_hero("hobbies.html", "Hobbies", b["hero_label"], b["title"], b["desc"]) + """
    <section>
      <div class="container">
        <div class="tcg-blog" id="tcg-all"></div>
      </div>
    </section>
"""
    scripts = TCG_RENDER_SCRIPT % {"id": "tcg-all", "slice": ""}
    return head(site, b["meta"], "tcg-blog.html") + nav(site, "hobbies.html") + body + footer(site, scripts)


def render_tcg_posts(c):
    posts = sorted(c["hobbies"]["tcg"]["posts"], key=lambda p: p["date"], reverse=True)
    return ("// One Piece TCG blog posts — newest first. Generated from content.json by admin/build.py.\n"
            "window.TCG_POSTS = " + json.dumps(posts, indent=2, ensure_ascii=False) + ";\n")


RENDERERS = {
    "index.html": render_index,
    "about.html": render_about,
    "experience.html": render_experience,
    "publications.html": render_publications,
    "projects.html": render_projects,
    "hobbies.html": render_hobbies,
    "ai-gallery.html": render_ai_gallery,
    "tcg-blog.html": render_tcg_blog,
    "tcg-posts.js": render_tcg_posts,
}


def load_content():
    with open(CONTENT_FILE, encoding="utf-8") as f:
        return json.load(f)


def build(content=None, out_dir=ROOT):
    content = content or load_content()
    written = []
    for name, fn in RENDERERS.items():
        path = os.path.join(out_dir, name)
        with open(path, "w", encoding="utf-8") as f:
            f.write(fn(content))
        written.append(name)
    return written


if __name__ == "__main__":
    for name in build():
        print("wrote", name)
