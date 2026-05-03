#!/usr/bin/env python3
"""
AyitiKonekte - Marquage i18n des fichiers Python.
Ajoute les imports gettext/gettext_lazy et les wrappers _() dans :
  models.py, serializers.py, views.py, forms.py, services/*.py
"""

import re
import sys
from pathlib import Path

APPS_DIR = Path(
    'C:/Users/wind/Desktop/TRANSVERSAL/MAKET-PEYIZAN-026/MP_web_2026/maket_peyizan/apps'
)

IMPORT_LAZY  = 'from django.utils.translation import gettext_lazy as _'
IMPORT_EAGER = 'from django.utils.translation import gettext as _'

# Fichiers a ignorer completement
SKIP_NAMES = frozenset([
    '__init__.py', 'apps.py', 'urls.py', 'urls_admin.py', 'admin.py',
    'filters.py', 'context_processors.py', 'permissions.py',
    'middleware.py', 'signals.py', 'fcm_service.py', 'fcm_notifications.py',
])

# ─── Classification ───────────────────────────────────────────────────────────

def classify(filepath):
    parts = filepath.parts
    name  = filepath.name
    if 'migrations' in parts:
        return None
    if name in SKIP_NAMES:
        return None
    if 'models' in parts or name == 'models.py':
        return 'model'
    if 'serializers' in parts or name == 'serializers.py':
        return 'serializer'
    if ('views' in parts or name == 'views.py'
            or re.search(r'views.*\.py$', name)
            or name == 'report_generators.py'):
        return 'view'
    if name == 'forms.py':
        return 'form'
    if 'services' in parts:
        return 'service'
    return None


# ─── Import ───────────────────────────────────────────────────────────────────

def has_i18n_import(content):
    return bool(re.search(r'from django\.utils\.translation import', content))

def insert_import(content, import_line):
    if has_i18n_import(content):
        return content, False
    lines = content.split('\n')
    last = -1
    for i, line in enumerate(lines):
        s = line.strip()
        if s.startswith(('import ', 'from ')):
            last = i
    pos = last + 1 if last >= 0 else 0
    lines.insert(pos, import_line)
    return '\n'.join(lines), True


# ─── Helpers ─────────────────────────────────────────────────────────────────

def worth_py(inner):
    """Vaut-il la peine de traduire ce contenu de chaine ?"""
    s = inner.strip()
    if not s or len(s) < 2:
        return False
    # Doit contenir au moins une lettre
    if not re.search(r'[a-zA-Z\u00C0-\u024F]', s):
        return False
    # Identifiant purement interne (snake_case tout minuscule)
    if re.match(r'^[a-z][a-z0-9_]*$', s):
        return False
    # Chemin de fichier ou URL
    if re.match(r'^(?:/|https?://|users/|produits/|payments/|emails/)', s):
        return False
    # Chaine de format seulement
    if re.match(r'^[\s%\{\}s\.d]+$', s):
        return False
    return True

def already_wrapped(prefix):
    """True si le prefix se termine par _( """
    return bool(re.search(r'_\s*\(\s*$', prefix.rstrip()))


# ─── Patterns regex ───────────────────────────────────────────────────────────

# --- Models ---
# verbose_name / verbose_name_plural / help_text = "string"
MODEL_META_RE = re.compile(
    r"((?:verbose_name(?:_plural)?|help_text)\s*=\s*)"
    r"(\"(?:[^\"\\]|\\.)*\"|'(?:[^'\\]|\\.)*')"
)

# TextChoices : VALUE = 'db_val', 'Human Label'
CHOICES_RE = re.compile(
    r"(\s+[A-Z][A-Z0-9_]*\s*=\s*'[^']+'\s*,\s*)"
    r"('(?:[^'\\]|\\.)*'|\"(?:[^\"\\]|\\.)*\")"
)

