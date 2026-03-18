# ============================================================
# EMBEDDING SERVICE — SUPMTI
# Génération et stockage des embeddings pour le RAG
# Tahirou — backend-tahirou
# ============================================================

import os
import json
import hashlib
import numpy as np
from openai import OpenAI
from dotenv import load_dotenv
from pypdf import PdfReader   # Import unique — supprimé le doublon dans charger_documents()
import faiss
import tiktoken
from app.academic_config import CHATBOT_CONFIG

# ============================================================
# INITIALISATION
# ============================================================

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

DOCUMENTS_PATH = os.getenv("DOCUMENTS_PATH", "./data/documents")
VECTOR_DB_PATH = os.getenv("VECTOR_DB_PATH", "./data/vectorstore")

MODELE_EMBEDDING = CHATBOT_CONFIG["modele_embedding"]
CHUNK_SIZE       = CHATBOT_CONFIG["chunk_size"]
CHUNK_OVERLAP    = CHATBOT_CONFIG["chunk_overlap"]

# ============================================================
# ÉTAPE 1 — CHARGER LES DOCUMENTS
# ============================================================

def charger_documents():
    """
    Lit tous les fichiers .txt et .pdf dans data/documents/
    Retourne une liste de textes bruts.
    """
    documents = []

    if not os.path.exists(DOCUMENTS_PATH):
        print(f"[ERREUR] Dossier introuvable : {DOCUMENTS_PATH}")
        return documents

    for nom_fichier in sorted(os.listdir(DOCUMENTS_PATH)):
        chemin = os.path.join(DOCUMENTS_PATH, nom_fichier)

        if nom_fichier.endswith(".txt"):
            try:
                with open(chemin, "r", encoding="utf-8") as f:
                    texte = f.read()
                documents.append({"source": nom_fichier, "contenu": texte})
                print(f"[OK] Fichier chargé : {nom_fichier} ({len(texte)} caractères)")
            except Exception as e:
                print(f"[ERREUR] Impossible de lire {nom_fichier} : {e}")

        elif nom_fichier.endswith(".pdf"):
            try:
                # PdfReader importé en haut du fichier — pas de double import
                reader = PdfReader(chemin)
                texte  = ""
                for page in reader.pages:
                    texte += page.extract_text() or ""
                documents.append({"source": nom_fichier, "contenu": texte})
                print(f"[OK] PDF chargé : {nom_fichier} ({len(texte)} caractères)")
            except Exception as e:
                print(f"[ERREUR] Impossible de lire {nom_fichier} : {e}")

    print(f"\n[RÉSUMÉ] {len(documents)} document(s) chargé(s) au total")
    return documents

# ============================================================
# ÉTAPE 2 — DÉCOUPER EN CHUNKS
# ============================================================

def decouper_en_chunks(documents):
    """
    Découpe chaque document en morceaux de CHUNK_SIZE tokens
    avec chevauchement de CHUNK_OVERLAP tokens.
    """
    chunks  = []
    encodeur = tiktoken.get_encoding("cl100k_base")

    for document in documents:
        texte  = document["contenu"]
        source = document["source"]

        texte  = texte.replace("\n\n\n", "\n\n").strip()
        tokens = encodeur.encode(texte)
        total_tokens = len(tokens)
        print(f"[INFO] {source} : {total_tokens} tokens au total")

        debut        = 0
        numero_chunk = 0

        while debut < total_tokens:
            fin          = min(debut + CHUNK_SIZE, total_tokens)
            chunk_texte  = encodeur.decode(tokens[debut:fin])

            chunks.append({
                "id":          f"{source}_chunk_{numero_chunk}",
                "source":      source,
                "contenu":     chunk_texte,
                "numero":      numero_chunk,
                "debut_token": debut,
                "fin_token":   fin
            })

            numero_chunk += 1
            debut        += CHUNK_SIZE - CHUNK_OVERLAP

    print(f"\n[RÉSUMÉ] {len(chunks)} chunk(s) créé(s) au total")
    return chunks

# ============================================================
# ÉTAPE 3 — GÉNÉRER LES EMBEDDINGS
# ============================================================

