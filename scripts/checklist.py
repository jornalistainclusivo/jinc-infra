#!/usr/bin/env python
"""
checklist.py — Verificação de qualidade do projeto JINC
Protocolo DevOps JINC v1.2 — 2026 Edition
Mandatório antes de qualquer merge/commit em main.
"""

import sys
import os
import json
import subprocess
from pathlib import Path
from datetime import datetime

# ─── Configuração de Requisitos ───────────────────────────────────────────────

REQUIRED_FRONTEND_FILES = [
    "jinc-frontend/lib/api.ts",
    "jinc-frontend/lib/strapi-types.ts",
    "jinc-frontend/app/layout.tsx",
    "jinc-frontend/app/page.tsx",
    "jinc-frontend/next.config.ts",
    "jinc-frontend/package.json",
]

REQUIRED_FRONTEND_COMPONENTS = [
    "jinc-frontend/components/news/TagBadge.tsx",
    "jinc-frontend/components/news/MediaGallery.tsx",
    "jinc-frontend/components/news/ShareBlock.tsx",
    "jinc-frontend/components/news/BlockMapper.tsx",
]

REQUIRED_FRONTEND_PAGES = [
    "jinc-frontend/app/artigo/[slug]/page.tsx",
    "jinc-frontend/app/tag/[slug]/page.tsx",
]

REQUIRED_CMS_FILES = [
    "cms/src/api/artigo/content-types/artigo/schema.json",
    "cms/src/api/autor/content-types/autor/schema.json",
    "cms/src/api/tag/content-types/tag/schema.json",
    "cms/src/api/categoria/content-types/categoria/schema.json",
    "cms/src/components/digital-media/midias.json",
    "cms/types/generated/components.d.ts",
]

STRAPI_SCHEMA_REQUIRED_FIELDS = {
    "cms/src/api/artigo/content-types/artigo/schema.json": ["titulo", "slug", "categoria", "tags", "midias"],
    "cms/src/api/categoria/content-types/categoria/schema.json": ["nome", "slug"],
    "cms/src/api/tag/content-types/tag/schema.json": ["tag", "slug"],
}

API_POPULATE_CHECKS = [
    ("tags", "jinc-frontend/lib/api.ts"),
    ("midias", "jinc-frontend/lib/api.ts"),
    ("categoria", "jinc-frontend/lib/api.ts"),
]

# ─── Helpers de Status ────────────────────────────────────────────────────────

PASS = "✅ PASS"
FAIL = "❌ FAIL"
WARN = "⚠️  WARN"

results = []

def check(label: str, passed: bool, detail: str = "", warn: bool = False) -> None:
    status = PASS if passed else (WARN if warn else FAIL)
    results.append((status, label, detail))
    icon = "✅" if passed else ("⚠️" if warn else "❌")
    print(f"  {icon} {label}" + (f" — {detail}" if detail else ""))

def section(title: str) -> None:
    print(f"\n{'─' * 60}")
    print(f"  {title}")
    print(f"{'─' * 60}")

# ─── Motores de Verificação ───────────────────────────────────────────────────

def check_required_files(root: Path) -> None:
    section("📁 Arquivos Obrigatórios")
    groups = [
        ("Frontend Core", REQUIRED_FRONTEND_FILES),
        ("Components", REQUIRED_FRONTEND_COMPONENTS),
        ("Pages", REQUIRED_FRONTEND_PAGES),
        ("CMS Core", REQUIRED_CMS_FILES)
    ]
    for label, files in groups:
        for f in files:
            p = root / f
            exists = p.exists()
            check(f"{label}: {f}", exists, "" if exists else "Arquivo não encontrado")

def check_strapi_schemas(root: Path) -> None:
    section("🔍 Validação dos Schemas Strapi")
    for schema_path, required_fields in STRAPI_SCHEMA_REQUIRED_FIELDS.items():
        p = root / schema_path
        if not p.exists():
            check(schema_path, False, "Schema não encontrado")
            continue
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            attributes = data.get("attributes", {})
            for field in required_fields:
                has_field = field in attributes
                check(f"{schema_path} → {field}", has_field, 
                      "" if has_field else f"Campo '{field}' ausente")
        except json.JSONDecodeError as e:
            check(schema_path, False, f"JSON inválido: {e}")

