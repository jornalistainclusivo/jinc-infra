"""Utilitário para converter HTML (WordPress) em Strapi 5 Blocks AST.

Uso:
    from tools.html_converter import html_to_strapi_blocks

    blocks = html_to_strapi_blocks("<p>Texto <strong>negrito</strong></p>")
"""

from bs4 import BeautifulSoup, Tag


def html_to_strapi_blocks(html: str) -> list[dict]:
    """Converte HTML para o formato de blocos JSON do Strapi 5.

    Suporta: parágrafos, headings (h2/h3), links, negrito, itálico.
    Filtra blocos de audiodescrição (#Audiodescrição, #DescriçãoDaImagem).
    """
    soup = BeautifulSoup(html, "html.parser")
    blocks: list[dict] = []

    for tag in soup.find_all(["p", "h2", "h3"]):
        if any(marker in tag.text for marker in ["#Audiodescrição", "#DescriçãoDaImagem"]):
            continue

        block_type = "heading" if tag.name in ("h2", "h3") else "paragraph"
        block: dict = {"type": block_type, "children": []}

        if block_type == "heading":
            block["level"] = 2 if tag.name == "h2" else 3

        for child in tag.children:
            if isinstance(child, Tag):
                if child.name == "a":
                    block["children"].append({
                        "type": "link",
                        "url": child.get("href", ""),
                        "children": [{"type": "text", "text": child.get_text()}],
                    })
                elif child.name in ("strong", "b"):
                    block["children"].append({"type": "text", "text": child.get_text(), "bold": True})
                elif child.name == "em":
                    block["children"].append({"type": "text", "text": child.get_text(), "italic": True})
            else:
                text = str(child).strip()
                if text:
                    block["children"].append({"type": "text", "text": str(child)})

        if block["children"]:
            blocks.append(block)

    return blocks
