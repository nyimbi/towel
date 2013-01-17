import httplib

from django import forms
from django.views.decorators.csrf import csrf_exempt

from towel.api import API, APIException, Resource

from .models import Person, EmailAddress, Message


class MessageForm(forms.ModelForm):
    class Meta:
        model = Message


class MessageResource(Resource):
    def post(self, request, *args, **kwargs):
        if (args or kwargs):
            raise APIException()

        form = MessageForm(request.POST)
        if not form.is_valid():
            raise APIException('Validation failed', data={
                'form': form.errors,
                })

        message = form.save()
        data = self.api.serialize_instance(message,
            build_absolute_uri=request.build_absolute_uri,
            )
        return self.serialize_response(data,
            status=httplib.CREATED,
            headers={'Location': data['__uri__']})


api_v1 = API('v1', decorators=[
    csrf_exempt,
    ])

api_v1.register(Person)
api_v1.register(EmailAddress)
api_v1.register(Message,
    view_class=MessageResource,
    )