def generer_embeddings(chunks):
    """
    Génère un vecteur de 1536 dimensions pour chaque chunk
    via l'API OpenAI text-embedding-ada-002.
    Traite par lots de 20.
    """
    embeddings  = []
    taille_lot  = 20

    print(f"[INFO] Génération des embeddings pour {len(chunks)} chunks...")

    for i in range(0, len(chunks), taille_lot):
        lot    = chunks[i:i + taille_lot]
        textes = [chunk["contenu"] for chunk in lot]

        try:
            reponse = client.embeddings.create(
                model=MODELE_EMBEDDING,
                input=textes
            )
            for j, embedding_data in enumerate(reponse.data):
                embeddings.append({
                    "chunk":   lot[j],
                    "vecteur": embedding_data.embedding
                })
            print(f"[OK] Lot {i // taille_lot + 1} traité ({len(lot)} chunks)")

        except Exception as e:
            print(f"[ERREUR] Lot {i // taille_lot + 1} échoué : {e}")

    print(f"\n[RÉSUMÉ] {len(embeddings)} embedding(s) généré(s)")
    return embeddings

# ============================================================
# ÉTAPE 4 — STOCKER DANS FAISS
# ============================================================

def stocker_dans_faiss(embeddings):
    """
    Stocke tous les vecteurs dans une base FAISS.
    Sauvegarde aussi les métadonnées (textes, sources).
    """
    if not embeddings:
        print("[ERREUR] Aucun embedding à stocker")
        return False

    os.makedirs(VECTOR_DB_PATH, exist_ok=True)

    vecteurs  = np.array([e["vecteur"] for e in embeddings], dtype=np.float32)
    dimension = vecteurs.shape[1]
    print(f"[INFO] Dimension : {dimension} | Vecteurs : {len(vecteurs)}")

    index = faiss.IndexFlatL2(dimension)
    index.add(vecteurs)

    chemin_index = os.path.join(VECTOR_DB_PATH, "index.faiss")
    faiss.write_index(index, chemin_index)
    print(f"[OK] Index FAISS sauvegardé : {chemin_index}")

    metadonnees = [
        {
            "id":      e["chunk"]["id"],
            "source":  e["chunk"]["source"],
            "contenu": e["chunk"]["contenu"],
            "numero":  e["chunk"]["numero"]
        }
        for e in embeddings
    ]

    chemin_meta = os.path.join(VECTOR_DB_PATH, "metadata.json")
    with open(chemin_meta, "w", encoding="utf-8") as f:
        json.dump(metadonnees, f, ensure_ascii=False, indent=2)
    print(f"[OK] Métadonnées sauvegardées : {chemin_meta}")

    return True

# ============================================================
# ÉTAPE 5 — CHARGER LA BASE EXISTANTE
# ============================================================

def charger_base_existante():
    """
    Charge la base FAISS et les métadonnées depuis le disque.
    Retourne (index, metadonnees) ou (None, None).
    """
    chemin_index = os.path.join(VECTOR_DB_PATH, "index.faiss")
    chemin_meta  = os.path.join(VECTOR_DB_PATH, "metadata.json")

    if not os.path.exists(chemin_index) or not os.path.exists(chemin_meta):
        print("[INFO] Aucune base vectorielle existante trouvée")
        return None, None

    try:
        index       = faiss.read_index(chemin_index)
        with open(chemin_meta, "r", encoding="utf-8") as f:
            metadonnees = json.load(f)
        print(f"[OK] Base vectorielle chargée : {index.ntotal} vecteurs")
        return index, metadonnees
    except Exception as e:
        print(f"[ERREUR] Impossible de charger la base : {e}")
        return None, None

# ============================================================
# ÉTAPE 6 — RECHERCHE SÉMANTIQUE
# ============================================================

def recherche_semantique(question, index, metadonnees, top_k=None):
    """
    Cherche les chunks les plus pertinents pour une question.
    Retourne les top_k chunks les plus proches sémantiquement.
    """
    if top_k is None:
        top_k = CHATBOT_CONFIG["top_k_recherche"]

    if index is None or metadonnees is None:
        print("[ERREUR] Base vectorielle non chargée")
        return []

    try:
        reponse = client.embeddings.create(
            model=MODELE_EMBEDDING,
            input=[question]
        )
        vecteur_question = np.array(
            [reponse.data[0].embedding], dtype=np.float32
        )

        distances, indices = index.search(vecteur_question, top_k)

        resultats = []
        for i, idx in enumerate(indices[0]):
            if 0 <= idx < len(metadonnees):
                chunk = metadonnees[idx].copy()
                chunk["score_similarite"] = float(distances[0][i])
                resultats.append(chunk)

        return resultats

    except Exception as e:
        print(f"[ERREUR] Recherche sémantique échouée : {e}")
        return []

