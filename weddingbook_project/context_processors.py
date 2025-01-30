from django.conf import settings

def media_url(request):
    """ Make MEDIA_URL available in all templates. """
    return {"MEDIA_URL": settings.MEDIA_URL}
