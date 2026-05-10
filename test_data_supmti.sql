-- ============================================================
-- SUPMTI CHATBOT — DONNÉES DE TEST COMPLÈTES
-- À exécuter dans pgAdmin (Query Tool) section par section
-- ============================================================

-- ============================================================
-- ÉTAPE 1 : NETTOYER LES DONNÉES EXISTANTES (optionnel)
-- Décommenter si tu veux repartir de zéro proprement
-- ============================================================
/*
TRUNCATE demandes_peermatch, ambassadeurs, fit_scores, student_interests,
         messages, conversations, document_chunks, documents,
         students, interests, programs, users
CASCADE;
*/


-- ============================================================
-- ÉTAPE 2 : INTÉRÊTS (centres d'intérêt étudiant)
-- Utilisés dans student_interests et pour le matching IA
-- ============================================================
INSERT INTO interests (id, name) VALUES
  (uuid_generate_v4(), 'Intelligence Artificielle'),
  (uuid_generate_v4(), 'Développement Web'),
  (uuid_generate_v4(), 'Marketing Digital'),
  (uuid_generate_v4(), 'Cybersécurité'),
  (uuid_generate_v4(), 'Gestion de Projet'),
  (uuid_generate_v4(), 'Design UI/UX'),
  (uuid_generate_v4(), 'Réseaux & Télécommunications'),
  (uuid_generate_v4(), 'Finance & Comptabilité'),
  (uuid_generate_v4(), 'Entrepreneuriat'),
  (uuid_generate_v4(), 'Data Science')
ON CONFLICT DO NOTHING;


-- ============================================================
-- ÉTAPE 3 : PROGRAMMES / FILIÈRES SUPMTI
-- Ces IDs seront référencés dans fit_scores
-- ============================================================
INSERT INTO programs (id, name, description, required_average, duration, diploma) VALUES
  (uuid_generate_v4(),
   'ISI — Ingénierie Systèmes Informatiques',
   'Formation d''ingénieurs spécialisés en développement logiciel, cloud et architecture système.',
   12.5, 5, 'Ingénieur d''État'),

  (uuid_generate_v4(),
   'ME — Management des Entreprises',
   'Formation en gestion, stratégie d''entreprise et leadership opérationnel.',
   11.0, 3, 'Licence Professionnelle'),

  (uuid_generate_v4(),
   'IISIC — IA & Systèmes d''Information',
   'Spécialisation en Intelligence Artificielle, Machine Learning et systèmes intelligents.',
   13.0, 5, 'Ingénieur d''État'),

  (uuid_generate_v4(),
   'IISRT — Réseaux & Télécommunications',
   'Expertise en infrastructure réseau, protocoles et systèmes de communication.',
   12.0, 5, 'Ingénieur d''État'),

  (uuid_generate_v4(),
   'FACG — Finance, Audit & Contrôle de Gestion',
   'Formation en comptabilité, audit interne, contrôle de gestion et finance d''entreprise.',
   11.5, 3, 'Licence Professionnelle'),

  (uuid_generate_v4(),
   'MSTIC — Management des Systèmes TIC',
   'Formation à l''intersection du digital, du management et de la transformation numérique.',
   11.0, 3, 'Licence Professionnelle')
ON CONFLICT DO NOTHING;


-- ============================================================
-- ÉTAPE 4 : UTILISATEURS DE TEST
-- 3 profils différents pour tester les scénarios SAMI
-- ============================================================

-- Utilisateur 1 : Étudiant avec profil complet (bon pour FitScore)
INSERT INTO users (id, full_name, email, password_hash, role, is_active) VALUES
  ('a1b2c3d4-0001-0001-0001-000000000001',
   'Yassine El Mansouri',
   'yassine@test.supmti.ma',
   '$2b$12$placeholder_hash_yassine',
   'student', TRUE),

-- Utilisateur 2 : Étudiante avec profil partiel
  ('a1b2c3d4-0002-0002-0002-000000000002',
   'Sarah Benali',
   'sarah@test.supmti.ma',
   '$2b$12$placeholder_hash_sarah',
   'student', TRUE),

-- Utilisateur 3 : Étudiant profil vide (pour tester l'onboarding)
  ('a1b2c3d4-0003-0003-0003-000000000003',
   'Omar Tahiri',
   'omar@test.supmti.ma',
   '$2b$12$placeholder_hash_omar',
   'student', TRUE),

-- Utilisateur 4 : Admin
  ('a1b2c3d4-0004-0004-0004-000000000004',
   'Admin SUPMTI',
   'admin@supmtimeknes.ac.ma',
   '$2b$12$placeholder_hash_admin',
   'admin', TRUE)
ON CONFLICT (email) DO NOTHING;


-- ============================================================
-- ÉTAPE 5 : PROFILS ÉTUDIANTS (table students)
-- Contient les données académiques pour le FitScore
-- ============================================================

-- Yassine : BAC Sciences Maths, bonne moyenne → profil ISI/IISIC
INSERT INTO students (id, user_id, average, level, bac_type, city) VALUES
  ('b1b2c3d4-0001-0001-0001-000000000001',
   'a1b2c3d4-0001-0001-0001-000000000001',
   15.5, 'Terminale', 'SM', 'Meknès'),

-- Sarah : BAC Economie, moyenne correcte → profil ME/FACG/MSTIC
  ('b1b2c3d4-0002-0002-0002-000000000002',
   'a1b2c3d4-0002-0002-0002-000000000002',
   13.0, 'Bac+1', 'ECO', 'Fès'),

-- Omar : profil vide pour tester l'onboarding
  ('b1b2c3d4-0003-0003-0003-000000000003',
   'a1b2c3d4-0003-0003-0003-000000000003',
   0.0, 'Terminale', NULL, NULL)
ON CONFLICT DO NOTHING;


-- ============================================================
-- ÉTAPE 6 : INTÉRÊTS DES ÉTUDIANTS (liaison)
-- ============================================================

-- Yassine : IA, Dev Web, Cybersécurité
INSERT INTO student_interests (student_id, interest_id)
SELECT 'b1b2c3d4-0001-0001-0001-000000000001', id
FROM interests
WHERE name IN ('Intelligence Artificielle', 'Développement Web', 'Cybersécurité')
ON CONFLICT DO NOTHING;

-- Sarah : Marketing, Gestion de projet, Finance
INSERT INTO student_interests (student_id, interest_id)
SELECT 'b1b2c3d4-0002-0002-0002-000000000002', id
FROM interests
WHERE name IN ('Marketing Digital', 'Gestion de Projet', 'Finance & Comptabilité')
ON CONFLICT DO NOTHING;


-- ============================================================
-- ÉTAPE 7 : SCORES FITSCORE PRÉ-CALCULÉS
-- Simule des résultats de l'algorithme de matching IA
-- ============================================================

-- FitScore de Yassine (excellente compat ISI et IISIC)
INSERT INTO fit_scores (id, student_id, program_id, score, explanation)
SELECT
  uuid_generate_v4(),
  'b1b2c3d4-0001-0001-0001-000000000001',
  p.id,
  CASE p.name
    WHEN 'IISIC — IA & Systèmes d''Information'      THEN 92.5
    WHEN 'ISI — Ingénierie Systèmes Informatiques'   THEN 88.0
    WHEN 'IISRT — Réseaux & Télécommunications'      THEN 74.0
    WHEN 'ME — Management des Entreprises'           THEN 55.0
    WHEN 'MSTIC — Management des Systèmes TIC'       THEN 60.0
    WHEN 'FACG — Finance, Audit & Contrôle de Gestion' THEN 42.0
    ELSE 50.0
  END,
  'Calculé sur la base BAC SM 15.5/20 et intérêts IA/Dev'
FROM programs p
ON CONFLICT DO NOTHING;

-- FitScore de Sarah (bonne compat ME, FACG, MSTIC)
INSERT INTO fit_scores (id, student_id, program_id, score, explanation)
SELECT
  uuid_generate_v4(),
  'b1b2c3d4-0002-0002-0002-000000000002',
  p.id,
  CASE p.name
    WHEN 'ME — Management des Entreprises'             THEN 87.0
    WHEN 'FACG — Finance, Audit & Contrôle de Gestion' THEN 84.5
    WHEN 'MSTIC — Management des Systèmes TIC'         THEN 79.0
    WHEN 'ISI — Ingénierie Systèmes Informatiques'     THEN 48.0
    WHEN 'IISIC — IA & Systèmes d''Information'        THEN 44.0
    WHEN 'IISRT — Réseaux & Télécommunications'        THEN 41.0
    ELSE 50.0
  END,
  'Calculé sur la base BAC ECO 13.0/20 et intérêts Marketing/Finance'
FROM programs p
ON CONFLICT DO NOTHING;


-- ============================================================
-- ÉTAPE 8 : CONVERSATIONS & MESSAGES DE TEST
-- Pour tester l'historique dans la Sidebar et /history
-- ============================================================

-- Conversation 1 : Yassine pose des questions sur les filières
INSERT INTO conversations (id, student_id, started_at) VALUES
  ('c1b2c3d4-0001-0001-0001-000000000001',
   'b1b2c3d4-0001-0001-0001-000000000001',
   NOW() - INTERVAL '3 days');

INSERT INTO messages (id, conversation_id, content, sender, created_at) VALUES
  (uuid_generate_v4(),
   'c1b2c3d4-0001-0001-0001-000000000001',
   'Bonjour, je suis Yassine, j''ai eu un BAC Sciences Maths avec 15.5 de moyenne et je m''intéresse à l''IA.',
   'user',
   NOW() - INTERVAL '3 days'),
  (uuid_generate_v4(),
   'c1b2c3d4-0001-0001-0001-000000000001',
   'Bonjour Yassine ! Avec un BAC SM et une moyenne de 15.5, tu es un excellent candidat pour les filières ingénieur de SUPMTI. Je te recommande particulièrement **IISIC** (IA & Systèmes d''Information) qui correspond parfaitement à ton intérêt pour l''IA, ainsi que **ISI** (Ingénierie Systèmes Informatiques). Veux-tu que je calcule ton FitScore précis ?',
   'bot',
   NOW() - INTERVAL '3 days' + INTERVAL '30 seconds'),
  (uuid_generate_v4(),
   'c1b2c3d4-0001-0001-0001-000000000001',
   'Oui, calcule mon FitScore s''il te plaît.',
   'user',
   NOW() - INTERVAL '3 days' + INTERVAL '2 minutes'),
  (uuid_generate_v4(),
   'c1b2c3d4-0001-0001-0001-000000000001',
   '🎯 **Ton FitScore SUPMTI** :\n\n1. **IISIC** — 92.5% ⭐ Top Match\n2. **ISI** — 88.0%\n3. **IISRT** — 74.0%\n\nTon profil mathématique est excellent ! Je te conseille de passer le test psychométrique pour affiner encore ces résultats.',
   'bot',
   NOW() - INTERVAL '3 days' + INTERVAL '3 minutes');

-- Conversation 2 : Sarah sur l'admission
INSERT INTO conversations (id, student_id, started_at) VALUES
  ('c1b2c3d4-0002-0002-0002-000000000002',
   'b1b2c3d4-0002-0002-0002-000000000002',
   NOW() - INTERVAL '1 day');

INSERT INTO messages (id, conversation_id, content, sender, created_at) VALUES
  (uuid_generate_v4(),
   'c1b2c3d4-0002-0002-0002-000000000002',
   'Bonjour ! Je m''appelle Sarah, j''ai un BAC Economie avec 13/20 et j''habite à Fès.',
   'user',
   NOW() - INTERVAL '1 day'),
  (uuid_generate_v4(),
   'c1b2c3d4-0002-0002-0002-000000000002',
   'Bonjour Sarah ! Bienvenue sur SUPMTI. Avec un BAC Economie et 13/20, tu es éligible à plusieurs filières intéressantes. Je te recommande notamment **Management des Entreprises (ME)** et **Finance, Audit & Contrôle de Gestion (FACG)**. Quels sont tes centres d''intérêt professionnels ?',
   'bot',
   NOW() - INTERVAL '1 day' + INTERVAL '30 seconds');


-- ============================================================
-- ÉTAPE 9 : AMBASSADEURS PEERMATCH
-- Étudiants ambassadeurs disponibles pour le matching
-- Note : program_id ici est le code filière (VARCHAR), pas UUID
-- ============================================================
INSERT INTO ambassadeurs (id, nom, program_id, niveau, email, whatsapp, is_active) VALUES
  (uuid_generate_v4(), 'Karim Alaoui',    'ISI',   'Master 1',   'karim.amb@supmtimeknes.ac.ma',  '+212612111111', TRUE),
  (uuid_generate_v4(), 'Nadia Essaidi',   'IISIC', 'Licence 3',  'nadia.amb@supmtimeknes.ac.ma',  '+212698222222', TRUE),
  (uuid_generate_v4(), 'Hamza Benkirane', 'ME',    'Master 2',   'hamza.amb@supmtimeknes.ac.ma',  '+212644333333', TRUE),
  (uuid_generate_v4(), 'Fatima Zahra',    'FACG',  'Licence 2',  'fatima.amb@supmtimeknes.ac.ma', '+212600444444', TRUE),
  (uuid_generate_v4(), 'Adil Rachidi',    'IISRT', 'Master 1',   'adil.amb@supmtimeknes.ac.ma',   '+22674673278', TRUE),
  (uuid_generate_v4(), 'Leila Hamdaoui',  'MSTIC', 'Licence 3',  'leila.amb@supmtimeknes.ac.ma',  '+212697666666', TRUE),
  -- Ambassadeur inactif (pour tester la logique de filtrage)
  (uuid_generate_v4(), 'Rachid Test',     'ISI',   'Diplômé',    'rachid.amb@supmtimeknes.ac.ma', '+212600000000', FALSE)
ON CONFLICT DO NOTHING;


-- ============================================================
-- ÉTAPE 10 : DEMANDES PEERMATCH DE TEST
-- Pour tester l'historique et le tableau admin
-- ============================================================
INSERT INTO demandes_peermatch (
  id, ambassadeur_id, prenom_etudiant, email_etudiant,
  filiere, message, statut, created_at
)
SELECT
  uuid_generate_v4(),
  a.id,
  'Test Etudiant',
  'testdemande@test.com',
  'ISI',
  'Je souhaite en savoir plus sur la filière ISI.',
  'en_attente',
  NOW() - INTERVAL '2 days'
FROM ambassadeurs a
WHERE a.program_id = 'ISI' AND a.is_active = TRUE
LIMIT 1;

INSERT INTO demandes_peermatch (
  id, ambassadeur_id, prenom_etudiant, email_etudiant,
  filiere, message, statut, created_at
)
SELECT
  uuid_generate_v4(),
  a.id,
  'Amina Tester',
  'amina@test.com',
  'ME',
  'Bonjour, j''aimerais discuter du débouché en management.',
  'traitee',
  NOW() - INTERVAL '5 days'
FROM ambassadeurs a
WHERE a.program_id = 'ME' AND a.is_active = TRUE
LIMIT 1;


-- ============================================================
-- ÉTAPE 11 : DOCUMENTS RAG (Base de Connaissances)
-- Textes que l'IA utilise pour répondre aux questions
-- ============================================================
INSERT INTO documents (id, title, source) VALUES
  ('d1b2c3d4-0001-0001-0001-000000000001', 'Guide d''Admission SUPMTI 2026',    'PDF_Interne'),
  ('d1b2c3d4-0002-0002-0002-000000000002', 'Règlement Intérieur SUPMTI',        'Portail_Etudiant'),
  ('d1b2c3d4-0003-0003-0003-000000000003', 'Présentation des Filières 2026',    'Site_Web'),
  ('d1b2c3d4-0004-0004-0004-000000000004', 'Frais de Scolarité & Bourses 2026', 'Administration')
ON CONFLICT DO NOTHING;

INSERT INTO document_chunks (id, document_id, content, embedding) VALUES
  -- Admission
  (uuid_generate_v4(), 'd1b2c3d4-0001-0001-0001-000000000001',
   'Les inscriptions pour l''année académique 2026 sont ouvertes du 1er juin au 31 août. Le dossier comprend les bulletins de terminale, le baccalauréat et une lettre de motivation.',
   'vector_placeholder'),
  (uuid_generate_v4(), 'd1b2c3d4-0001-0001-0001-000000000001',
   'Le concours d''accès au cycle ingénieur se déroule en deux phases : un test écrit (mathématiques, physique, informatique) suivi d''un entretien de motivation.',
   'vector_placeholder'),
  (uuid_generate_v4(), 'd1b2c3d4-0001-0001-0001-000000000001',
   'SUPMTI accepte les candidats titulaires d''un baccalauréat scientifique (SM, PC, SVT) ou économique pour les filières licence avec une moyenne minimale de 10/20.',
   'vector_placeholder'),

  -- Frais & Bourses
  (uuid_generate_v4(), 'd1b2c3d4-0004-0004-0004-000000000004',
   'Les frais de scolarité pour le cycle ingénieur sont de 22 000 DH par an. Pour les licences professionnelles, ils sont de 15 000 DH par an.',
   'vector_placeholder'),
  (uuid_generate_v4(), 'd1b2c3d4-0004-0004-0004-000000000004',
   'SUPMTI propose des bourses d''excellence pour les étudiants ayant une mention Très Bien au baccalauréat (16/20 et plus). La bourse couvre jusqu''à 30% des frais de scolarité.',
   'vector_placeholder'),
  (uuid_generate_v4(), 'd1b2c3d4-0004-0004-0004-000000000004',
   'Des facilités de paiement sont disponibles : paiement en 3 tranches par semestre. Un accompagnement pour les demandes de crédit bancaire étudiant est également proposé.',
   'vector_placeholder'),

  -- Filières
  (uuid_generate_v4(), 'd1b2c3d4-0003-0003-0003-000000000003',
   'La filière ISI (Ingénierie Systèmes Informatiques) forme des ingénieurs polyvalents en développement logiciel, cloud computing, DevOps et architecture système. Durée : 5 ans après le baccalauréat.',
   'vector_placeholder'),
  (uuid_generate_v4(), 'd1b2c3d4-0003-0003-0003-000000000003',
   'La filière IISIC (IA & Systèmes d''Information et de Communication) est la plus récente de SUPMTI. Elle couvre le Machine Learning, le Deep Learning, le NLP et la Data Science avancée.',
   'vector_placeholder'),
  (uuid_generate_v4(), 'd1b2c3d4-0003-0003-0003-000000000003',
   'Le taux d''insertion professionnelle à SUPMTI est de 94% dans les 6 mois suivant l''obtention du diplôme, selon l''enquête alumni 2025.',
   'vector_placeholder'),
  (uuid_generate_v4(), 'd1b2c3d4-0003-0003-0003-000000000003',
   'SUPMTI dispose de partenariats avec plus de 80 entreprises au Maroc et à l''international pour les stages et l''emploi : OCP, Maroc Telecom, CIH Bank, CGI, Capgemini.',
   'vector_placeholder')
ON CONFLICT DO NOTHING;


-- ============================================================
-- VÉRIFICATION FINALE
-- Exécuter pour vérifier que tout est bien inséré
-- ============================================================
SELECT 'users'              AS table_name, COUNT(*) FROM users
UNION ALL
SELECT 'students',                          COUNT(*) FROM students
UNION ALL
SELECT 'interests',                         COUNT(*) FROM interests
UNION ALL
SELECT 'student_interests',                 COUNT(*) FROM student_interests
UNION ALL
SELECT 'programs',                          COUNT(*) FROM programs
UNION ALL
SELECT 'fit_scores',                        COUNT(*) FROM fit_scores
UNION ALL
SELECT 'conversations',                     COUNT(*) FROM conversations
UNION ALL
SELECT 'messages',                          COUNT(*) FROM messages
UNION ALL
SELECT 'ambassadeurs',                      COUNT(*) FROM ambassadeurs
UNION ALL
SELECT 'demandes_peermatch',                COUNT(*) FROM demandes_peermatch
UNION ALL
SELECT 'documents',                         COUNT(*) FROM documents
UNION ALL
SELECT 'document_chunks',                   COUNT(*) FROM document_chunks
ORDER BY table_name;