# ============================================================
# ÉTAPE 7 — PIPELINE COMPLET D'INITIALISATION
# ============================================================

def initialiser_base_vectorielle():
    """
    Lance le pipeline complet :
    1. Charge les documents
    2. Découpe en chunks
    3. Génère les embeddings
    4. Stocke dans FAISS
    5. Sauvegarde le hash des documents sources
    """
    print("=" * 60)
    print("INITIALISATION DE LA BASE VECTORIELLE SUPMTI")
    print("=" * 60)

    print("\n--- ÉTAPE 1 : Chargement des documents ---")
    documents = charger_documents()
    if not documents:
        print("[ERREUR] Aucun document trouvé dans", DOCUMENTS_PATH)
        return False

    print("\n--- ÉTAPE 2 : Découpage en chunks ---")
    chunks = decouper_en_chunks(documents)
    if not chunks:
        print("[ERREUR] Aucun chunk créé")
        return False

    print("\n--- ÉTAPE 3 : Génération des embeddings ---")
    embeddings = generer_embeddings(chunks)
    if not embeddings:
        print("[ERREUR] Aucun embedding généré")
        return False

    print("\n--- ÉTAPE 4 : Stockage dans FAISS ---")
    succes = stocker_dans_faiss(embeddings)

    if succes:
        # Sauvegarder le hash des documents pour détecter les futurs changements
        _sauvegarder_hash_documents(documents)
        print("\n" + "=" * 60)
        print("✅ BASE VECTORIELLE INITIALISÉE AVEC SUCCÈS !")
        print("=" * 60)
    else:
        print("\n[ERREUR] Échec de l'initialisation")

    return succes

# ============================================================
# ÉTAPE 8 — VÉRIFIER SI LA BASE DOIT ÊTRE RECONSTRUITE
# ============================================================

def _calculer_hash_documents(documents):
    """Calcule un hash MD5 du contenu combiné de tous les documents."""
    contenu_combine = "".join(
        f"{d['source']}:{d['contenu']}" for d in documents
    )
    return hashlib.md5(contenu_combine.encode("utf-8")).hexdigest()


def _sauvegarder_hash_documents(documents):
    """Sauvegarde le hash des documents après reconstruction."""
    os.makedirs(VECTOR_DB_PATH, exist_ok=True)
    chemin_hash = os.path.join(VECTOR_DB_PATH, "documents_hash.txt")
    hash_val    = _calculer_hash_documents(documents)
    try:
        with open(chemin_hash, "w") as f:
            f.write(hash_val)
        print(f"[INFO] Hash documents sauvegardé : {hash_val[:12]}...")
    except Exception as e:
        print(f"[AVERTISSEMENT] Impossible de sauvegarder le hash : {e}")


def base_doit_etre_reconstruite():
    """
    Vérifie si la base vectorielle doit être reconstruite.
    Conditions déclenchant une reconstruction :
    1. Les fichiers FAISS n'existent pas
    2. Le contenu des documents sources a changé (hash différent)
    """
    chemin_index = os.path.join(VECTOR_DB_PATH, "index.faiss")
    chemin_meta  = os.path.join(VECTOR_DB_PATH, "metadata.json")
    chemin_hash  = os.path.join(VECTOR_DB_PATH, "documents_hash.txt")

    # Condition 1 : fichiers FAISS absents
    if not os.path.exists(chemin_index) or not os.path.exists(chemin_meta):
        print("[INFO] Base vectorielle inexistante — reconstruction nécessaire")
        return True

    # Condition 2 : hash des documents sources
    if not os.path.exists(chemin_hash):
        print("[INFO] Hash documents absent — reconstruction par précaution")
        return True

    # Charger les documents actuels et comparer le hash
    documents_actuels = charger_documents()
    if not documents_actuels:
        print("[INFO] Aucun document trouvé — pas de reconstruction")
        return False

    hash_actuel = _calculer_hash_documents(documents_actuels)
    try:
        with open(chemin_hash, "r") as f:
            hash_sauvegarde = f.read().strip()
    except Exception:
        hash_sauvegarde = ""

    if hash_actuel != hash_sauvegarde:
        print("[INFO] Contenu des documents modifié — reconstruction nécessaire")
        return True

    print("[INFO] Base vectorielle à jour — pas de reconstruction nécessaire")
    return False