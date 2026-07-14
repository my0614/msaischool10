from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.utils import timezone

from news.models.common import Sample
from news.serializers.common import SampleListSerializer


class HelloWorldView(APIView):
    def get(self, request):
        name = request.query_params.get("name", "")
        sample = Sample.objects.create(
            name=name, phone_number="123-456-7890", address="Sample Address"
        )
        return Response(
            dict(status="OK", message="SUCCESS", data="Hello world!! {}".format(name))
        )

class SampleListView(APIView):
    def get(self, request):
        sample_queryset = Sample.objects.all()

        paginator = PageNumberPagination()
        paginator.page_size = 10

        result_page = paginator.paginate_queryset(sample_queryset, request)
        serializer = SampleListSerializer(result_page, many=True)

        page_information = {
            "total_count": paginator.page.paginator.count,
            "total_pages": paginator.page.paginator.num_pages,
            "next": paginator.get_next_link(),
            "previous": paginator.get_previous_link(),
            "page_size": paginator.page.paginator.per_page,
        }

        return Response(
            dict(
                status="OK",
                message="SUCCESS",
                data=serializer.data,
                page_information=page_information,
            )
        )

    def post(self, request):
        serializer = SampleListSerializer(data=request.data)
        if serializer.is_valid():
            sample = serializer.save()
            return Response(
                dict(
                    status="OK",
                    message="SUCCESS",
                    data={
                        "id": str(sample.id),
                        "name": sample.name,
                        "phone_number": sample.phone_number,
                        "address": sample.address,
                    },
                )
            )
        return Response(
            dict(status="ERROR", message="Invalid data", data=serializer.errors),
            status=status.HTTP_400_BAD_REQUEST,
        )
        

class SampleDetailView(APIView):
    def get(self, request, sample_id):
        try:
            sample = Sample.objects.get(id=sample_id)
            return Response(
                dict(
                    status="OK",
                    message="SUCCESS",
                    data={
                        "id": str(sample.id),
                        "name": sample.name,
                        "phone_number": sample.phone_number,
                        "address": sample.address,
                    },
                )
            )
        except Sample.DoesNotExist:
            return Response(
                dict(status="ERROR", message="Sample not found", data={}), status=404
            )

    def put(self, request, sample_id):
        try:
            sample = Sample.objects.get(id=sample_id)
            serializer = SampleListSerializer(sample, data=request.data, partial=True)

            if serializer.is_valid():
                serializer.save()
            else:
                return Response(
                    dict(
                        status="ERROR", message="Invalid data", data=serializer.errors
                    ),
                    status=status.HTTP_400_BAD_REQUEST,
                )

            return Response(
                dict(
                    status="OK",
                    message="SUCCESS",
                    data={
                        "id": str(sample.id),
                        "name": sample.name,
                        "phone_number": sample.phone_number,
                        "address": sample.address,
                    },
                )
            )
        except Sample.DoesNotExist:
            return Response(
                dict(status="ERROR", message="Sample not found", data={}), status=404
            )
    
    def delete(self, request, sample_id):
        try:
            # sample_queryset = Sample.objects.filter(id=sample_id)
            # sample_queryset.delete()
            sample = Sample.objects.get(id=sample_id)
            sample.delete()
            # sample.removed_at = timezone.now()
            # sample.save()
            return Response(dict(status="OK", message="SUCCESS", data={}))
        except Sample.DoesNotExist:
            return Response(
                dict(status="ERROR", message="Sample not found", data={}), status=404
            )