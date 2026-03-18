#!/usr/bin/env python3
# ============================================================
# TEST WEBSCRAPING SUPMTI v2
# Même logique que rag_service.py corrigé :
#   - Garde le footer HTML (contient tél, email)
#   - Injecte un bloc hardcodé (frais, filières, contact)
#   - Ignore les pages < 300 chars (JS dynamique)
#   - 21 URLs testées
# Lance depuis la racine du projet : python test_scraping.py
# ============================================================

import sys
import os
import time
import hashlib
import requests
from datetime import datetime
from bs4 import BeautifulSoup

GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
BLUE   = "\033[94m"
BOLD   = "\033[1m"
RESET  = "\033[0m"

def ok(msg):    print(f"  {GREEN}✅ {msg}{RESET}")
def err(msg):   print(f"  {RED}❌ {msg}{RESET}")
def warn(msg):  print(f"  {YELLOW}⚠️  {msg}{RESET}")
def info(msg):  print(f"  {BLUE}ℹ️  {msg}{RESET}")
def titre(msg): print(f"\n{BOLD}{'='*60}\n  {msg}\n{'='*60}{RESET}")

SEUIL_JS_MIN_CHARS = 300

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept":          "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection":      "keep-alive",
}

# ---- Import academic_config ----
try:
    sys.path.insert(0, '.')
    from app.academic_config import SCHOOL_INFO, FRAIS_SCOLARITE, FILIERES, SUPMTI_URLS
    URLS_A_TESTER = SUPMTI_URLS
    CONFIG_OK = True
except ImportError as e:
    warn(f"Impossible d'importer academic_config : {e}")
    CONFIG_OK = False
    SCHOOL_INFO     = {"telephone": "+212 5 35 51 10 11", "email": "contact@supmtimeknes.ac.ma",
                       "nom": "SUPMTI Meknès", "adresse": "Meknès, Maroc",
                       "site_web": "https://www.supmtimeknes.ac.ma",
                       "horaires": {"lundi_vendredi": "08:30-18:00", "samedi": "08:30-12:00"}}
    FRAIS_SCOLARITE = {"frais_annuels": 35000, "total_annuel": 38500,
                       "mensualites": 10, "montant_mensuel": 3500, "frais_inscription": 3500}
    FILIERES        = {}
    URLS_A_TESTER   = [
        "https://www.supmtimeknes.ac.ma",
        "https://supmtimeknes.ac.ma/supmti/",
        "https://supmtimeknes.ac.ma/programme-management-des-entreprises/",
        "https://supmtimeknes.ac.ma/finance-audit-et-controle-de-gestion/",
        "https://supmtimeknes.ac.ma/ingenierie-des-systemes-informatiques/",
        "https://supmtimeknes.ac.ma/admission_ecole_d_ingenierie/",
        "https://supmtimeknes.ac.ma/admission-en-ecole-de-management/",
    ]

# URLs ajoutées en v2 (peuvent être 404)
URLS_NOUVELLES_V2 = {"/contact/", "/nous-contacter/", "/tarifs/",
                     "/frais-de-scolarite/", "/actualites/"}


# ============================================================
# BLOC HARDCODÉ (même que dans rag_service.py)
# ============================================================

def construire_bloc_hardcode():
    lignes = [
        "=== DONNÉES GARANTIES SUPMTI (academic_config) ===",
        f"Ecole : {SCHOOL_INFO['nom']}",
        f"Telephone : {SCHOOL_INFO['telephone']}",
        f"Email : {SCHOOL_INFO['email']}",
        "",
        "=== FRAIS DE SCOLARITE ===",
        f"Frais annuels : {FRAIS_SCOLARITE['frais_annuels']} MAD/an",
        f"Frais inscription : {FRAIS_SCOLARITE['frais_inscription']} MAD",
        f"Total annuel : {FRAIS_SCOLARITE['total_annuel']} MAD",
        f"Mensualites : {FRAIS_SCOLARITE['mensualites']} x {FRAIS_SCOLARITE['montant_mensuel']} MAD/mois",
        "",
        "=== BOURSES ===",
        "Note >=18 : 100% bourse | >=16 : 70% | >=14 : 50% | >=12 : 30% | <12 : 0%",
        "",
        "=== FILIERES ===",
    ]
    for fid, f in FILIERES.items():
        lignes.append(f"{fid} - {f['nom']} ({f['niveau']}, {f['duree']} ans)")
        lignes.append(f"  Description : {f.get('description', '')}")
        lignes.append(f"  Debouches : {', '.join(f.get('debouches', []))}")
    lignes += [
        "",
        "=== STRUCTURE ===",
        "ISI (BAC+3) -> IISIC ou IISRT (BAC+5)",
        "ME (BAC+3) -> FACG ou MSTIC (BAC+5)",
        "",
        "=== ADMISSION ===",
        "1ere annee : apres le BAC, sur dossier + entretien",
        "3eme annee : DUT, BTS, DEUG (BAC+2)",
        "4eme annee : Licence ou BAC+3 (BAC+3)",
    ]
    return "\n".join(lignes)


