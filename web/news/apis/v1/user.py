from django.http import JsonResponse
from rest_framework.views import APIView
from django.contrib.auth import authenticate, login, logout
import datetime

class UserSignInView(APIView):
    authentication_classes = ()
    permission_classes = ()
    def post(self, request):
        username = request.data.get('username', None)
        password = request.data.get('password', None)
        if username == '' or password == '':
            return JsonResponse(dict(
            status='WRONG_USERNAME_OR_PASSWORD',
            message='이메일 또는 패스워드를 확인하세요.'
            ), status=401)

        # 사용자 인증 진행
        user = authenticate(
            request,
            username=username,
            password=password
        )

        if user is None:
            return JsonResponse(dict(
                status='WRONG_CREDENTIALS',
                message='이메일 또는 패스워드를 확인하세요.'
            ), status=401)

        login(request, user)

        return JsonResponse(dict(
            status='OK',
            message='로그인에 성공하였습니다.',
            username=username,
            password=password
        ))
        
class UserMySelfView(APIView):
    def get(self, request):
        user = request.user

        if user.is_authenticated:
            user.last_login = datetime.datetime.now()
            user.save()
            user_dict = dict(
                username=user.username,
                last_login=user.last_login.strftime("%d/%m/%Y, %H:%M:%S")
            )
            return JsonResponse(dict(
                status='OK',
                message='유저 정보를 조회하였습니다.',
                user=user_dict
            ))
        else:
            return JsonResponse(dict(
                status='USER_NOT_FOUND',
                message='유저 정보가 없습니다',
                user=dict()
            ), status=404)


class UserSignOutView(APIView):
    def get(self, request):
        logout(request)
        return JsonResponse(dict(
            status='OK',
            message='로그아웃하였습니다.',
        ))
