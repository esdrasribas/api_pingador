"""
URL configuration for api_pingador project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from django.contrib import admin
from django.urls import path
from pingador import views
from drf_yasg.views import get_schema_view
from rest_framework import permissions
from drf_yasg import openapi
from django.views.generic import TemplateView

schema_view = get_schema_view(
    openapi.Info(
        title="API Pingador",
        default_version="v1",
        description=(
            "A API Pingador foi desenvolvida para gerenciar testes de conectividade com o circuito do cliente, "
            "oferecendo endpoints para solicitação e consulta desses testes. Com suporte a autenticação "
            "Bearer, ela é projetada para oferecer confiabilidade e rastreabilidade em ambientes de rede."
            "\n\n"
            "### Funcionalidades:\n"
            "- **SolicitaTesteConectividade:** Endpoint para iniciar um teste de conectividade entre sistemas.\n"
            "- **ConsultarTesteConectividade:** Endpoint para consultar o status de um teste previamente solicitado.\n\n"
            "### Contato:\n"
            "Para dúvidas ou suporte, entre em contato pelo e-mail: [esdras.moreira@vtal.com](mailto:esdras.moreira@vtal.com).\n\n"
            "### Termos de Serviço:\n"
        ),
        # terms_of_service="https://www.example.com/terms/",
        contact=openapi.Contact(email="esdras.moreira@vtal.com"),
        # license=openapi.License(name="Licença Example"),
        security=[{'BearerAuth': []}],
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)


urlpatterns = [
    # ADMIN
    path('secureadmin/', admin.site.urls),
    # Endpoint API Pingador
    path('api/v1/SolicitaTesteConectividade/',
        views.SolicitaTesteConectividade.as_view(), name='SolicitaTesteConectividade'),
    path('api/v1/ConsultarTesteConectividade/',
         views.ConsultarTesteConectividade.as_view(), name='ConsultarTesteConectividade'),

     # Endpoint de Health Check
    path('api/v1/health/', views.HealthCheckView.as_view(), name='health_check'),

    # Swagger Documentation
    path('swagger/', schema_view.with_ui('swagger',
         cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc',
         cache_timeout=0), name='schema-redoc'),

    path(
        'swagger-ui/',
        TemplateView.as_view(
            template_name='swagger_ui_custom.html',
            extra_context={'schema_url': 'openapi-schema'}
        ),
        name='swagger-ui',
    ),

    path('swagger<format>/', schema_view.without_ui(cache_timeout=0),
         name='schema-json'),

    # Token JWT
    path('token/', TokenObtainPairView.as_view()),
    path('token/refresh/', TokenRefreshView.as_view()),
]
