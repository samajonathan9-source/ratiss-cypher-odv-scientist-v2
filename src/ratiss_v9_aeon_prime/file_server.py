
# -*- coding: utf-8 -*-
"""
================================================================================
          SERVEUR DE GESTION ET D'IMPORTATION DE FICHIERS — RATISS V9
================================================================================
Propriété Intellectuelle : JohnKing0 & Architecte Jonathan Evina
Version du Système       : RATISS V9 AEON PRIME - INTEGRATED QUANTUM ECOSYSTEM
ID ORCID de l'Auteur     : 0009-0000-4092-5313
Ancrage DOI Académique   : 10.17605/OSF.IO/6JZMB
================================================================================

Ce script fournit les endpoints d'API REST pour la manipulation, le téléchargement (upload)
et l'extraction automatisée des fichiers au sein du workspace de RATISS. Il complète
le serveur REST universel en s'interfaçant avec le FileManager.

---
ENDPOINTS DE GESTION DE CONTENU :
- GET    /api/files             : Énumère tous les fichiers du workspace avec métadonnées.
- GET    /api/file/{filename}   : Télécharge ou affiche le contenu brut d'un fichier.
- POST   /api/upload            : Importation sécurisée multipart d'un fichier client.
- GET    /api/convert/{filename}: Convertit à la volée le fichier complexe en Markdown/Text.
- DELETE /api/file/{filename}   : Supprime de manière permanente un fichier du workspace.

================================================================================
"""

import os
import sys
from fastapi import APIRouter, UploadFile, File, HTTPException, status
from fastapi.responses import FileResponse, JSONResponse

# Imports locaux sécurisés
from ratiss_v9_aeon_prime.file_manager import FileManager

# Initialisation du routeur FastAPI pour inclusion globale
router = APIRouter(prefix="/api/workspace", tags=["Workspace File Management"])
fm = FileManager()


@router.get("/files")
def list_workspace_files():
    """Liste tous les fichiers stockés dans le workspace de RATISS."""
    try:
        files = fm.list_files(".")
        return {"status": "success", "count": len(files), "files": files}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Impossible de lister les fichiers : {str(e)}"
        )


@router.get("/file/{filename:path}")
def download_file(filename: str):
    """Télécharge le fichier brut du workspace spécifié."""
    try:
        safe_path = fm._resolve_safe_path(filename)
        if not os.path.exists(safe_path) or os.path.isdir(safe_path):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Le fichier '{filename}' n'existe pas ou est un dossier."
            )
        return FileResponse(safe_path, filename=os.path.basename(safe_path))
    except PermissionError as pe:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(pe))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """
    Importation sécurisée par fichier unique multipart (upload) dans le workspace.
    """
    try:
        # Nettoyage et sécurisation du nom de fichier
        filename = os.path.basename(file.filename)
        safe_path = fm._resolve_safe_path(filename)
        
        # Écrit le contenu téléversé par blocs
        with open(safe_path, "wb") as buffer:
            while content := await file.read(1024 * 64): # Blocs de 64 ko
                buffer.write(content)
                
        return {
            "status": "success",
            "message": f"Fichier '{filename}' importé avec succès.",
            "filename": filename,
            "size_bytes": os.path.getsize(safe_path)
        }
    except PermissionError as pe:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(pe))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de l'importation du fichier: {str(e)}"
        )


@router.get("/convert/{filename:path}")
def convert_file_for_llm(filename: str):
    """
    Retourne la version textuelle convertie du document à la volée (sans LLM)
    pour alimenter le contexte d'un agent.
    """
    try:
        text_content = fm.convert_to_text(filename)
        return {
            "status": "success",
            "filename": filename,
            "conversion_type": "plain_text_markdown",
            "content": text_content
        }
    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Le fichier '{filename}' est introuvable pour la conversion."
        )
    except PermissionError as pe:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(pe))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.delete("/file/{filename:path}")
def delete_workspace_file(filename: str):
    """Supprime un fichier ou un dossier du workspace."""
    try:
        msg = fm.delete_file(filename)
        return {"status": "success", "message": msg}
    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Impossible de supprimer '{filename}' : Fichier introuvable."
        )
    except PermissionError as pe:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(pe))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
