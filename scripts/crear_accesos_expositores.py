"""
Script para crear accesos de usuario para todos los expositores
que aún no tengan un PerfilUsuario vinculado.

Uso:
    python manage.py shell < scripts/crear_accesos_expositores.py

O desde el shell:
    exec(open('scripts/crear_accesos_expositores.py', encoding='utf-8').read())
"""
import re
from django.contrib.auth.models import User
from accounts.models import PerfilUsuario
from core.models import Expositor


PASSWORD_TEMPORAL = 'Temporal123'
DOMINIO_PLACEHOLDER = 'festivalbutifarra.local'


def slugify_username(nombre_empresa, email, exp_id):
    """
    Genera un username limpio a partir del nombre de la empresa.
    Fallbacks: email → expositor{id}
    """
    base = (nombre_empresa or '').strip()

    if not base or base.lower() in ('por definir', 'sin nombre', 'none'):
        if email and '@' in email:
            base = email.split('@')[0]
        else:
            base = f'expositor{exp_id}'

    base = base.lower()
    base = re.sub(r'[^a-z0-9._-]+', '_', base)
    base = re.sub(r'_+', '_', base).strip('_.-')

    if not base:
        base = f'expositor{exp_id}'

    return base[:140]


def username_unico(base, existentes):
    """
    Si 'base' ya existe, prueba base_2, base_3, etc.
    'existentes' es un set que se va actualizando.
    """
    if base not in existentes:
        existentes.add(base)
        return base

    i = 2
    while True:
        candidato = f"{base}_{i}"
        if candidato not in existentes:
            existentes.add(candidato)
            return candidato
        i += 1


# ============================================================
#  EJECUCIÓN
# ============================================================

print("=" * 70)
print("  CREACIÓN DE ACCESOS PARA EXPOSITORES")
print("=" * 70)

# Usuarios ya existentes (para no chocar)
existing_users = set(User.objects.values_list('username', flat=True))

# Expositores sin perfil vinculado
sin_perfil = Expositor.objects.filter(perfil_usuario__isnull=True).order_by('id')
print(f"\nExpositores sin acceso: {sin_perfil.count()}")

creados = []
saltados = []
errores = []

for exp in sin_perfil:
    try:
        # 1) Email (todos tienen, pero por si acaso)
        email = (exp.email_contacto or '').strip()
        if not email:
            email = f"expositor{exp.id}@{DOMINIO_PLACEHOLDER}"
            print(f"  ⚠️  Expositor {exp.id} sin email → usando placeholder {email}")

        # 2) Username único
        base = slugify_username(exp.nombre_empresa, email, exp.id)
        username = username_unico(base, existing_users)

        # 3) Crear User
        user = User.objects.create_user(
            username=username,
            email=email,
            password=PASSWORD_TEMPORAL,
            is_active=True,
        )
        user.first_name = exp.nombre_expositor or ''
        user.save(update_fields=['first_name'])

        # 4) Crear/actualizar Perfil
        perfil, creado = PerfilUsuario.objects.get_or_create(user=user)
        perfil.rol = 'expositor'
        perfil.expositor = exp
        perfil.telefono = exp.numero_contacto or ''
        perfil.activo = True
        perfil.save()

        # 5) Refrescar el username en el set
        creados.append({
            'id': exp.id,
            'empresa': exp.nombre_empresa,
            'username': username,
            'email': email,
        })

    except Exception as e:
        errores.append({
            'id': exp.id,
            'empresa': exp.nombre_empresa,
            'error': str(e),
        })


# ============================================================
#  REPORTE FINAL
# ============================================================

print("\n" + "=" * 70)
print(f"  ✅ CREADOS: {len(creados)}")
print(f"  ❌ ERRORES: {len(errores)}")
print("=" * 70)

if creados:
    print("\n📋 CREDENCIALES (comparte con cada expositor):")
    print("-" * 70)
    print(f"{'ID':<5} {'Usuario':<35} {'Contraseña':<15}")
    print("-" * 70)
    for c in creados:
        print(f"{c['id']:<5} {c['username']:<35} {PASSWORD_TEMPORAL:<15}")
    print("-" * 70)
    print("\n📧 Emails asociados:")
    print("-" * 70)
    for c in creados:
        print(f"  ID={c['id']:<5} | {c['empresa']:<40} | {c['email']}")
    print("-" * 70)

if errores:
    print("\n❌ ERRORES:")
    for e in errores:
        print(f"  ID={e['id']} | {e['empresa']} → {e['error']}")

print("\n🎉 Proceso terminado.")
print("=" * 70)