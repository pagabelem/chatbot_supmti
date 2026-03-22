"""
Service de génération de PDF pour les rapports d'orientation.
"""
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from io import BytesIO
from datetime import datetime
from typing import List, Dict, Any, Optional
import unicodedata

from app.database.models import Student, Program, Interest, StudentInterest
from app.core.logging import logger
from sqlalchemy.orm import Session

# Importer la fonction de comparaison
from app.api.routes.compare import get_career_by_keywords

class PDFService:
    """Service de génération de rapports PDF"""
    
    def __init__(self, db: Session = None):
        self.styles = getSampleStyleSheet()
        self._setup_styles()
        self.db = db
    
    def _setup_styles(self):
        """Configure les styles personnalisés pour le PDF"""
        # Style pour le titre principal
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#003366'),
            spaceAfter=30,
            alignment=1  # Centre
        ))
        
        # Style pour les sous-titres
        self.styles.add(ParagraphStyle(
            name='CustomHeading',
            parent=self.styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#003366'),
            spaceAfter=12,
            spaceBefore=12
        ))
        
        # Style pour le texte normal
        self.styles.add(ParagraphStyle(
            name='CustomNormal',
            parent=self.styles['Normal'],
            fontSize=11,
            textColor=colors.black,
            spaceAfter=6
        ))
        
        # Style pour les informations importantes
        self.styles.add(ParagraphStyle(
            name='Important',
            parent=self.styles['Normal'],
            fontSize=12,
            textColor=colors.HexColor('#006600'),
            spaceAfter=6
        ))
        
        # Style pour les scores élevés
        self.styles.add(ParagraphStyle(
            name='HighScore',
            parent=self.styles['Normal'],
            fontSize=12,
            textColor=colors.HexColor('#006600'),
            spaceAfter=6,
            alignment=1
        ))
    
    def generate_orientation_report(self, student: Student, recommendations: List[Dict[str, Any]]) -> BytesIO:
        """
        Génère un rapport PDF pour un étudiant.
        
        Args:
            student: Objet Student SQLAlchemy
            recommendations: Liste des programmes recommandés avec scores
        
        Returns:
            BytesIO: Contenu du PDF
        """
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=2*cm,
            leftMargin=2*cm,
            topMargin=2*cm,
            bottomMargin=2*cm
        )
        
        # Conteneur pour les éléments du PDF
        story = []
        
        # === 1. Titre ===
        title = Paragraph("Rapport d'Orientation Académique", self.styles['CustomTitle'])
        story.append(title)
        
        # === 2. Date ===
        date_str = datetime.now().strftime("%d %B %Y")
        date = Paragraph(f"Date : {date_str}", self.styles['CustomNormal'])
        story.append(date)
        story.append(Spacer(1, 20))
        
        # === 3. Informations étudiant ===
        story.append(Paragraph("Informations personnelles", self.styles['CustomHeading']))
        
        # Récupérer le nom de l'utilisateur
        user_name = "Non renseigné"
        if student.user:
            user_name = student.user.full_name
        
        student_info = [
            ["Nom complet :", user_name],
            ["Niveau :", student.level or "Non renseigné"],
            ["Bac :", student.bac_type or "Non renseigné"],
            ["Ville :", student.city or "Non renseigné"],
        ]
        
        info_table = Table(student_info, colWidths=[120, 350])
        info_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#003366')),
            ('TEXTCOLOR', (1, 0), (1, -1), colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        story.append(info_table)
        story.append(Spacer(1, 20))
        
        # === 4. Centres d'intérêt ===
        story.append(Paragraph("Centres d'intérêt", self.styles['CustomHeading']))
        
        # Récupérer les intérêts de l'étudiant
        interests = self._get_student_interests(student)
        interests_text = ", ".join(interests) if interests else "Non renseignés"
        interests_para = Paragraph(interests_text, self.styles['CustomNormal'])
        story.append(interests_para)
        story.append(Spacer(1, 20))
        
        # === 5. Recommandations ===
        story.append(Paragraph("Programmes recommandés", self.styles['CustomHeading']))
        
        if recommendations:
            # Créer les données du tableau
            rec_data = [["#", "Programme", "Score", "Débouchés"]]
            for i, rec in enumerate(recommendations, 1):
                score = rec.get('score', 0)
                score_text = f"{score}%"
                
                # Nettoyer le nom du programme
                program_name = rec.get('name', '')
                
                rec_data.append([
                    str(i),
                    program_name,
                    score_text,
                    rec.get('career_opportunities', 'Consulter documentation')
                ])
            
            rec_table = Table(rec_data, colWidths=[30, 150, 60, 280])
            
            # Style de base
            table_style = [
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#003366')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('FONTSIZE', (0, 1), (-1, -1), 10),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('WORDWRAP', (1, 1), (1, -1), True),
            ]
            
            # Colorer les scores selon leur valeur
            for i, rec in enumerate(recommendations, 1):
                score = rec.get('score', 0)
                if score >= 75:
                    table_style.append(('TEXTCOLOR', (2, i), (2, i), colors.HexColor('#006600')))
                elif score >= 50:
                    table_style.append(('TEXTCOLOR', (2, i), (2, i), colors.HexColor('#FF8C00')))
                else:
                    table_style.append(('TEXTCOLOR', (2, i), (2, i), colors.HexColor('#8B0000')))
            
            rec_table.setStyle(TableStyle(table_style))
            story.append(rec_table)
        else:
            story.append(Paragraph("Aucune recommandation disponible pour le moment.", self.styles['CustomNormal']))
        
        story.append(Spacer(1, 30))
        
        # === 6. Pied de page ===
        footer_text = "Rapport généré par le système d'orientation intelligent de SUP MTI Meknès"
        footer = Paragraph(footer_text, self.styles['CustomNormal'])
        story.append(footer)
        
        # Générer le PDF
        doc.build(story)
        buffer.seek(0)
        
        logger.info(f"✅ PDF généré pour l'étudiant {student.id}")
        return buffer
    
    def _get_student_interests(self, student: Student) -> List[str]:
        """
        Récupère les centres d'intérêt d'un étudiant de manière fiable.
        """
        interests = []
        
        # Méthode 1: Utiliser la relation si elle est chargée
        if hasattr(student, 'student_interests') and student.student_interests:
            for si in student.student_interests:
                if hasattr(si, 'interest') and si.interest:
                    interests.append(si.interest.name)
            if interests:
                return interests
        
        # Méthode 2: Faire une requête directe si on a une session DB
        if self.db and student.id:
            try:
                interest_records = self.db.query(Interest).join(
                    StudentInterest
                ).filter(
                    StudentInterest.student_id == student.id
                ).all()
                interests = [i.name for i in interest_records]
                logger.debug(f"Intérêts récupérés via requête directe: {interests}")
            except Exception as e:
                logger.error(f"Erreur lors de la récupération des intérêts: {e}")
        
        return interests


# === FONCTION DE NORMALISATION ===
def normalize_text(text: str) -> str:
    """
    Normalise un texte en enlevant les accents et caractères spéciaux.
    """
    normalized = unicodedata.normalize('NFKD', text)
    normalized = normalized.encode('ASCII', 'ignore').decode('utf-8')
    return normalized.lower()


# === FONCTION AMÉLIORÉE DE CALCUL DES SCORES ===
def calculate_scores(interests: List[str], programs: List[Program]) -> List[Dict[str, Any]]:
    """
    Calcule les scores de compatibilité entre les intérêts et les programmes.
    Version améliorée avec pondération et meilleure correspondance.
    """
    results = []
    
    # Si pas d'intérêts, retourner les programmes avec score 0
    if not interests:
        for program in programs:
            results.append({
                'id': str(program.id),
                'name': program.name,
                'score': 0,
                'career_opportunities': get_career_by_keywords(program.name)
            })
        return results
    
    # Normaliser les intérêts
    normalized_interests = [normalize_text(interest) for interest in interests]
    
    for program in programs:
        score = 0
        program_name = program.name
        program_lower = normalize_text(program_name)
        
        # Mots-clés importants par domaine
        keywords_map = {
            "ia": ["ia", "intelligence", "artificielle", "machine learning", "deep learning", "ml", "dl"],
            "data": ["data", "science", "big data", "analyse", "statistique", "datascience"],
            "cyber": ["cyber", "securite", "securit", "hacking", "cryptographie", "secur"],
            "logiciel": ["logiciel", "software", "developpement", "programmation", "code", "dev"],
            "cloud": ["cloud", "computing", "aws", "azure", "devops", "docker"],
            "reseau": ["reseau", "res", "telecom", "5g", "iot", "infrastructure"],
            "management": ["management", "manage", "gestion", "projet", "rh", "strategie"],
            "finance": ["finance", "audit", "comptabilite", "gestion", "risque", "compta"]
        }
        
        # Vérifier chaque intérêt
        for norm_interest in normalized_interests:
            # Correspondance directe dans le nom du programme
            if norm_interest in program_lower:
                score += 30
                continue
            
            # Vérifier les mots-clés du domaine
            for domain, keywords in keywords_map.items():
                if any(keyword in norm_interest for keyword in keywords):
                    if domain in program_lower or any(keyword in program_lower for keyword in keywords):
                        score += 25
                        break
            else:
                # Correspondance partielle (mots individuels)
                interest_words = norm_interest.split()
                for word in interest_words:
                    if len(word) > 3 and word in program_lower:
                        score += 10
                        break
        
        # Bonus pour les correspondances multiples
        matched_domains = set()
        for domain, keywords in keywords_map.items():
            if any(keyword in program_lower for keyword in keywords):
                for norm_interest in normalized_interests:
                    if any(keyword in norm_interest for keyword in keywords):
                        matched_domains.add(domain)
        
        score += len(matched_domains) * 5
        
        # Arrondir et limiter à 100
        score = min(round(score), 100)
        
        results.append({
            'id': str(program.id),
            'name': program_name,
            'score': score,
            'career_opportunities': get_career_by_keywords(program_name)
        })
    
    # Trier par score décroissant
    results.sort(key=lambda x: x['score'], reverse=True)
    return results