import requests
import re
from bs4 import BeautifulSoup

# --- CONFIGURAÇÕES ---
STRAPI_URL = "http://localhost:1337"
STRAPI_TOKEN = "53ad474f1479e63c4b45cc31a60128f634fe3a69c0a7b58da597552e33d4cf54c7403541c9f13586aae6e3c7d1ddb417dc3e2ba9945eb97503bb758821430951e7112725b40c5370f98eb0818c928ab1c1bcf4a774ba90e73eb97510a278bf6861aa728152972e36de607c6ebee2d4edd80c895c2d952bc9ff3f9e6628135605"
WP_API_BASE = "https://jornalistainclusivo.com/wp-json/wp/v2"

headers = {"Authorization": f"Bearer {STRAPI_TOKEN}"}
headers_aws = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}

# --- MAPEAMENTOS ---
AUTHOR_MAP = {"5": "Carol Nunes", "23": "Daniela Rorato", "26": "Gabriel Henrique", "28": "Igor Lima", "27": "Karina Almeida", "29": "Mileide Moreira", "11": "Murilo Pereira", "1": "Rafael Ferraz"}
CATEGORY_MAP = {"9": "noticias", "178": "mercado-de-trabalho", "11": "entrevistas", "2131": "neurodiversidade", "2132": "educacao", "52": "paradesporto", "50": "saude", "51": "direitos-pcd", "1754": "direitos-pcd", "3": "direitos-pcd", "49": "artigos", "75": "artigos", "7": "artigos"}

cache = {"autores": {}, "categorias": {}}

def get_or_create_category(wp_cat_id):
    slug = CATEGORY_MAP.get(str(wp_cat_id))
    if not slug: return None
    if slug in cache["categorias"]: return cache["categorias"][slug]
    
    # Busca
    res = requests.get(f"{STRAPI_URL}/api/categorias?filters[slug][$eq]={slug}", headers=headers).json()
    if res.get('data'):
        sid = res['data'][0]['id']
    else:
        # Cria se não existir (O pulo do gato)
        print(f"  [+] Criando Categoria: {slug}")
        new = requests.post(f"{STRAPI_URL}/api/categorias", headers=headers, json={"data": {"nome": slug.capitalize(), "slug": slug}}).json()
        sid = new['data']['id']
    
    cache["categorias"][slug] = sid
    return sid

def get_or_create_author(wp_author_id):
    nome = AUTHOR_MAP.get(str(wp_author_id))
    if not nome: return None
    if nome in cache["autores"]: return cache["autores"][nome]
    
    # Busca
    res = requests.get(f"{STRAPI_URL}/api/autores?filters[nome][$eq]={nome}", headers=headers).json()
    if res.get('data'):
        sid = res['data'][0]['id']
    else:
        # Cria se não existir
        print(f"  [+] Criando Autor: {nome}")
        new = requests.post(f"{STRAPI_URL}/api/autores", headers=headers, json={"data": {"nome": nome}}).json()
        sid = new['data']['id']
    
    cache["autores"][nome] = sid
    return sid

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

def process_content(html):
    soup = BeautifulSoup(html, 'html.parser')
    h2 = soup.find('h2')
    subtitulo = h2.get_text().strip() if h2 else ""
    if h2: h2.decompose()
    
    # Acessibilidade
    acc_text = ""
    for p in soup.find_all('p'):
        if any(x in p.text for x in ["#Audiodescrição", "#DescriçãoDaImagem", "Legenda Descrita"]):
            acc_text = re.sub(r"#.*?:", "", p.text).strip()
            break
            
    # Formato Blocks (Strapi 5)
    body_blocks = [{"type": "paragraph", "children": [{"type": "text", "text": soup.get_text(separator='\n')}]}]
    return subtitulo, acc_text, body_blocks

def migrate(limit=10):
    print(f"--- Iniciando Migração JINC ({limit} posts) ---")
    posts = requests.get(f"{WP_API_BASE}/posts?per_page={limit}").json()
    
    for i, wp in enumerate(posts):
        # Limpeza do Resumo (get_text remove os <p>)
        resumo_limpo = BeautifulSoup(wp['excerpt']['rendered'], 'html.parser').get_text().strip()
        sub, acc, body = process_content(wp['content']['rendered'])
        
        payload = {
            "data": {
                "titulo": wp['title']['rendered'],
                "slug": wp['slug'],
                "subtitulo": sub,
                "resumo_simples": resumo_limpo,
                "descricao_audio": acc,
                "alt_text_ia": acc,
                "data_publicacao": wp['date'].split('T')[0],
                "capa": upload_capa(wp.get('featured_media')),
                "autors": [get_or_create_author(wp['author'])],
                "categoria": get_or_create_category(wp['categories'][0]) if wp['categories'] else None,
                "locale": "pt-BR",
                "legacy_id": str(wp['id']),
                "blocos_de_conteudo": [{"__component": "blocos-materia.texto-livre", "texto": body}],
                "publishedAt": None
            }
        }
        res = requests.post(f"{STRAPI_URL}/api/artigos", headers=headers, json=payload)
        print(f"[{i+1}/{len(posts)}] {wp['slug']} -> {res.status_code}")

if __name__ == "__main__":
    migrate(limit=10)
