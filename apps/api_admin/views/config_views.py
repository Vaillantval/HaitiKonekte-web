from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema

from apps.accounts.permissions import IsSuperAdmin
from apps.home.models import SiteConfig, FAQCategorie, FAQItem, ContactMessage


def _config_data(c):
    return {
        'nom_site':        c.nom_site,
        'slogan':          c.slogan,
        'email_contact':   c.email_contact,
        'telephone':       c.telephone,
        'adresse':         c.adresse,
        'facebook_url':    c.facebook_url,
        'instagram_url':   c.instagram_url,
        'whatsapp_numero': c.whatsapp_numero,
    }


# ── GET/PATCH /api/admin/config/site/ ───────────────────────────
@api_view(['GET', 'PATCH'])
@permission_classes([IsSuperAdmin])
def site_config(request):
    config = SiteConfig.get_config()

    if request.method == 'GET':
        return Response({'success': True, 'data': _config_data(config)})

    for field in [
        'nom_site', 'slogan', 'email_contact', 'telephone',
        'adresse', 'facebook_url', 'instagram_url', 'whatsapp_numero'
    ]:
        if field in request.data:
            setattr(config, field, request.data[field])
    config.save()
    return Response({'success': True, 'data': _config_data(config)})


# ── GET /api/admin/config/faq/categories/ ───────────────────────
@extend_schema(operation_id='admin_faq_categories_list', tags=['Admin — Config'])
@api_view(['GET'])
@permission_classes([IsSuperAdmin])
def faq_categories(request):
    cats = FAQCategorie.objects.all().order_by('ordre')
    data = [
        {'id': c.pk, 'titre': c.titre, 'ordre': c.ordre, 'is_active': c.is_active}
        for c in cats
    ]
    return Response({'success': True, 'data': data})


@extend_schema(operation_id='admin_faq_categorie_detail', tags=['Admin — Config'])
@api_view(['GET'])
@permission_classes([IsSuperAdmin])
def faq_categorie_detail(request, pk):
    cat   = get_object_or_404(FAQCategorie, pk=pk)
    items = FAQItem.objects.filter(categorie=cat, is_active=True)
    return Response({
        'success': True,
        'data': {
            'id':    cat.pk,
            'titre': cat.titre,
            'items': [
                {'id': i.pk, 'question': i.question, 'reponse': i.reponse}
                for i in items
            ]
        }
    })


# ── GET /api/admin/config/faq/items/ ────────────────────────────
@extend_schema(operation_id='admin_faq_items_list', tags=['Admin — Config'])
@api_view(['GET'])
@permission_classes([IsSuperAdmin])
def faq_items(request):
    items = FAQItem.objects.select_related('categorie').order_by('ordre')
    data  = [
        {
            'id':        i.pk,
            'categorie': i.categorie.titre,
            'question':  i.question,
            'reponse':   i.reponse,
            'is_active': i.is_active,
        }
        for i in items
    ]
    return Response({'success': True, 'data': data})


@extend_schema(operation_id='admin_faq_item_detail', tags=['Admin — Config'])
@api_view(['GET'])
@permission_classes([IsSuperAdmin])
def faq_item_detail(request, pk):
    i = get_object_or_404(FAQItem, pk=pk)
    return Response({
        'success': True,
        'data': {
            'id':        i.pk,
            'categorie': i.categorie.titre,
            'question':  i.question,
            'reponse':   i.reponse,
        }
    })


# ── GET /api/admin/config/contact/ ──────────────────────────────
@extend_schema(operation_id='admin_contact_messages_list', tags=['Admin — Config'])
@api_view(['GET'])
@permission_classes([IsSuperAdmin])
def contact_messages(request):
    msgs = ContactMessage.objects.order_by('-created_at')[:50]
    data = [
        {
            'id':         m.pk,
            'nom':        m.nom,
            'email':      m.email,
            'sujet':      m.sujet,
            'message':    m.message,
            'statut':     m.statut,
            'created_at': m.created_at.isoformat(),
        }
        for m in msgs
    ]
    return Response({'success': True, 'data': data})


@extend_schema(operation_id='admin_contact_message_detail', tags=['Admin — Config'])
@api_view(['GET', 'PATCH'])
@permission_classes([IsSuperAdmin])
def contact_message_detail(request, pk):
    msg = get_object_or_404(ContactMessage, pk=pk)

    if request.method == 'GET':
        return Response({
            'success': True,
            'data': {
                'id':      msg.pk,
                'nom':     msg.nom,
                'email':   msg.email,
                'sujet':   msg.sujet,
                'message': msg.message,
                'statut':  msg.statut,
            }
        })

    nouveau_statut = request.data.get('statut')
    STATUTS        = ['nouveau', 'lu', 'repondu', 'archive']
    if nouveau_statut and nouveau_statut in STATUTS:
        msg.statut = nouveau_statut
        msg.save()

    return Response({'success': True, 'data': {'id': msg.pk, 'statut': msg.statut}})
