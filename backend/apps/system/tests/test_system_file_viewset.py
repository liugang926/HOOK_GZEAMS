from djangorestframework_camel_case.parser import CamelCaseJSONParser
from rest_framework.parsers import FormParser, MultiPartParser

from apps.system.viewsets.system_file import SystemFileViewSet


def test_system_file_viewset_supports_multipart_and_json():
    parser_types = tuple(SystemFileViewSet.parser_classes)

    assert CamelCaseJSONParser in parser_types
    assert MultiPartParser in parser_types
    assert FormParser in parser_types
