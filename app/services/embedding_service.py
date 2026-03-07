# ============================================================
# EMBEDDING SERVICE — SUPMTI
# Génération et stockage des embeddings pour le RAG
# Tahirou — backend-tahirou
# ============================================================

import os
import json
import pickle
import numpy as np
from openai import OpenAI
from dotenv import load_dotenv
import faiss
import tiktoken
from app.academic_config import CHATBOT_CONFIG
import pypdf
# ============================================================
# INITIALISATION
# ============================================================

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

DOCUMENTS_PATH = os.getenv("DOCUMENTS_PATH", "./data/documents")
VECTOR_DB_PATH = os.getenv("VECTOR_DB_PATH", "./data/vectorstore")

MODELE_EMBEDDING = CHATBOT_CONFIG["modele_embedding"]
CHUNK_SIZE = CHATBOT_CONFIG["chunk_size"]
CHUNK_OVERLAP = CHATBOT_CONFIG["chunk_overlap"]

# ============================================================
# ÉTAPE 1 — CHARGER LES DOCUMENTS
# ============================================================

def charger_documents():
    """
    Lit tous les fichiers .txt et .pdf dans data/documents/
    Retourne une liste de textes bruts
    """
    documents = []

    if not os.path.exists(DOCUMENTS_PATH):
        print(f"[ERREUR] Dossier introuvable : {DOCUMENTS_PATH}")
        return documents

    for nom_fichier in os.listdir(DOCUMENTS_PATH):
        chemin = os.path.join(DOCUMENTS_PATH, nom_fichier)

        # Lire les fichiers .txt
        if nom_fichier.endswith(".txt"):
            try:
                with open(chemin, "r", encoding="utf-8") as f:
                    texte = f.read()
                    documents.append({
                        "source": nom_fichier,
                        "contenu": texte
                    })
                    print(f"[OK] Fichier chargé : {nom_fichier} ({len(texte)} caractères)")
            except Exception as e:
                print(f"[ERREUR] Impossible de lire {nom_fichier} : {e}")

        # Lire les fichiers .pdf
        elif nom_fichier.endswith(".pdf"):
            try:
                from pypdf import PdfReader
                reader = PdfReader(chemin)
                texte = ""
                for page in reader.pages:
                    texte += page.extract_text() or ""
                documents.append({
                    "source": nom_fichier,
                    "contenu": texte
                })
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
    avec un chevauchement de CHUNK_OVERLAP tokens
    """
    chunks = []
    encodeur = tiktoken.get_encoding("cl100k_base")

    for document in documents:
        texte = document["contenu"]
        source = document["source"]

        # Nettoyer le texte
        texte = texte.replace("\n\n\n", "\n\n").strip()

        # Encoder le texte en tokens
        tokens = encodeur.encode(texte)
        total_tokens = len(tokens)

        print(f"[INFO] {source} : {total_tokens} tokens au total")

        # Découper en chunks avec chevauchement
        debut = 0
        numero_chunk = 0

        while debut < total_tokens:
            fin = min(debut + CHUNK_SIZE, total_tokens)

            # Décoder les tokens en texte
            chunk_tokens = tokens[debut:fin]
            chunk_texte = encodeur.decode(chunk_tokens)

            chunks.append({
                "id": f"{source}_chunk_{numero_chunk}",
                "source": source,
                "contenu": chunk_texte,
                "numero": numero_chunk,
                "debut_token": debut,
                "fin_token": fin
            })

            numero_chunk += 1
            debut += CHUNK_SIZE - CHUNK_OVERLAP

    print(f"\n[RÉSUMÉ] {len(chunks)} chunk(s) créé(s) au total")
    return chunks

# ============================================================
# ÉTAPE 3 — GÉNÉRER LES EMBEDDINGS
# ============================================================

def generer_embeddings(chunks):
    """
    Pour chaque chunk, génère un vecteur de 1536 dimensions
    via l'API OpenAI text-embedding-ada-002
    Traite par lots de 20 pour éviter les limites API
    """
    embeddings = []
    taille_lot = 20

    print(f"[INFO] Génération des embeddings pour {len(chunks)} chunks...")

    for i in range(0, len(chunks), taille_lot):
        lot = chunks[i:i + taille_lot]
        textes = [chunk["contenu"] for chunk in lot]

        try:
            reponse = client.embeddings.create(
                model=MODELE_EMBEDDING,
                input=textes
            )

            for j, embedding_data in enumerate(reponse.data):
                embeddings.append({
                    "chunk": lot[j],
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
    Stocke tous les vecteurs dans une base FAISS
    Sauvegarde aussi les métadonnées (textes, sources)
    """
    if not embeddings:
        print("[ERREUR] Aucun embedding à stocker")
        return False

    # Créer le dossier si inexistant
    os.makedirs(VECTOR_DB_PATH, exist_ok=True)

    # Préparer les vecteurs numpy
    vecteurs = np.array(
        [e["vecteur"] for e in embeddings],
        dtype=np.float32
    )

    dimension = vecteurs.shape[1]  # 1536 pour ada-002
    print(f"[INFO] Dimension des vecteurs : {dimension}")
    print(f"[INFO] Nombre de vecteurs : {len(vecteurs)}")

    # Créer l'index FAISS
    index = faiss.IndexFlatL2(dimension)
    index.add(vecteurs)

    # Sauvegarder l'index FAISS
    chemin_index = os.path.join(VECTOR_DB_PATH, "index.faiss")
    faiss.write_index(index, chemin_index)
    print(f"[OK] Index FAISS sauvegardé : {chemin_index}")

    # Sauvegarder les métadonnées (textes originaux)
    metadonnees = [
        {
            "id": e["chunk"]["id"],
            "source": e["chunk"]["source"],
            "contenu": e["chunk"]["contenu"],
            "numero": e["chunk"]["numero"]
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
    Charge la base FAISS et les métadonnées depuis le disque
    Retourne (index, metadonnees) ou (None, None) si inexistant
    """
    chemin_index = os.path.join(VECTOR_DB_PATH, "index.faiss")
    chemin_meta = os.path.join(VECTOR_DB_PATH, "metadata.json")

    if not os.path.exists(chemin_index) or not os.path.exists(chemin_meta):
        print("[INFO] Aucune base vectorielle existante trouvée")
        return None, None

    try:
        index = faiss.read_index(chemin_index)
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
    Cherche les chunks les plus pertinents pour une question
    Retourne les top_k chunks les plus proches sémantiquement
    """
    if top_k is None:
        top_k = CHATBOT_CONFIG["top_k_recherche"]

    if index is None or metadonnees is None:
        print("[ERREUR] Base vectorielle non chargée")
        return []

    try:
        # Générer le vecteur de la question
        reponse = client.embeddings.create(
            model=MODELE_EMBEDDING,
            input=[question]
        )
        vecteur_question = np.array(
            [reponse.data[0].embedding],
            dtype=np.float32
        )

        # Rechercher dans FAISS
        distances, indices = index.search(vecteur_question, top_k)

        # Récupérer les chunks correspondants
        resultats = []
        for i, idx in enumerate(indices[0]):
            if idx < len(metadonnees) and idx >= 0:
                chunk = metadonnees[idx].copy()
                chunk["score_similarite"] = float(distances[0][i])
                resultats.append(chunk)

        return resultats

    except Exception as e:
        print(f"[ERREUR] Recherche sémantique échouée : {e}")
        return []

# ============================================================
# ÉTAPE 7 — INITIALISATION COMPLÈTE (Pipeline complet)
# ============================================================

def initialiser_base_vectorielle():
    """
    Lance le pipeline complet :
    1. Charge les documents
    2. Découpe en chunks
    3. Génère les embeddings
    4. Stocke dans FAISS
    """
    print("=" * 60)
    print("INITIALISATION DE LA BASE VECTORIELLE SUPMTI")
    print("=" * 60)

    # Étape 1 : Charger les documents
    print("\n--- ÉTAPE 1 : Chargement des documents ---")
    documents = charger_documents()
    if not documents:
        print("[ERREUR] Aucun document trouvé dans", DOCUMENTS_PATH)
        return False

    # Étape 2 : Découper en chunks
    print("\n--- ÉTAPE 2 : Découpage en chunks ---")
    chunks = decouper_en_chunks(documents)
    if not chunks:
        print("[ERREUR] Aucun chunk créé")
        return False

    # Étape 3 : Générer les embeddings
    print("\n--- ÉTAPE 3 : Génération des embeddings ---")
    embeddings = generer_embeddings(chunks)
    if not embeddings:
        print("[ERREUR] Aucun embedding généré")
        return False

    # Étape 4 : Stocker dans FAISS
    print("\n--- ÉTAPE 4 : Stockage dans FAISS ---")
    succes = stocker_dans_faiss(embeddings)

    if succes:
        print("\n" + "=" * 60)
        print("✅ BASE VECTORIELLE INITIALISÉE AVEC SUCCÈS !")
        print("=" * 60)
    else:
        print("\n[ERREUR] Échec de l'initialisation")

    return succes

# ============================================================
# ÉTAPE 8 — VÉRIFIER SI LA BASE DOIT ÊTRE RECONSTRUITE
# ============================================================

def base_doit_etre_reconstruite():
    """
    Vérifie si la base vectorielle existe déjà
    Si elle n'existe pas → retourne True (besoin de reconstruction)
    Si elle existe → retourne False
    """
    chemin_index = os.path.join(VECTOR_DB_PATH, "index.faiss")
    chemin_meta = os.path.join(VECTOR_DB_PATH, "metadata.json")

    existe = os.path.exists(chemin_index) and os.path.exists(chemin_meta)

    if existe:
        print("[INFO] Base vectorielle déjà existante — pas de reconstruction nécessaire")
        return False
    else:
        print("[INFO] Base vectorielle inexistante — reconstruction nécessaire")
        return True
