import re
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.db import transaction

from accounts.models import PerfilUsuario
from core.models import Expositor


PASSWORD_TEMPORAL = 'Temporal123'
DOMINIO_PLACEHOLDER = 'festivalbutifarra.local'


import unicodedata


def limpiar_acentos(texto):
    """Convierte á→a, é→e, ñ→n, ü→u, etc."""
    if not texto:
        return ''
    # Descompone y elimina diacríticos
    nfkd = unicodedata.normalize('NFKD', texto)
    return ''.join(c for c in nfkd if not unicodedata.combining(c))

def slugify_username(nombre_empresa, email, exp_id):
    base = (nombre_empresa or '').strip()

    if not base or base.lower() in ('por definir', 'sin nombre', 'none'):
        if email and '@' in email:
            base = email.split('@')[0]
        else:
            base = f'expositor{exp_id}'

    base = base.lower()
    base = limpiar_acentos(base)                 # ← NUEVO: quita acentos/ñ
    base = re.sub(r'[^a-z0-9._-]+', '_', base)   # luego reemplaza el resto
    base = re.sub(r'_+', '_', base).strip('_.-')

    if not base:
        base = f'expositor{exp_id}'

    return base[:140]


def username_unico(base, existentes):
    """Devuelve un username no usado. Si 'base' existe, prueba base_2, _3..."""
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


class Command(BaseCommand):
    help = 'Crea accesos (User + Perfil) para todos los expositores sin perfil vinculado.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Solo muestra lo que haría, sin crear nada.',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']

        self.stdout.write('=' * 70)
        self.stdout.write('  CREACION DE ACCESOS PARA EXPOSITORES')
        self.stdout.write('=' * 70)

        existing_users = set(User.objects.values_list('username', flat=True))
        sin_perfil = Expositor.objects.filter(
            perfil_usuario__isnull=True
        ).order_by('id')

        total = sin_perfil.count()
        self.stdout.write(f'\nExpositores sin acceso: {total}')

        if total == 0:
            self.stdout.write(self.style.SUCCESS('\nNo hay nada que hacer.'))
            return

        if dry_run:
            self.stdout.write(self.style.WARNING('\n*** MODO DRY-RUN: no se creara nada ***'))

        creados = []
        errores = []

        for exp in sin_perfil:
            try:
                email = (exp.email_contacto or '').strip()
                if not email:
                    email = f"expositor{exp.id}@{DOMINIO_PLACEHOLDER}"

                base = slugify_username(exp.nombre_empresa, email, exp.id)
                username = username_unico(base, existing_users)

                if dry_run:
                    creados.append({
                        'id': exp.id,
                        'empresa': exp.nombre_empresa,
                        'username': username,
                        'email': email,
                    })
                    continue

                with transaction.atomic():
                    user = User.objects.create_user(
                        username=username,
                        email=email,
                        password=PASSWORD_TEMPORAL,
                        is_active=True,
                    )
                    user.first_name = exp.nombre_expositor or ''
                    user.save(update_fields=['first_name'])

                    perfil, _ = PerfilUsuario.objects.get_or_create(user=user)
                    perfil.rol = 'expositor'
                    perfil.expositor = exp
                    perfil.telefono = exp.numero_contacto or ''
                    perfil.activo = True
                    perfil.save()

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

        # ============ REPORTE ============
        self.stdout.write('\n' + '=' * 70)
        if dry_run:
            self.stdout.write(self.style.WARNING(
                f'  [DRY-RUN] SE CREARIAN: {len(creados)}'
            ))
        else:
            self.stdout.write(self.style.SUCCESS(
                f'  OK CREADOS: {len(creados)}'
            ))
        self.stdout.write(self.style.ERROR(f'  ERRORES: {len(errores)}'))
        self.stdout.write('=' * 70)

        if creados:
            self.stdout.write('\nCREDENCIALES (comparte con cada expositor):')
            self.stdout.write('-' * 90)
            self.stdout.write(f'{"ID":<5} {"Usuario":<35} {"Password":<15} {"Email"}')
            self.stdout.write('-' * 90)
            for c in creados:
                self.stdout.write(
                    f'{c["id"]:<5} {c["username"]:<35} {PASSWORD_TEMPORAL:<15} {c["email"]}'
                )
            self.stdout.write('-' * 90)

        if errores:
            self.stdout.write(self.style.ERROR('\nERRORES:'))
            for e in errores:
                self.stdout.write(
                    self.style.ERROR(
                        f'  ID={e["id"]} | {e["empresa"]} -> {e["error"]}'
                    )
                )

        self.stdout.write('\nProceso terminado.\n')