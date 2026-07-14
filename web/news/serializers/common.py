from rest_framework import serializers
from news.models.common import Sample

class SampleListSerializer(serializers.ModelSerializer):
    formatted_phone_number = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = Sample
        fields = ["id", "name", "phone_number", "address", "formatted_phone_number"]

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["create_at"] = instance.created_at.strftime("%Y-%m-%d %H:%M:%S")
        data["name"] = "이름: {}".format(data["name"])
        data["phone_number"] = "전화번호: {}".format(data["phone_number"].replace("-", ""))  # 하이픈 제거
        return data

    def validate_phone_number(self, value):
        return value.replace("-","")
    
    def create(self, validated_data):
        formatted_phone_number = validated_data.pop("formatted_phone_number", None)
        if formatted_phone_number:
            validated_data["phone_number"] = formatted_phone_number.replace("-", "")
        return super().create(validated_data)

    def update(self, instance, validated_data):
        formatted_phone_number = validated_data.pop("formatted_phone_number", None)
        if formatted_phone_number:
            validated_data["phone_number"] = formatted_phone_number.replace("-", "")
        return super().update(instance, validated_data)