# --- Serializers + Views ---
# raise ValidationError("msg") / raise ValueError("msg") / raise PermissionDenied("msg")
RAISE_STR_RE = re.compile(
    r"(raise\s+(?:\w+\.)?(?:ValidationError|ValueError|PermissionDenied)\s*\(\s*)"
    r"(\"(?:[^\"\\]|\\.)*\"|'(?:[^'\\]|\\.)*')"
)

# {'field': "error message"} -- dict a une seule cle (ValidationError dicts)
RAISE_DICT_RE = re.compile(
    r"(\{\s*['\"][a-z_]+['\"]\s*:\s*)"
    r"(\"(?:[^\"\\]|\\.)*\"|'(?:[^'\\]|\\.)*')"
    r"(\s*\})"
)

# --- Views & API ---
# 'error': "msg", 'message': "msg", 'detail': "msg" dans les dicts Response
RESPONSE_KEY_RE = re.compile(
    r"((?:'error'|'message'|'detail'|'paiement_erreur'"
    r"|\"error\"|\"message\"|\"detail\"|\"paiement_erreur\")\s*:\s*)"
    r"(\"(?:[^\"\\]|\\.)*\"|'(?:[^'\\]|\\.)*')"
)

# --- Forms ---
# label = "text" dans les definitions de champs
FORM_LABEL_RE = re.compile(
    r"(label\s*=\s*)"
    r"(\"(?:[^\"\\]|\\.)*\"|'(?:[^'\\]|\\.)*')"
)

# Placeholder dans widget attrs : 'placeholder': "text"
WIDGET_PLACEHOLDER_RE = re.compile(
    r"('placeholder'|\"placeholder\")\s*:\s*"
    r"(\"(?:[^\"\\]|\\.)*\"|'(?:[^'\\]|\\.)*')"
)

# error_messages dict : 'required': "msg", 'invalid': "msg"
ERROR_MESSAGES_RE = re.compile(
    r"('(?:required|invalid|max_length|min_length|unique|blank|null)'"
    r"|\"(?:required|invalid|max_length|min_length|unique|blank|null)\")"
    r"(\s*:\s*)"
    r"(\"(?:[^\"\\]|\\.)*\"|'(?:[^'\\]|\\.)*')"
)


# ─── Transformations ──────────────────────────────────────────────────────────

def sub_factory(field_count):
    """Fabrique une fonction de remplacement qui incremente field_count."""
    count = [0]

    def handler_meta(m):
        prefix, s = m.group(1), m.group(2)
        inner = s[1:-1]
        if already_wrapped(prefix) or not worth_py(inner):
            return m.group(0)
        count[0] += 1
        return prefix + '_(' + s + ')'

    def handler_choice(m):
        prefix, s = m.group(1), m.group(2)
        inner = s[1:-1]
        if already_wrapped(prefix) or not worth_py(inner):
            return m.group(0)
        count[0] += 1
        return prefix + '_(' + s + ')'

    def handler_raise(m):
        prefix, s = m.group(1), m.group(2)
        inner = s[1:-1]
        if already_wrapped(prefix) or not worth_py(inner):
            return m.group(0)
        count[0] += 1
        return prefix + '_(' + s + ')'

    def handler_raise_dict(m):
        prefix, s, suffix = m.group(1), m.group(2), m.group(3)
        inner = s[1:-1]
        if already_wrapped(prefix) or not worth_py(inner):
            return m.group(0)
        count[0] += 1
        return prefix + '_(' + s + ')' + suffix

    def handler_response(m):
        prefix, s = m.group(1), m.group(2)
        inner = s[1:-1]
        if already_wrapped(prefix) or not worth_py(inner):
            return m.group(0)
        count[0] += 1
        return prefix + '_(' + s + ')'

    def handler_form_label(m):
        prefix, s = m.group(1), m.group(2)
        inner = s[1:-1]
        if already_wrapped(prefix) or not worth_py(inner):
            return m.group(0)
        count[0] += 1
        return prefix + '_(' + s + ')'

    def handler_error_msg(m):
        key, sep, s = m.group(1), m.group(2), m.group(3)
        inner = s[1:-1]
        if already_wrapped(sep) or not worth_py(inner):
            return m.group(0)
        count[0] += 1
        return key + sep + '_(' + s + ')'

    return (count, handler_meta, handler_choice, handler_raise,
            handler_raise_dict, handler_response, handler_form_label,
            handler_error_msg)


