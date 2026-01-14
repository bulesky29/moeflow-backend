from flask import current_app, request  # <--- 必须导入 request
from app.constants.v_code import VCodeTypeIntro

from app.core.views import MoeAPIView
from app.decorators.auth import admin_required, token_required
from app.models.v_code import Captcha, VCode, VCodeType
from app.validators import ConfirmEmailVCodeSchema, ResetPasswordVCodeSchema


class CaptchaAPI(MoeAPIView):
    def post(self):
        """
        [DEBUG 魔改版]
        返回假图片，防止前端转圈卡死
        """
        # 这是一个 1x1 像素透明 PNG 的 Base64，纯粹为了骗过前端组件
        fake_image = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=="
        
        # 返回固定的 info，防止数据库报错
        return {
            "info": "debug_skip_captcha", 
            "image": fake_image
        }


class ConfirmEmailVCodeAPI(MoeAPIView):
    def post(self):
        """
        [DEBUG 魔改版] 注册/绑定邮箱验证码
        1. 跳过图形验证码检查
        2. 控制台直接打印验证码
        """
        wait = current_app.config.get("CONFIRM_EMAIL_WAIT_SECONDS", 60)
        
        # ▼▼▼ 修改点 1: 绕过 Schema 校验，直接获取参数 ▼▼▼
        # 原代码: data = self.get_json(ConfirmEmailVCodeSchema())
        data = request.get_json()
        email = data.get("email", "").lower()
        
        if not email:
            return {"msg": "邮箱不能为空"}, 400

        # 创建验证码记录 (存入数据库)
        v_code = VCode.create(VCodeType.CONFIRM_EMAIL, email, wait=wait)
        
        # ▼▼▼ 修改点 2: 禁止发送邮件，改为控制台打印 ▼▼▼
        # v_code.to_email(email)  <-- 注释掉这行，防止 RabbitMQ 卡死
        
        print(f"\n{'='*20} [DEBUG] 注册验证码 {'='*20}")
        print(f"邮箱: {email}")
        print(f"验证码: {v_code.content}")
        print(f"{'='*55}\n")

        return {"wait": wait}


class ResetEmailVCodeAPI(MoeAPIView):
    @token_required
    def post(self):
        """
        重置邮箱 (通常需要登录，暂不修改 Schema，仅改为打印)
        """
        wait = current_app.config.get("RESET_EMAIL_WAIT_SECONDS", 60)
        email = self.current_user.email.lower()
        
        v_code = VCode.create(VCodeType.RESET_EMAIL, email, wait=wait)
        
        # v_code.to_email(email)
        print(f"\n======== [DEBUG] 修改邮箱验证码: {v_code.content} ========\n")
        
        return {"wait": wait}


class ResetPasswordVCodeAPI(MoeAPIView):
    def post(self):
        """
        [DEBUG 魔改版] 重置密码验证码
        """
        wait = current_app.config.get("RESET_PASSWORD_WAIT_SECONDS", 60)
        
        # ▼▼▼ 修改点: 绕过 Schema 校验 ▼▼▼
        # data = self.get_json(ResetPasswordVCodeSchema())
        data = request.get_json()
        email = data.get("email", "").lower()
        
        if not email:
            return {"msg": "邮箱不能为空"}, 400

        v_code = VCode.create(VCodeType.RESET_PASSWORD, email, wait=wait)
        
        # ▼▼▼ 修改点: 控制台打印 ▼▼▼
        # v_code.to_email(email)
        
        print(f"\n{'='*20} [DEBUG] 重置密码验证码 {'='*20}")
        print(f"邮箱: {email}")
        print(f"验证码: {v_code.content}")
        print(f"{'='*55}\n")
        
        return {"wait": wait}


class AdminVCodeListAPI(MoeAPIView):
    @admin_required
    def get(self):
        """返回最新的 100 个验证码"""
        codes = (
            VCode.objects(type__ne=VCodeType.CAPTCHA).limit(100).order_by("-send_time")
        )
        return [
            {
                "id": str(code.id),
                "content": code.content,
                "intro": VCodeTypeIntro[code.type],
                "info": code.info,
                "expires": code.expires.isoformat(),
                "wrong_count": code.wrong_count,
                "send_time": code.send_time.isoformat(),
            }
            for code in codes
        ]