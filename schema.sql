-- Extension pour fonctions avancées (optionnelle)
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ============================================================
-- 1. Table des programmes (normalisation des filières)
-- ============================================================
CREATE TABLE programs (
    id SERIAL PRIMARY KEY,
    code VARCHAR(10) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    description TEXT
);

-- ============================================================
-- 2. Table des utilisateurs
-- ============================================================
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100),
    email VARCHAR(120) UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role VARCHAR(20) CHECK (role IN ('student', 'admin', 'advisor')),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- 3. Table des ambassadeurs (anciennement ambassadeurs)
-- ============================================================
CREATE TABLE ambassadors (
    id SERIAL PRIMARY KEY,
    nom VARCHAR(100) NOT NULL,
    program_id INTEGER REFERENCES programs(id) ON DELETE SET NULL,
    niveau VARCHAR(50) NOT NULL CHECK (niveau IN ('1ère année', '2ème année', '3ème année')),
    email VARCHAR(150),
    whatsapp VARCHAR(20),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Index pour les ambassadeurs
CREATE INDEX idx_ambassadors_program_active ON ambassadors(program_id, is_active);

-- ============================================================
-- 4. Table des disponibilités des ambassadeurs
-- ============================================================
CREATE TABLE ambassador_availability (
    id SERIAL PRIMARY KEY,
    ambassador_id INTEGER REFERENCES ambassadors(id) ON DELETE CASCADE,
    available_date DATE NOT NULL,
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT check_start_end CHECK (start_time < end_time)
);

-- Index pour accélérer les recherches de disponibilités
CREATE INDEX idx_amb_avail_ambassador ON ambassador_availability(ambassador_id);

-- ============================================================
-- 5. Table des demandes de peer matching (anciennement demandes_peermatch)
-- ============================================================
CREATE TABLE peer_match_requests (
    id SERIAL PRIMARY KEY,
    ambassador_id INTEGER REFERENCES ambassadors(id) ON DELETE SET NULL,
    prenom_etudiant VARCHAR(100),
    email_etudiant VARCHAR(150),
    program_id INTEGER REFERENCES programs(id) ON DELETE SET NULL,
    message TEXT,
    statut VARCHAR(20) NOT NULL DEFAULT 'en_attente' CHECK (statut IN ('en_attente', 'contacte', 'ferme')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Index sur les demandes
CREATE INDEX idx_peer_requests_ambassador ON peer_match_requests(ambassador_id);
CREATE INDEX idx_peer_requests_status ON peer_match_requests(statut);

-- ============================================================
-- 6. Table des conversations (chat)
-- ============================================================
CREATE TABLE conversations (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    started_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_conversations_user_id ON conversations(user_id);

-- ============================================================
-- 7. Table des messages
-- ============================================================
CREATE TABLE messages (
    id SERIAL PRIMARY KEY,
    conversation_id INTEGER REFERENCES conversations(id) ON DELETE CASCADE,
    sender VARCHAR(20) CHECK (sender IN ('user', 'bot', 'advisor')),
    content TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_messages_conversation_id ON messages(conversation_id);
CREATE INDEX idx_messages_created_at ON messages(created_at);

-- ============================================================
-- 8. Table des créneaux de disponibilité des conseillers
-- ============================================================
CREATE TABLE availability_slots (
    id SERIAL PRIMARY KEY,
    advisor_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    start_time TIMESTAMPTZ NOT NULL,
    end_time TIMESTAMPTZ NOT NULL,
    is_booked BOOLEAN DEFAULT FALSE,
    CONSTRAINT check_slot_start_end CHECK (start_time < end_time),
    CONSTRAINT unique_advisor_start UNIQUE (advisor_id, start_time)
);

CREATE INDEX idx_availability_slots_advisor ON availability_slots(advisor_id);
CREATE INDEX idx_availability_slots_dates ON availability_slots(start_time, end_time);

-- ============================================================
-- 9. Table des rendez-vous
-- ============================================================
CREATE TABLE appointments (
    id SERIAL PRIMARY KEY,
    student_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    advisor_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    slot_id INTEGER REFERENCES availability_slots(id) ON DELETE CASCADE UNIQUE, -- Un slot ne peut être réservé qu'une fois
    status VARCHAR(20) DEFAULT 'scheduled' CHECK (status IN ('scheduled', 'completed', 'cancelled')),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_appointments_student ON appointments(student_id);
CREATE INDEX idx_appointments_advisor ON appointments(advisor_id);
CREATE INDEX idx_appointments_slot ON appointments(slot_id);
CREATE INDEX idx_appointments_status ON appointments(status);

-- ============================================================
-- 10. Table des logs système
-- ============================================================
CREATE TABLE system_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    action TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_system_logs_user ON system_logs(user_id);
CREATE INDEX idx_system_logs_created ON system_logs(created_at);

-- ============================================================
-- 11. Table des interactions IA (pour l'analytique)
-- ============================================================
CREATE TABLE ai_interactions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    question TEXT,
    detected_language VARCHAR(20),
    intent VARCHAR(100),
    recommended_program_id INTEGER REFERENCES programs(id) ON DELETE SET NULL, -- Référence à la table programs
    eligibility_result VARCHAR(50), -- Si valeurs limitées, ajouter CHECK
    response_time FLOAT, -- en secondes
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_ai_interactions_user ON ai_interactions(user_id);
CREATE INDEX idx_ai_interactions_created ON ai_interactions(created_at);
CREATE INDEX idx_ai_interactions_program ON ai_interactions(recommended_program_id);

-- ============================================================
-- 12. Table des logs de chat (pour le débogage / historique)
-- ============================================================
CREATE TABLE chat_logs (
    id SERIAL PRIMARY KEY,
    user_question TEXT NOT NULL,
    bot_response TEXT NOT NULL,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL, -- Ajout pour lier à un utilisateur si possible
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_chat_logs_user ON chat_logs(user_id);
CREATE INDEX idx_chat_logs_created ON chat_logs(created_at);

