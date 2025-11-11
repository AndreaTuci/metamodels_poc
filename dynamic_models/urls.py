from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api_views import MetaModelViewSet, DynamicModelViewSet
from .data_views import (
    dynamic_data_list, dynamic_data_add, dynamic_data_edit, 
    dynamic_data_delete, dynamic_data_export
)

# Router per le API
router = DefaultRouter()
router.register(r'meta-models', MetaModelViewSet, basename='metamodel')

urlpatterns = [
    # API per gestione dei MetaModel
    path('api/', include(router.urls)),
    
    # API dinamica per i dati dei modelli
    # Esempio: /api/data/Product/ per accedere ai dati del modello "Product"
    path('api/data/<str:model_name>/', 
         DynamicModelViewSet.as_view({
             'get': 'list',
             'post': 'create'
         }), 
         name='dynamic-model-list'),
    
    path('api/data/<str:model_name>/<int:pk>/', 
         DynamicModelViewSet.as_view({
             'get': 'retrieve',
             'put': 'update',
             'patch': 'partial_update',
             'delete': 'destroy'
         }), 
         name='dynamic-model-detail'),
    
    # Views per gestione dati nell'admin
    path('data/<int:meta_model_id>/', dynamic_data_list, name='dynamic_data_list'),
    path('data/<int:meta_model_id>/add/', dynamic_data_add, name='dynamic_data_add'),
    path('data/<int:meta_model_id>/<int:object_id>/', dynamic_data_edit, name='dynamic_data_edit'),
    path('data/<int:meta_model_id>/<int:object_id>/delete/', dynamic_data_delete, name='dynamic_data_delete'),
    path('data/<int:meta_model_id>/export/', dynamic_data_export, name='dynamic_data_export'),
]