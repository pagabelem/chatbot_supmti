"""
Service OCR pour extraire du texte d'images.
"""
import easyocr
import cv2
import numpy as np
import re
from fastapi import UploadFile
import io
from PIL import Image
from typing import List, Dict, Any
import os
import fitz  # PyMuPDF pour les PDFs

class OCRService:
    def __init__(self):
        # Initialiser le lecteur avec les langues supportées
        print("🔄 Initialisation du service OCR...")
        
        # Essayer différentes combinaisons
        lang_combinations = [
            ['en', 'fr'],           # Anglais + Français
            ['en'],                  # Anglais seulement
            ['en', 'ar'],            # Anglais + Arabe
            ['fr'],                   # Français seulement
            ['ar', 'en'],             # Arabe + Anglais
        ]
        
        self.reader = None
        for langs in lang_combinations:
            try:
                print(f"🔄 Essai avec {langs}...")
                self.reader = easyocr.Reader(langs, gpu=False)
                print(f"✅ Service OCR prêt avec {langs} !")
                break
            except Exception as e:
                print(f"⚠️ Échec avec {langs}: {e}")
                continue
        
        if self.reader is None:
            raise Exception("Impossible d'initialiser l'OCR avec aucune combinaison de langues")
    
    def preprocess_image(self, img: np.ndarray) -> np.ndarray:
        """
        Améliore la qualité de l'image pour une meilleure reconnaissance OCR.
        """
        # Conversion en niveaux de gris
        if len(img.shape) == 3:
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        else:
            gray = img
        
        # Amélioration du contraste (CLAHE)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        enhanced = clahe.apply(gray)
        
        # Réduction du bruit
        denoised = cv2.fastNlMeansDenoising(enhanced, None, 10, 7, 21)
        
        # Augmentation de la résolution
        height, width = denoised.shape
        if width < 1000:  # Si l'image est trop petite
            scale = 2
            new_width = int(width * scale)
            new_height = int(height * scale)
            denoised = cv2.resize(denoised, (new_width, new_height), interpolation=cv2.INTER_CUBIC)
        
        return denoised
    
    async def process_file(self, file: UploadFile) -> np.ndarray:
        """
        Traite un fichier (image ou PDF) et retourne une image numpy array.
        """
        contents = await file.read()
        
        # Cas 1: PDF
        if file.content_type == 'application/pdf':
            print(f"📄 Conversion PDF en image...")
            pdf_document = fitz.open(stream=contents, filetype="pdf")
            
            # Prendre la première page
            page = pdf_document[0]
            
            # Convertir en image avec résolution améliorée
            zoom = 3  # Résolution plus élevée
            mat = fitz.Matrix(zoom, zoom)
            pix = page.get_pixmap(matrix=mat)
            
            # Convertir pixmap en numpy array
            img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(
                pix.height, pix.width, pix.n
            )
            
            # Si c'est en RGB, convertir en BGR pour OpenCV
            if pix.n == 3:
                img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
            
            pdf_document.close()
            return img
        
        # Cas 2: Image
        elif file.content_type.startswith('image/'):
            nparr = np.frombuffer(contents, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            return img
        
        else:
            raise ValueError(f"Type de fichier non supporté: {file.content_type}")
    
    async def extract_text(self, file: UploadFile) -> Dict[str, Any]:
        """
        Extrait tout le texte d'une image ou PDF uploadé.
        """
        try:
            # Traiter le fichier (image ou PDF)
            img = await self.process_file(file)
            
            # Prétraiter l'image pour améliorer la qualité
            processed_img = self.preprocess_image(img)
            
            # OCR avec paramètres optimisés
            result = self.reader.readtext(
                processed_img,
                paragraph=False,
                contrast_ths=0.1,
                adjust_contrast=0.5,
                text_threshold=0.5,  # Plus sensible
                low_text=0.2,
                link_threshold=0.2,
                canvas_size=2000  # Taille max de l'image
            )
            
            # Formater les résultats
            texts = []
            full_text = []
            
            for (bbox, text, confidence) in result:
                # Ne garder que les textes avec une confiance acceptable
                if confidence > 0.3:  # Seuil minimum
                    texts.append({
                        'text': text,
                        'confidence': float(confidence),
                        'position': [[int(x), int(y)] for x, y in bbox]
                    })
                    full_text.append(text)
            
            return {
                'success': True,
                'filename': file.filename,
                'file_type': file.content_type,
                'texts': texts,
                'full_text': ' '.join(full_text),
                'count': len(texts)
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def extract_name_from_text(self, text: str) -> str | None:
        """
        Extrait le nom et prénom du texte avec des patterns précis.
        """
        # Patterns pour le nom (version française)
        name_patterns = [
            r'Nom\s*[:\s]*([A-Za-z\s]+?)(?:\s+Pr[ée]nom|\s+\d|\s*$)',
            r'Pr[ée]nom\s*[:\s]*([A-Za-z\s]+?)(?:\s+Nom|\s+\d|\s*$)',
            r'[ÉE]tudiant\s*[:\s]*([A-Za-z\s]+)',
            r'N[oô]m\s*et\s*Pr[ée]nom\s*[:\s]*([A-Za-z\s]+)',
            r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3})',  # Capture "Prenom Nom" ou "Nom Prenom"
        ]
        
        # Patterns pour le nom (version anglaise)
        english_patterns = [
            r'Name\s*[:\s]*([A-Za-z\s]+?)(?:\s+Student|\s+\d|\s*$)',
            r'Student\s*[:\s]*([A-Za-z\s]+)',
            r'Full\s*Name\s*[:\s]*([A-Za-z\s]+)',
        ]
        
        all_patterns = name_patterns + english_patterns
        
        for pattern in all_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                name = match.group(1).strip()
                # Nettoyer le nom (enlever les caractères spéciaux)
                name = re.sub(r'[^A-Za-z\s-]', '', name)
                if len(name.split()) >= 2:  # Au moins prénom et nom
                    return name
        
        return None
    
    def extract_grades_from_text(self, text_items: List[Dict]) -> List[Dict]:
        """
        Extrait les notes valides du texte (exclut les matricules et dates).
        """
        grades = []
        
        for item in text_items:
            text = item['text']
            
            # Patterns pour les notes (sur 20)
            grade_patterns = [
                r'(\d{1,2}[.,]?\d*)\s*\/\s*20',  # 15/20
                r'(\d{1,2}[.,]?\d*)\s*\/20',     # 15/20 (sans espace)
                r'(\d{1,2}[.,]?\d*)\s*/\s*20',    # 15 /20
                r'(\d{1,2}[.,]?\d*)/(?:20)?',      # 15/20 simplifié
            ]
            
            # Exclure les nombres trop longs (matricules)
            if len(text.replace(' ', '')) > 15:
                continue
            
            # Exclure les années (2020-2025)
            if re.search(r'20\d{2}', text):
                continue
            
            for pattern in grade_patterns:
                match = re.search(pattern, text)
                if match:
                    grade_value = float(match.group(1).replace(',', '.'))
                    
                    # Ne garder que les notes réalistes (entre 0 et 20)
                    if 0 <= grade_value <= 20:
                        # Essayer d'identifier la matière
                        subject = "Inconnue"
                        subjects = ['math', 'français', 'anglais', 'physique', 'svt', 'histoire', 'géographie']
                        for subj in subjects:
                            if subj in text.lower():
                                subject = subj.capitalize()
                                break
                        
                        grades.append({
                            'text': text,
                            'grade': grade_value,
                            'confidence': item['confidence'],
                            'subject': subject
                        })
                        break
        
        return grades
    
    async def extract_grades_from_bulletin(self, file: UploadFile) -> Dict[str, Any]:
        """
        Spécialisé pour extraire les notes d'un bulletin scolaire.
        """
        # Extraire tout le texte d'abord
        result = await self.extract_text(file)
        
        if not result['success']:
            return result
        
        # Extraire les notes valides
        grades = self.extract_grades_from_text(result['texts'])
        
        return {
            'success': True,
            'filename': file.filename,
            'grades': grades,
            'full_text': result['full_text'],
            'grades_count': len(grades)
        }
    
    async def extract_student_info(self, file: UploadFile) -> Dict[str, Any]:
        """
        Extrait les informations d'un étudiant (nom, niveau, etc.)
        """
        result = await self.extract_text(file)
        
        if not result['success']:
            return result
        
        info = {
            'name': None,
            'bac_type': None,
            'average': None,
            'subjects': []
        }
        
        # Extraire le nom avec les nouveaux patterns
        info['name'] = self.extract_name_from_text(result['full_text'])
        
        # Chercher le type de bac
        bac_patterns = [
            'bac scientifique', 'bac sciences', 'bac maths', 'bac lettres',
            'série scientifique', 'série lettres', 'série économie',
            'baccalauréat scientifique', 'baccalauréat lettres'
        ]
        
        all_text_lower = result['full_text'].lower()
        for bac in bac_patterns:
            if bac in all_text_lower:
                info['bac_type'] = bac.capitalize()
                break
        
        # Extraire les notes et calculer la moyenne
        grades = self.extract_grades_from_text(result['texts'])
        if grades:
            info['average'] = sum(g['grade'] for g in grades) / len(grades)
            info['subjects'] = [g['subject'] for g in grades if g['subject'] != 'Inconnue']
        
        return {
            'success': True,
            'filename': file.filename,
            'student_info': info,
            'full_text': result['full_text']
        }