def check_api_populate(root: Path) -> None:
    section("📡 API Layer — Populate Checks")
    for keyword, filepath in API_POPULATE_CHECKS:
        p = root / filepath
        if not p.exists():
            check(filepath, False, "Arquivo de API não encontrado")
            continue
        content = p.read_text(encoding="utf-8")
        found = keyword in content
        check(f"Populate: {keyword}", found, "" if found else f"'{keyword}' ausente em api.ts")

def check_env_safety(root: Path) -> None:
    section("🔐 Segurança — Secrets & .env")
    for sub in ["jinc-frontend", "cms"]:
        repo_dir = root / sub
        if not repo_dir.exists():
            check(f"Pasta {sub}", False, "Diretório não encontrado", warn=True)
            continue

        # Check .gitignore local
        gitignore = repo_dir / ".gitignore"
        if gitignore.exists():
            has_env = ".env" in gitignore.read_text(encoding="utf-8")
            check(f"{sub}/.gitignore protege .env", has_env, "" if has_env else "ALERTA: .env não está no gitignore")
        
        # Check Git Index (Tracked files)
        try:
            # shell=True necessário em alguns ambientes Windows para localizar o binário do git corretamente
            result = subprocess.run(
                ["git", "ls-files", "--error-unmatch", ".env"],
                cwd=str(repo_dir), capture_output=True, text=True, check=False
            )
            tracked = (result.returncode == 0)
            check(f"{sub}: .env não rastreado", not tracked, "ERRO: .env está no cache do Git!" if tracked else "")
        except FileNotFoundError:
            check(f"{sub}: Git status", False, "Executável 'git' não encontrado no PATH", warn=True)

def check_accessibility_basics(root: Path) -> None:
    section("♿ Acessibilidade (Focus & Aria)")
    news_dir = root / "jinc-frontend" / "components" / "news"
    if news_dir.exists():
        for tsx_file in news_dir.glob("*.tsx"):
            content = tsx_file.read_text(encoding="utf-8")
            if any(tag in content for tag in ["<button", "<Link", "<a "]):
                has_focus = "focus-visible" in content or "focus:outline" in content
                check(f"Focus: {tsx_file.name}", has_focus, "" if has_focus else "Sem focus-visible", warn=not has_focus)

def check_typescript_types(root: Path) -> None:
    section("🔷 TypeScript Integrity")
    types_file = root / "jinc-frontend" / "lib" / "strapi-types.ts"
    if types_file.exists():
        content = types_file.read_text(encoding="utf-8")
        for iface in ["StrapiArtigo", "StrapiTag", "StrapiCategoria"]:
            check(f"Interface {iface}", iface in content, "" if iface in content else f"{iface} ausente")
        
        any_count = content.count(": any")
        check("Uso de 'any'", any_count <= 2, f"{any_count} encontrados", warn=any_count > 2)

# ─── Relatório e Execução ─────────────────────────────────────────────────────

def print_summary() -> int:
    section("📊 Relatório Final")
    fails = sum(1 for r in results if r[0] == FAIL)
    warns = sum(1 for r in results if r[0] == WARN)
    
    print(f"\n  Total: {len(results)} | FAIHURES: {fails} | WARNINGS: {warns}")
    print(f"  Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    if fails > 0:
        print(f"\n  {FAIL} — Corrija os erros acima antes de prosseguir.\n")
        return 1
    print(f"\n  {PASS} — Projeto JINC validado com sucesso! ✨\n")
    return 0

def main():
    # Detecta a raiz do projeto baseada na localização deste script (assumindo /scripts/checklist.py)
    script_path = Path(__file__).resolve()
    root = script_path.parent.parent 

    print(f"\n{'═' * 60}")
    print(f"  🎯 JINC DevOps Checklist — v1.2")
    print(f"  Runtime: Python {sys.version.split()[0]}")
    print(f"  Root: {root}")
    print(f"{'═' * 60}")

    if not (root / "jinc-frontend").exists() and not (root / "cms").exists():
        print(f"❌ ERRO: Script executado fora da estrutura JINC. Verifique o path: {root}")
        sys.exit(1)

    check_required_files(root)
    check_strapi_schemas(root)
    check_api_populate(root)
    check_env_safety(root)
    check_accessibility_basics(root)
    check_typescript_types(root)

    sys.exit(print_summary())

if __name__ == "__main__":
    main()
