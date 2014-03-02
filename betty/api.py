import json
import os
import copy
import shutil

from django.http import (
    HttpResponse,
    HttpResponseNotAllowed,
    HttpResponseForbidden,
    HttpResponseBadRequest,
    HttpResponseNotFound
)

from wand.image import Image as WandImage

from .conf.app import settings
from .models import Image, source_upload_to
 
ACC_HEADERS = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
    'Access-Control-Max-Age': 1000,
    'Access-Control-Allow-Headers': '*'
}


def crossdomain(origin="*", methods=[], headers=["X-Betty-Api-Key", "Content-Type"]):

    def _method_wrapper(func):

        def _crossdomain_wrapper(request, *args, **kwargs):
            if request.method != "OPTIONS":
                response = func(request, *args, **kwargs)
            else:
                response = HttpResponse()
            response["Access-Control-Allow-Origin"] = "*"
            if methods:
                if request.method not in methods:
                    return HttpResponseNotAllowed(methods)
                response["Access-Control-Allow-Methods"] = ", ".join(methods)
            if headers:
                response["Access-Control-Allow-Headers"] = ", ".join(headers)
            return response

        return _crossdomain_wrapper

    return _method_wrapper


@crossdomain(methods=['POST', 'OPTIONS'])
def new(request):
    if not (request.user.is_superuser or request.user.has_perm("betty.add_image")):
        response_text = json.dumps({'message': 'Not authorized'})
        return HttpResponseForbidden(response_text, content_type="application/json")

    image_file = request.FILES.get("image")
    if image_file is None:
        return HttpResponseBadRequest()

    image = Image.objects.create(name=image_file.name)
    os.makedirs(image.path())
    source_path = source_upload_to(image, image_file.name)

    with open(source_path, 'wb+') as f:
        for chunk in image_file.chunks():
            f.write(chunk)
        f.seek(0)
        with WandImage(file=f) as img:
            image.width = img.size[0]
            image.height = img.size[1]

        image.source.name = source_path
        image.save()

    return HttpResponse(json.dumps(image.to_native()), content_type="application/json")


@crossdomain(methods=['POST', 'OPTIONS'])
def update_selection(request, image_id, ratio_slug):
    if not (request.user.is_superuser or request.user.has_perm("betty.change_image")):
        response_text = json.dumps({'message': 'Not authorized'})
        return HttpResponseForbidden(response_text, content_type="application/json")

    try:
        image = Image.objects.get(id=image_id)
    except Image.DoesNotExist:
        message = json.dumps({"message": "No such image!"})
        return HttpResponseNotFound(message, content_type="application/json")

    try:
        request_json = json.loads(request.body)
    except Exception:
        message = json.dumps({"message": "Bad selection"})
        return HttpResponseBadRequest(message, content_type="application/json")
    try:
        selection = {
            "x0": int(request_json["x0"]),
            "y0": int(request_json["y0"]),
            "x1": int(request_json["x1"]),
            "y1": int(request_json["y1"]),
        }
    except (KeyError, ValueError):
        message = json.dumps({"message": "Bad selection"})
        return HttpResponseBadRequest(message, content_type="application/json")

    selections = copy.copy(image.selections)
    if selections is None:
        selections = {}

    if ratio_slug not in settings.BETTY_RATIOS:
        message = json.dumps({"message": "No such ratio"})
        return HttpResponseBadRequest(message, content_type="application/json")

    selections[ratio_slug] = selection
    image.selections = selections
    image.save()

    # TODO: Use a celery task for this?
    ratio_path = os.path.join(image.path(), ratio_slug)
    if os.path.exists(ratio_path):
        # crops = os.listdir(ratio_path)
        # TODO: flush cache on crops
        shutil.rmtree(ratio_path)
    
    message = json.dumps({"message": "Update sucessfull"})
    return HttpResponse(message, content_type="application/json")


@crossdomain(methods=['GET', 'OPTIONS'])
def search(request):
    if not request.user.is_staff:
        response_text = json.dumps({'message': 'Not authorized'})
        return HttpResponseForbidden(response_text, content_type="application/json")

    results = []
    query = request.GET.get("q")
    if query:
        for image in Image.objects.filter(name__icontains=query)[:20]:
            results.append(image.to_native())
    return HttpResponse(json.dumps(results), content_type="application/json")


@crossdomain(methods=["GET", "PATCH", "OPTIONS"])
def detail(request, image_id):
    if not (request.user.is_superuser or request.user.has_perm("betty.change_image")):
        response_text = json.dumps({'message': 'Not authorized'})
        return HttpResponseForbidden(response_text, content_type="application/json")

    try:
        image = Image.objects.get(id=image_id)
    except Image.DoesNotExist:
        message = json.dumps({"message": "No such image!"})
        return HttpResponseNotFound(message, content_type="application/json")

    if request.method == "PATCH":
        try:
            request_json = json.loads(request.body)
        except Exception:
            message = json.dumps({"message": "Bad Request"})
            return HttpResponseBadRequest(message, content_type="application/json")

        update_fields = []
        for field in ("name", "credit", "selections"):
            if field in request_json:
                setattr(image, field, request_json[field])
                update_fields.append(field)
        image.save(update_fields=update_fields)

    return HttpResponse(json.dumps(image.to_native()), content_type="application/json")