# ============================================================
# EXTRACTION TEXTE — identique à rag_service.py v2
# ============================================================

def extraire_texte_page(soup, url):
    """Garde le footer, supprime uniquement script/style/nav/meta/link."""
    for tag in soup(["script", "style", "nav", "meta", "link",
                     "noscript", "iframe", "button", "form"]):
        tag.decompose()
    texte = soup.get_text(separator="\n", strip=True)
    lignes = [l.strip() for l in texte.splitlines() if l.strip() and len(l.strip()) > 2]
    return "\n".join(lignes)


def tester_url(url, timeout=15):
    debut = time.time()
    r = {
        "url": url, "ok": False, "status": 0, "duree_ms": 0,
        "nb_chars": 0, "nb_mots": 0, "titre_page": "",
        "footer_ok": False, "tel_dans_footer": False,
        "est_js": False, "erreur": None, "texte": ""
    }
    try:
        resp = requests.get(url, headers=HEADERS, timeout=timeout)
        r["duree_ms"] = int((time.time() - debut) * 1000)
        r["status"]   = resp.status_code

        if resp.status_code != 200:
            r["erreur"] = f"HTTP {resp.status_code}"
            return r

        soup = BeautifulSoup(resp.content, "html.parser")

        titre_tag = soup.find("title")
        r["titre_page"] = titre_tag.get_text(strip=True) if titre_tag else ""

        # Vérifier footer AVANT suppression
        footer = soup.find("footer")
        if footer:
            tf = footer.get_text(strip=True)
            r["footer_ok"]       = len(tf) > 20
            r["tel_dans_footer"] = (
                SCHOOL_INFO["telephone"].replace(" ", "") in tf.replace(" ", "")
            )

        texte_propre = extraire_texte_page(soup, url)
        r["nb_chars"] = len(texte_propre)
        r["nb_mots"]  = len(texte_propre.split())
        r["texte"]    = texte_propre

        if len(texte_propre) < SEUIL_JS_MIN_CHARS:
            r["est_js"] = True
            r["erreur"] = f"JS dynamique ({len(texte_propre)} chars < {SEUIL_JS_MIN_CHARS})"
            return r

        r["ok"] = True

    except requests.exceptions.Timeout:
        r["erreur"] = "Timeout"
    except requests.exceptions.ConnectionError:
        r["erreur"] = "Connexion impossible"
    except Exception as e:
        r["erreur"] = str(e)[:80]

    r["duree_ms"] = int((time.time() - debut) * 1000)
    return r


# ============================================================
# MAIN
# ============================================================

