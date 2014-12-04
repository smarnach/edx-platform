from django.conf import settings

from rest_framework import generics
from rest_framework.views import APIView
from openedx.core.djangoapps.api.permissions import ApiKeyHeaderPermission
from server_api.serializers import PaginationSerializer


class PermissionMixin(object):
    """
    Mixin to set custom permission_classes
    """
    permission_classes = (ApiKeyHeaderPermission,)


class SecureAPIView(PermissionMixin, APIView):
    """
    View used for protecting access to specific workflows
    """
    pass


class PaginationMixin(object):
    """
    Mixin to set custom pagination support
    """
    pagination_serializer_class = PaginationSerializer
    paginate_by = getattr(settings, 'API_PAGE_SIZE', 20)
    paginate_by_param = 'page_size'
    max_paginate_by = 150


class SecureListAPIView(PermissionMixin,
                        PaginationMixin,
                        generics.ListAPIView):
    """
        Inherited from ListAPIView
    """
    pass