def transform_model(content):
    (count, h_meta, h_choice, _, _, _, _, _) = sub_factory(0)
    content = MODEL_META_RE.sub(h_meta, content)
    content = CHOICES_RE.sub(h_choice, content)
    return content, count[0]


def transform_serializer(content):
    (count, _, _, h_raise, h_raise_dict, _, _, h_err) = sub_factory(0)
    content = RAISE_STR_RE.sub(h_raise, content)
    content = RAISE_DICT_RE.sub(h_raise_dict, content)
    content = ERROR_MESSAGES_RE.sub(h_err, content)
    return content, count[0]


def transform_view(content):
    (count, _, _, h_raise, h_raise_dict, h_resp, _, _) = sub_factory(0)
    content = RESPONSE_KEY_RE.sub(h_resp, content)
    content = RAISE_STR_RE.sub(h_raise, content)
    content = RAISE_DICT_RE.sub(h_raise_dict, content)
    return content, count[0]


def transform_form(content):
    (count, _, _, h_raise, h_raise_dict, _, h_label, h_err) = sub_factory(0)
    content = FORM_LABEL_RE.sub(h_label, content)
    content = ERROR_MESSAGES_RE.sub(h_err, content)
    content = RAISE_STR_RE.sub(h_raise, content)
    content = RAISE_DICT_RE.sub(h_raise_dict, content)
    return content, count[0]


def transform_service(content):
    # Services : uniquement les exceptions a message utilisateur
    (count, _, _, h_raise, h_raise_dict, _, _, _) = sub_factory(0)
    content = RAISE_STR_RE.sub(h_raise, content)
    content = RAISE_DICT_RE.sub(h_raise_dict, content)
    return content, count[0]


# ─── Traitement fichier ───────────────────────────────────────────────────────

TRANSFORM = {
    'model':      (IMPORT_LAZY,  transform_model),
    'serializer': (IMPORT_LAZY,  transform_serializer),
    'view':       (IMPORT_EAGER, transform_view),
    'form':       (IMPORT_LAZY,  transform_form),
    'service':    (IMPORT_EAGER, transform_service),
}


def process_file(filepath, ftype):
    original = filepath.read_text(encoding='utf-8')
    import_line, transform_fn = TRANSFORM[ftype]
    content, count = transform_fn(original)
    content, import_added = insert_import(content, import_line)
    changed = content != original
    if changed:
        filepath.write_text(content, encoding='utf-8')
    return count, import_added, changed


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    py_files = sorted(APPS_DIR.rglob('*.py'))
    results  = []

    for fp in py_files:
        ftype = classify(fp)
        if ftype is None:
            continue
        try:
            count, import_added, changed = process_file(fp, ftype)
            if changed:
                results.append((
                    fp.relative_to(APPS_DIR), ftype, count, import_added
                ))
        except Exception as e:
            print(f'ERREUR {fp}: {e}', file=sys.stderr)
            import traceback; traceback.print_exc()

    sep = '-' * 72
    print('\n' + sep)
    print(f'{"Fichier":<52} {"Type":>10} {"Strings":>8}')
    print(sep)
    grand_total = 0
    for path, ftype, count, imp in results:
        note = ' +import' if imp else ''
        print(f'{str(path):<52} {ftype:>10} {count:>8}{note}')
        grand_total += count
    print(sep)
    print(f'{"TOTAL":<52} {"":>10} {grand_total:>8}')
    print(f'{len(results)} fichiers modifies\n')


if __name__ == '__main__':
    main()