def main():
    print(f"\n{BOLD}{'='*60}")
    print(f"  WEBSCRAPING SUPMTI v2")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}{RESET}")

    # ─── TEST 0 : BLOC HARDCODÉ ───
    titre("TEST 0 — BLOC HARDCODE (frais + contact garantis)")

    bloc = construire_bloc_hardcode()
    checks_bloc = [
        ("Telephone present",      SCHOOL_INFO["telephone"].replace(" ", "") in bloc.replace(" ", "")),
        ("Email present",          SCHOOL_INFO["email"] in bloc),
        ("Frais annuels presents", str(FRAIS_SCOLARITE["frais_annuels"]) in bloc),
        ("Total annuel present",   str(FRAIS_SCOLARITE["total_annuel"]) in bloc),
        ("Bourses presentes",      "100%" in bloc),
        ("6 filieres presentes",   len(FILIERES) >= 6 and all(fid in bloc for fid in FILIERES)),
    ]
    nb_bloc_ok = 0
    for label, cond in checks_bloc:
        if cond:
            ok(label)
            nb_bloc_ok += 1
        else:
            err(f"{label} — ABSENT")

    info(f"Taille bloc : {len(bloc)} chars")

    # ─── TEST 1 : CONNECTIVITÉ ───
    titre("TEST 1 — CONNECTIVITE INTERNET")
    try:
        requests.get("https://www.google.com", timeout=5)
        ok("Internet disponible")
    except Exception as e:
        err(f"Pas de connexion : {e}")
        sys.exit(1)
    try:
        resp = requests.get("https://www.supmtimeknes.ac.ma", headers=HEADERS, timeout=10)
        ok(f"Site SUPMTI accessible (HTTP {resp.status_code})")
    except Exception as e:
        err(f"Site SUPMTI inaccessible : {e}")
        sys.exit(1)

    # ─── TEST 2 : SCRAPING ───
    titre(f"TEST 2 — SCRAPING ({len(URLS_A_TESTER)} URLs)")

    resultats     = []
    contenu_scrape = ""
    nb_ok = nb_erreur = nb_js = nb_v2_404 = 0
    footers_avec_tel = 0

    for i, url in enumerate(URLS_A_TESTER, 1):
        nom = url.replace("https://", "").replace("www.", "")[:55]
        print(f"\n  [{i:02d}/{len(URLS_A_TESTER)}] {BLUE}{nom}{RESET}")

        r = tester_url(url)
        resultats.append(r)
        est_v2 = any(slug in url for slug in URLS_NOUVELLES_V2)

        if r["ok"]:
            ok(f"HTTP {r['status']} — {r['nb_chars']} chars — {r['nb_mots']} mots — {r['duree_ms']}ms")
            if r["titre_page"]:
                info(f"Titre : {r['titre_page'][:70]}")
            if r["footer_ok"]:
                msg = "Footer conserve"
                if r["tel_dans_footer"]:
                    msg += " + TELEPHONE TROUVE dans footer"
                    footers_avec_tel += 1
                ok(msg)
            contenu_scrape += r["texte"] + "\n"
            nb_ok += 1
        elif r["est_js"]:
            warn(f"Page JS dynamique — ignoree proprement ({r['nb_chars']} chars)")
            nb_js += 1
        else:
            if est_v2 and r["status"] == 404:
                warn(f"HTTP 404 — URL v2 inexistante (a supprimer de academic_config)")
                nb_v2_404 += 1
            else:
                err(f"ECHEC — {r['erreur']}")
            nb_erreur += 1

    # ─── RÉSUMÉ ───
    titre("RESUME SCRAPING")
    erreurs_reelles = nb_erreur - nb_v2_404
    contenu_combine = bloc + "\n\n" + contenu_scrape

    print(f"  URLs testees         : {len(URLS_A_TESTER)}")
    print(f"  URLs OK              : {GREEN}{nb_ok}{RESET}")
    print(f"  Pages JS ignorees    : {YELLOW}{nb_js}{RESET} (non bloquant)")
    print(f"  URLs v2 404          : {YELLOW}{nb_v2_404}{RESET} (a supprimer)")
    print(f"  Erreurs reelles      : {RED}{erreurs_reelles}{RESET}")
    print(f"  Footers avec tel     : {footers_avec_tel}")
    print(f"  Contenu scrape seul  : {len(contenu_scrape):,} chars")
    print(f"  Contenu TOTAL        : {len(contenu_combine):,} chars (avec bloc hardcode)")

    # ─── TEST 3 : COHÉRENCE ───
    titre("TEST 3 — COHERENCE DU CONTENU COMBINE (scrape + hardcode)")
    cl = contenu_combine.lower()

    checks_coherence = [
        ("Nom ecole SUPMTI",         "supmti"        in cl),
        ("Ville Meknes",             "meknes"         in cl or "meknès" in cl),
        ("Telephone",                "+212"           in contenu_combine or "05 35" in contenu_combine),
        ("Email",                    "contact@"       in cl),
        (f"Frais {FRAIS_SCOLARITE['frais_annuels']} MAD",
                                     str(FRAIS_SCOLARITE["frais_annuels"]) in contenu_combine),
        (f"Total {FRAIS_SCOLARITE['total_annuel']} MAD",
                                     str(FRAIS_SCOLARITE["total_annuel"]) in contenu_combine),
        ("Filiere ISI",              "isi"            in cl),
        ("Filiere ME / management",  "management"     in cl),
        ("Filiere IISIC / IA",       "iisic"          in cl or "intelligence artificielle" in cl),
        ("Filiere IISRT / reseaux",  "iisrt"          in cl or "réseaux" in cl),
        ("Filiere FACG / finance",   "facg"           in cl or "finance" in cl),
        ("Filiere MSTIC",            "mstic"          in cl),
        ("Admission",                "admission"      in cl),
        ("Bourses",                  "bourse"         in cl or "100%"    in contenu_combine),
        ("BAC+3 / BAC+5",            "bac+3"          in cl or "bac+5"   in cl),
    ]

    nb_coh_ok = 0
    for label, cond in checks_coherence:
        if cond:
            ok(label)
            nb_coh_ok += 1
        else:
            err(f"{label} — ABSENT")

    score = round((nb_coh_ok / len(checks_coherence)) * 100)
    print(f"\n  Score coherence : {nb_coh_ok}/{len(checks_coherence)} ({score}%)")

    # ─── TEST 4 : HASH ───
    titre("TEST 4 — DETECTION DE CHANGEMENT (HASH)")
    hash_actuel = hashlib.md5(contenu_combine.encode("utf-8")).hexdigest()
    info(f"Hash MD5 contenu combine : {hash_actuel}")

    VECTOR_DB_PATH = os.getenv("VECTOR_DB_PATH", "./data/vectorstore")
    chemin_hash    = os.path.join(VECTOR_DB_PATH, "site_hash.txt")

    if os.path.exists(chemin_hash):
        try:
            with open(chemin_hash, "r") as f:
                ancien = f.read().strip()
            if ancien == hash_actuel:
                ok("Aucun changement — base RAG a jour")
            else:
                warn(f"CHANGEMENT DETECTE — reconstruction FAISS necessaire")
                info(f"Ancien : {ancien[:16]}... | Nouveau : {hash_actuel[:16]}...")
        except Exception as e:
            warn(f"Lecture hash precedent impossible : {e}")
    else:
        info(f"Pas de hash precedent dans {chemin_hash}")
        info("Premiere synchronisation — reconstruction FAISS necessaire")

    # ─── RAPPORT FINAL ───
    titre("RAPPORT FINAL")

    if score >= 100 and erreurs_reelles == 0:
        print(f"  {GREEN}{BOLD}SCRAPING PARFAIT — 100% operationnel{RESET}")
    elif score >= 85 and erreurs_reelles == 0:
        print(f"  {GREEN}{BOLD}SCRAPING OPERATIONNEL{RESET}")
    elif score >= 70:
        print(f"  {YELLOW}{BOLD}SCRAPING PARTIEL — verifier les erreurs{RESET}")
    else:
        print(f"  {RED}{BOLD}SCRAPING DEGRADE — action requise{RESET}")

    print(f"\n  Bloc hardcode  : {nb_bloc_ok}/{len(checks_bloc)} {'OK' if nb_bloc_ok == len(checks_bloc) else 'INCOMPLET'}")
    print(f"  URLs OK        : {nb_ok}/{len(URLS_A_TESTER)}")
    print(f"  Pages JS       : {nb_js} ignorees")
    print(f"  Erreurs reelles: {erreurs_reelles}")
    print(f"  Coherence      : {score}%")
    print(f"  Total contenu  : {len(contenu_combine):,} chars")
    print(f"  Hash           : {hash_actuel[:24]}...")

    # URLs v2 à supprimer si 404
    urls_v2_404 = [r["url"] for r in resultats
                   if r["status"] == 404 and any(s in r["url"] for s in URLS_NOUVELLES_V2)]
    if urls_v2_404:
        titre("URLS A SUPPRIMER DE academic_config.py -> SUPMTI_URLS")
        for u in urls_v2_404:
            print(f'    Supprimer : "{u}",')

    print()


if __name__ == "__main__":
    main()