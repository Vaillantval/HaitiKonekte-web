from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema

from apps.accounts.permissions import IsSuperAdmin
from apps.home.models import SiteConfig, FAQCategorie, FAQItem, ContactMessage, SliderImage


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


# ── GET/POST /api/admin/config/slider/ ──────────────────────────
def _slide_data(s, request=None):
    image_url = None
    if s.image:
        image_url = request.build_absolute_uri(s.image.url) if request else s.image.url
    return {
        'id':           s.pk,
        'titre':        s.titre,
        'sous_titre':   s.sous_titre,
        'texte_bouton': s.texte_bouton,
        'lien':         s.lien,
        'image':        image_url,
        'ordre':        s.ordre,
        'is_active':    s.is_active,
        'created_at':   s.created_at.isoformat(),
    }


@api_view(['GET', 'POST'])
@permission_classes([IsSuperAdmin])
def slider_list(request):
    if request.method == 'GET':
        slides = SliderImage.objects.all().order_by('ordre')
        return Response({'success': True, 'data': [_slide_data(s, request) for s in slides]})

    # POST — multipart (image upload)
    image = request.FILES.get('image')
    if not image:
        return Response({'success': False, 'error': 'Image requise.'}, status=400)

    slide = SliderImage.objects.create(
        image        = image,
        titre        = request.data.get('titre', ''),
        sous_titre   = request.data.get('sous_titre', ''),
        texte_bouton = request.data.get('texte_bouton', 'Découvrir'),
        lien         = request.data.get('lien', ''),
        ordre        = int(request.data.get('ordre', 0)),
        is_active    = request.data.get('is_active', 'true').lower() != 'false',
    )
    return Response({'success': True, 'data': _slide_data(slide, request)}, status=201)


@api_view(['GET', 'PATCH', 'DELETE'])
@permission_classes([IsSuperAdmin])
def slider_detail(request, pk):
    slide = get_object_or_404(SliderImage, pk=pk)

    if request.method == 'GET':
        return Response({'success': True, 'data': _slide_data(slide, request)})

    if request.method == 'DELETE':
        slide.image.delete(save=False)
        slide.delete()
        return Response({'success': True, 'data': {'id': pk}})

    # PATCH
    for field in ('titre', 'sous_titre', 'texte_bouton', 'lien'):
        if field in request.data:
            setattr(slide, field, request.data[field])
    if 'ordre' in request.data:
        slide.ordre = int(request.data['ordre'])
    if 'is_active' in request.data:
        val = request.data['is_active']
        slide.is_active = val if isinstance(val, bool) else str(val).lower() != 'false'
    if 'image' in request.FILES:
        slide.image.delete(save=False)
        slide.image = request.FILES['image']
    slide.save()
    return Response({'success': True, 'data': _slide_data(slide, request)})
