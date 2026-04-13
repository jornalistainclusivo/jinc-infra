import requests
import re
from bs4 import BeautifulSoup
import unicodedata

# --- CONFIGURAÇÕES ---
STRAPI_URL = "http://localhost:1337"
STRAPI_TOKEN = "TOKEN_REMOVIDO_POR_SEGURANCA"
WP_API_BASE = "https://jornalistainclusivo.com/wp-json/wp/v2"

SYSTEM_INSTRUCTION = """
Você é um assistente especializado em acessibilidade e jornalismo inclusivo. 
Gere os dados para o Strapi 5 no formato AST de Blocks.
Exemplo Few-Shot exigido para o bloco 'contextual-layer':
{
  "__component": "blocos-materia.contextual-layer",
  "title": "Glossário Inclusivo",
  "layout": "multi_column",
  "items": [
    {
      "heading": "Nome do Termo",
      "description": [
        {
          "type": "paragraph",
          "children": [{ "type": "text", "text": "A IA deve gerar a explicação aqui..." }]
        }
      ]
    }
  ]
}
"""
headers = {"Authorization": f"Bearer {STRAPI_TOKEN}"}
headers_aws = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}

# --- FAXINA DE RASCUNHOS ---

def cleanup_drafts():
    print("--- Faxina: Excluindo rascunhos anteriores ---")
    res = requests.get(f"{STRAPI_URL}/api/artigos?status=draft", headers=headers).json()
    if res.get('data'):
        for doc in res['data']:
            doc_id = doc['documentId']
            requests.delete(f"{STRAPI_URL}/api/artigos/{doc_id}", headers=headers)
            print(f"  [-] Deletado: {doc_id}")

# --- PROCESSAMENTO DE CONTEÚDO (LINKS E FORMATAÇÃO) ---

def html_to_strapi_blocks(html):
    """Converte HTML para o formato de blocos JSON do Strapi 5 mantendo links e negrito."""
    soup = BeautifulSoup(html, 'html.parser')
    blocks = []
    
    # Iteramos por parágrafos e cabeçalhos para manter a estrutura
    for tag in soup.find_all(['p', 'h2', 'h3']):
        if any(x in tag.text for x in ["#Audiodescrição", "#DescriçãoDaImagem"]):
            continue
            
        # Define o tipo de bloco
        block_type = "paragraph"
        if tag.name == 'h2': block_type = "heading"
        
        block = {"type": block_type, "children": []}
        if block_type == "heading": block["level"] = 2

        for child in tag.children:
            if child.name == 'a': # Trata Links
                block["children"].append({
                    "type": "link",
                    "url": child.get('href'),
                    "children": [{"type": "text", "text": child.get_text()}]
                })
            elif child.name in ['strong', 'b']: # Trata Negrito
                block["children"].append({"type": "text", "text": child.get_text(), "bold": True})
            elif child.name == 'em': # Trata Itálico
                block["children"].append({"type": "text", "text": child.get_text(), "italic": True})
            else:
                text = str(child)
                if text.strip() and not text.startswith('<'):
                    block["children"].append({"type": "text", "text": text})
        
        if block["children"]:
            blocks.append(block)
            
    return blocks

# --- UPLOAD DE MÍDIA ---

def upload_capa(wp_media_id):
    if not wp_media_id: return None
    try:
        media = requests.get(f"{WP_API_BASE}/media/{wp_media_id}", timeout=10).json()
        img_url = media.get('source_url')
        img_res = requests.get(img_url, headers=headers_aws, timeout=20)
        if img_res.status_code == 200:
            files = {'files': (img_url.split('/')[-1], img_res.content, media.get('mime_type', 'image/jpeg'))}
            res = requests.post(f"{STRAPI_URL}/api/upload", headers=headers, files=files)
            return res.json()[0]['id']
    except: pass
    return None

# --- MIGRAÇÃO ---

def migrate(limit=10):
    cleanup_drafts()
    print(f"\n--- Iniciando Migração V2.2 ({limit} posts) ---")
    posts = requests.get(f"{WP_API_BASE}/posts?per_page={limit}").json()

    for i, wp in enumerate(posts):
        # Captura audiodescrição para acessibilidade
        soup = BeautifulSoup(wp['content']['rendered'], 'html.parser')
        acc = ""
        for p in soup.find_all('p'):
            if "#Audiodescrição" in p.text:
                acc = p.text.replace("#Audiodescrição:", "").strip()
                break
        
        formatted_blocks = html_to_strapi_blocks(wp['content']['rendered'])
        
        # Rank Math / Yoast Fallback
        wp_seo = wp.get('yoast_head_json', {})
        
        payload = {
            "data": {
                "titulo": wp['title']['rendered'],
                "slug": wp['slug'],
                "subtitulo": "", # Será preenchido pela IA
                "resumo_simples": BeautifulSoup(wp['excerpt']['rendered'], 'html.parser').get_text().strip(),
                "descricao_audio": acc,
                "alt_text_ia": acc,
                "data_publicacao": wp['date'].split('T')[0],
                "capa": upload_capa(wp.get('featured_media')),
                "locale": "pt-BR",
                "blocos_de_conteudo": [
                    {
                        "__component": "blocos-materia.texto-livre", 
                        "texto": formatted_blocks
                    }
                ],
                # Ajustado para 'seo' em caixa baixa e inicializando structuredData
                "seo": {
                    "metaTitle": wp_seo.get('title', wp['title']['rendered'][:60]),
                    "metaDescription": wp_seo.get('description', ""),
                    "keywords": "",
                    "structuredData": {} # Inicia como objeto vazio em vez de null
                },
                "publishedAt": None
            }
        }
        
        res = requests.post(f"{STRAPI_URL}/api/artigos", headers=headers, json=payload)
        if res.status_code in [200, 201]:
            print(f"[{i+1}/{len(posts)}] Sucesso: {wp['slug']}")
        else:
            print(f"[{i+1}/{len(posts)}] Erro: {res.text}")

if __name__ == "__main__":
    migrate(limit=10)
