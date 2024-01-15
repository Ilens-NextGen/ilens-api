from accounts.models import User
from django.core import signing as si
from django.conf import settings

def generate_otps(user_id, purpose):
	"""Generates otp for password reset and account verification"""
	data = {
			'user_id': user_id,
			'for': purpose
	}
	token = si.dumps(data, compress=True)
	return token

def verify_otps(token, purpose):
    """Verify the generated otps for password reset and account verification"""
    try:
        data = si.loads(token, max_age=settings.TOKEN_EXPIRY)
        if purpose != data.get('for'):
            return None, 400
        user = User.objects.get(id=data.get('user_id'))
        if not user:
            return None, 404
    except (si.SignatureExpired, si.BadSignature):
        return None, 400
    return user, 200
