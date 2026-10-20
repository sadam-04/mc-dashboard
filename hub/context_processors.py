from django.conf import settings

def export_deploy_details(request):
    return {
        'SITE_HEADER_TITLE': getattr(settings, 'SITE_HEADER_TITLE', ''),
        'MAIN_WEB_ADDR': getattr(settings, 'MAIN_WEB_ADDR', ''),
        'DYNMAP_WEB_ADDR': getattr(settings, 'DYNMAP_WEB_ADDR', ''),
    }